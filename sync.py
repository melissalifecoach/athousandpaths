#!/usr/bin/env python3
"""
Sync pages from the live Squarespace site.
Re-downloads all HTML pages so the navigation stays up to date.
"""

import os
import time
import urllib.request
from pathlib import Path

BASE_URL = "https://www.athousandpaths.com"
SITE_DIR = Path("www.athousandpaths.com")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

def url_for(filepath):
    """Convert a local .html filepath to its live URL."""
    rel = filepath.relative_to(SITE_DIR)
    path = str(rel)

    # Skip non-HTML and special files
    if not path.endswith(".html"):
        return None
    if path in ("serve.json",):
        return None

    # Handle query-string pages like blog?month=01-2021.html
    if "?" in path:
        slug = path.replace(".html", "")
        return f"{BASE_URL}/{slug}"

    # Strip .html extension for clean URL
    slug = path[:-5]  # remove .html
    return f"{BASE_URL}/{slug}"

def download(url, dest):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                dest.write_bytes(resp.read())
                return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
    return False

def main():
    html_files = sorted(SITE_DIR.rglob("*.html"))
    total = len(html_files)
    print(f"Found {total} HTML files to sync...\n")

    success = 0
    skipped = 0
    failed = []

    for i, filepath in enumerate(html_files, 1):
        url = url_for(filepath)
        if not url:
            skipped += 1
            continue

        print(f"[{i}/{total}] {filepath.name} → {url}")
        ok = download(url, filepath)
        if ok:
            print(f"  ✓ Updated")
            success += 1
        else:
            failed.append(str(filepath))

        time.sleep(0.3)  # be polite to Squarespace servers

    print(f"\n✅ Done! {success} updated, {skipped} skipped, {len(failed)} failed")
    if failed:
        print("\nFailed pages:")
        for f in failed:
            print(f"  {f}")

if __name__ == "__main__":
    main()
