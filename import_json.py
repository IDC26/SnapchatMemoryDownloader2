import concurrent.futures
import json
import os
import time
import zipfile
from pathlib import Path
from typing import Iterable, NamedTuple

import requests


# === CONFIG ===
JSON_FILE = Path("")
OUTPUT_DIR = Path("")
MAX_WORKERS = min(32, (os.cpu_count() or 4) * 5)
TIMEOUT = 30
CHUNK_SIZE = 8192


CONTENT_TYPE_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/heic": ".heic",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "application/zip": ".zip",
}


class DownloadJob(NamedTuple):
    index: int
    url: str
    base_name: str
    guessed_ext: str
    output_dir: Path


def load_media_items(json_file: Path) -> list[dict]:
    with json_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("Saved Media", [])


def _guess_ext_from_media_type(media_type: str) -> str:
    mt = (media_type or "").lower()
    return ".mp4" if mt == "video" else ".jpg"


def build_jobs(media_items: Iterable[dict], output_dir: Path) -> list[DownloadJob]:
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_stems = {p.stem for p in output_dir.iterdir() if p.is_file()}

    jobs: list[DownloadJob] = []
    for i, item in enumerate(media_items, start=1):
        url = item.get("Media Download Url")
        if not url:
            continue

        base_name = f"{i:05d}"
        if base_name in existing_stems:
            continue

        guessed_ext = _guess_ext_from_media_type(item.get("Media Type") or "")
        jobs.append(DownloadJob(i, url, base_name, guessed_ext, output_dir))

    return jobs


def _configure_session(max_workers: int) -> requests.Session:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=max_workers,
        pool_maxsize=max_workers,
        max_retries=2,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _ext_from_content_type(content_type: str | None, guessed_ext: str) -> str:
    if not content_type:
        return guessed_ext
    ctype = content_type.split(";", 1)[0].strip().lower()
    return CONTENT_TYPE_EXT.get(ctype, guessed_ext)


def unzip_and_filter(zip_path: Path, output_dir: Path, base_name: str) -> str:
    """
    Extract the ZIP into output_dir, delete overlay files, keep only *-main.*
    Returns the final kept filename.
    """
    kept_filename = None

    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.infolist():
            filename = member.filename

            # Extract file
            extracted_path = output_dir / Path(filename).name
            z.extract(member, output_dir)

            # Keep only files ending with '-main.<ext>'
            name_lower = extracted_path.name.lower()
            if "-main" in name_lower:
                kept_filename = extracted_path.name
            else:
                extracted_path.unlink(missing_ok=True)

    # Remove the ZIP
    zip_path.unlink(missing_ok=True)

    return kept_filename or f"{base_name}.zip"  # fallback name


def download_one(job: DownloadJob, session: requests.Session) -> tuple[bool, str, str | None]:
    try:
        with session.get(job.url, stream=True, timeout=TIMEOUT) as resp:
            resp.raise_for_status()

            ext = _ext_from_content_type(resp.headers.get("Content-Type"), job.guessed_ext)
            final_path = job.output_dir / f"{job.base_name}{ext}"

            with final_path.open("wb") as f:
                for chunk in resp.iter_content(CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)

        # Handle ZIP extraction
        if ext == ".zip":
            final_name = unzip_and_filter(final_path, job.output_dir, job.base_name)
            return True, final_name, None

        return True, final_path.name, None

    except Exception as e:
        return False, job.base_name, str(e)


def download_all(jobs: list[DownloadJob]) -> None:
    if not jobs:
        print("Nothing to download, everything is already up to date.")
        return

    total = len(jobs)
    print(f"Starting download of {total} Snapchat memories with {MAX_WORKERS} workers…")
    start_time = time.time()

    success = 0
    failed = 0

    session = _configure_session(MAX_WORKERS)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(download_one, job, session) for job in jobs]

            for future in concurrent.futures.as_completed(futures):
                ok, name, err = future.result()
                if ok:
                    success += 1
                    print(f"✅ [{success}/{total}] {name}")
                else:
                    failed += 1
                    print(f"❌ [{success + failed}/{total}] {name} – {err}")
    finally:
        session.close()

    elapsed = time.time() - start_time
    print(f"Finished in {elapsed:.1f}s → {success} succeeded, {failed} failed")


def main() -> None:
    media_items = load_media_items(JSON_FILE)
    jobs = build_jobs(media_items, OUTPUT_DIR)
    download_all(jobs)


if __name__ == "__main__":
    main()
