"""
Copyright (c) 2025 Jagadeeshgowdayt
This file is part of PDF-extractor-with-metadata, released under the MIT License.
See LICENSE in the project root for details.
"""
"""Scraper for a university resource portal

Queries a public search API, downloads approved PDF resources, extracts metadata,
converts pages to JPEGs, and writes a results.jsonl with paths and metadata.
"""
import os
import json
import time
import argparse
from typing import List
from pathlib import Path

import requests

from utils import build_filename
from pdf_tools import download_pdf, extract_pdf_metadata, pdf_to_jpegs


BASE_URL = "<YOUR_RESOURCE_PORTAL_BASE_URL>"  # Set your resource portal base URL here
SEARCH_API = BASE_URL + "/api/search"
DOWNLOAD_API = BASE_URL + "/api/resource/download"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def get_signed_url(key: str) -> str:
    """Call the /api/resource/download?key=... endpoint to get a signed URL."""
    if key.startswith("http://") or key.startswith("https://"):
        return key
    resp = requests.get(DOWNLOAD_API, params={"key": key}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("url")


def ensure_unique_path(path: Path) -> Path:
    """If path exists, append a numeric suffix before extension to make unique."""
    if not path.exists():
        return path
    base = path.with_suffix("")
    ext = path.suffix
    i = 1
    while True:
        candidate = Path(f"{base}_{i}{ext}")
        if not candidate.exists():
            return candidate
        i += 1


def process_resource(resource: dict, out_base: Path, lowercase: bool = False) -> dict:
    key = resource.get("fileUrl") or resource.get("file_url") or resource.get("url")
    if not key:
        return {"error": "no fileUrl", "resource": resource}

    try:
        file_url = get_signed_url(key)
    except Exception as e:
        return {"error": f"could not get signed url: {e}", "key": key}
    title = resource.get("courseName") or resource.get("title") or resource.get("course")
    school = resource.get("school") or ""

    pdf_dir = out_base / "pdfs"
    images_base = out_base / "images"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    images_base.mkdir(parents=True, exist_ok=True)

    pdf_name = os.path.basename(file_url.split("?")[0])
    pdf_path = pdf_dir / pdf_name

    try:
        download_pdf(file_url, str(pdf_path))
    except Exception as e:
        return {"error": f"download failed: {e}", "url": file_url}

    meta = extract_pdf_metadata(str(pdf_path))
    page_count = meta.get("page_count", 0) or 0

    resource_id = pdf_name.replace(".pdf", "")
    # All images in one folder, unique names
    try:
        img_paths = pdf_to_jpegs(str(pdf_path), str(images_base), resource_id)
    except Exception as e:
        return {"error": f"conversion failed: {e}", "url": file_url}

    normalized = []
    for i, ip in enumerate(img_paths, start=1):
        new_name = build_filename(title, school, i, ext="jpeg", lowercase=lowercase)
        new_path = images_base / new_name
        unique_path = ensure_unique_path(new_path)
        try:
            os.replace(ip, str(unique_path))
        except Exception:
            os.rename(ip, str(unique_path))
        normalized.append(str(unique_path))

    result = {
        "id": resource.get("id"),
        "title": title,
        "school": school,
        "file_url": file_url,
        "pdf_path": str(pdf_path),
        "metadata": meta,
        "images": normalized,
    }
    return result


def fetch_search(q: str = "", max_results: int = 20) -> List[dict]:
    params = {"q": q}
    resp = requests.get(SEARCH_API, params=params, timeout=30)
    resp.raise_for_status()
    items = resp.json()
    if not isinstance(items, list):
        return []
    return items[:max_results]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", "-q", default="", help="Search query to send to UniVault")
    parser.add_argument("--max", "-m", type=int, default=70, help="Maximum resources to process")
    parser.add_argument("--smoke", action="store_true", help="Run a small smoke test (max 3)")
    parser.add_argument("--lowercase", action="store_true", help="Lowercase output filenames")
    args = parser.parse_args()

    max_items = 3 if args.smoke else args.max
    out_base = OUTPUT_DIR
    out_base.mkdir(parents=True, exist_ok=True)
    results_file = out_base / "results.jsonl"

    print(f"Fetching search q={args.query!r} max={max_items}")
    items = fetch_search(args.query, max_items)
    print(f"Found {len(items)} items")

    with open(results_file, "w", encoding="utf-8") as rf:
        for i, item in enumerate(items, start=1):
            print(f"[{i}/{len(items)}] Processing {item.get('title')}")
            res = process_resource(item, out_base, lowercase=args.lowercase)
            rf.write(json.dumps(res, ensure_ascii=False) + "\n")
            # polite rate limit
            time.sleep(1)

    print(f"Done. Results written to {results_file}")


if __name__ == "__main__":
    main()
