<div align="center">

# 📸 Snapchat Memory Downloader  

Fast, reliable, and content-aware Snapchat Memories downloader with:
parallel downloads, MIME-type based extension detection, and smart ZIP
extraction that keeps only the real `*-main.*` media files.

---

[![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![Issues](https://img.shields.io/github/issues/IDC26/SnapchatMemoryDownloader)
![Stars](https://img.shields.io/github/stars/IDC26/SnapchatMemoryDownloader?style=social)

---

</div>

# Table of Contents
- [📸 Snapchat Memory Downloader](#-snapchat-memory-downloader)
- [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
    - [High-Performance Downloader](#high-performance-downloader)
    - [Smart Media Type Detection](#smart-media-type-detection)
    - [Automatic ZIP Extraction](#automatic-zip-extraction)
    - [Safe \& Idempotent](#safe--idempotent)
  - [Requirements](#requirements)
  - [Getting Your Snapchat Export](#getting-your-snapchat-export)
  - [Configuration](#configuration)
  - [How File Naming Works](#how-file-naming-works)
  - [ZIP Handling Logic](#zip-handling-logic)
  - [Running the Script](#running-the-script)
  - [Example Directory Structure](#example-directory-structure)
  - [Script Behavior Summary](#script-behavior-summary)
  - [Optional Enhancements](#optional-enhancements)

## Overview

A fast, reliable, and content-aware tool for downloading your Snapchat Memories from a Snapchat data export. Supports high-performance parallel downloads, correct file-type detection, and smart extraction of Snapchat’s ZIP-formatted “enhanced memories.”

## Features

### High-Performance Downloader

- Parallel downloads optimized for IO-bound workloads
- Shared `requests.Session` with connection pooling
- Automatic resume: skips already-downloaded items

### Smart Media Type Detection

- Fixes mislabeled media types by inspecting `Content-Type` headers
- Dynamically assigns the correct extension (`.jpg`, `.png`, `.mp4`, `.zip`, etc.)
- Avoids corrupt or incorrectly named files

### Automatic ZIP Extraction

- Extracts ZIPs into your media directory
- Keeps only the `*-main.*` file
- Deletes all `*-overlay.*` files and removes the ZIP afterward

### Safe & Idempotent

- Running the script multiple times is safe
- Existing items are detected and skipped by index
- ZIP extraction cleans up temporary artifacts

## Requirements

- Python 3.10+
- Install dependencies:

```bash
pip install requests
```

## Getting Your Snapchat Export

1. Go to https://accounts.snapchat.com/accounts/downloadmydata
2. Request your data export.
3. Download and extract the ZIP from Snapchat.
4. Locate the file `memories_history.json`.
5. Place it anywhere and update the script paths accordingly.

## Configuration

In the script set:

```python
JSON_FILE = Path("/path/to/memories_history.json")
OUTPUT_DIR = Path("/path/to/output/media")
```

The `media` folder will be created automatically.

## How File Naming Works

Each memory receives a deterministic numeric name based on its order:

```
00001
00002
00003
...
```

After downloading and extension detection:

```
00001.jpg
00002.mp4
00003.zip → extracted → <uuid>-main.jpg
```

ZIP-based memories keep their original Snapchat filenames for correctness.

## ZIP Handling Logic

When a ZIP is downloaded:

1. Save as `00003.zip`.
2. Extract into the output directory.
3. Delete all `*-overlay.*` files and any non-`*-main.*` files.
4. Keep only `<uuid>-main.jpg`.
5. Remove the original `.zip`.

This ensures your media directory contains only clean, final media files without overlays or metadata artifacts.

## Running the Script

```bash
python3 downloader.py
```

Example output:

```
Starting download of 842 Snapchat memories with 32 workers…
✅ [1/842] 00001.jpg
✅ [2/842] 00002.mp4
✅ [3/842] 2797cf8c-main.jpg
...
Finished in 31.4s → 842 succeeded, 0 failed
```

## Example Directory Structure

```
media/
├── 00001.jpg
├── 00002.mp4
├── 2797cf8c-b23c-main.jpg
├── 00004.jpg
└── ...
```

## Script Behavior Summary

| Behavior           | Description                                   |
| ------------------ | --------------------------------------------- |
| Detect extension   | Uses HTTP headers to determine real file type |
| Skip existing      | Prevents duplicate downloads                  |
| Extract ZIPs       | Saves only `*-main.*`, deletes overlays       |
| Clean up           | Deletes ZIP files after extraction            |
| Parallel downloads | Increases speed significantly                 |
| Idempotent         | Safe to run repeatedly                        |

## Optional Enhancements

- Rename extracted `*-main.*` files to match numeric index (e.g., `00003.jpg`)
- Export a CSV with metadata
- Add a fully async downloader (`aiohttp`)
- Add SHA256 verification
- Implement retry logic with exponential backoff
- Dockerize the downloader
- GitHub Actions automation (CI)