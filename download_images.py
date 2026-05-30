#!/usr/bin/env python3
"""
Download all images from Squarespace CDN and update HTML files to use local paths.
Run from the project root: python3 download_images.py
"""

import os
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path

SITE_DIR = Path("www.athousandpaths.com")
IMAGES_DIR = SITE_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

CDN_PATTERN = re.compile(r'https://images\.squarespace-cdn\.com/[^\s"\'<>]+')

def url_to_filename(url):
    """Turn a CDN URL into a safe local filename."""
    # Remove query strings
    url_clean = url.split("?")[0]
    # Get the last path segment (the UUID or image name)
    filename = url_clean.split("/")[-1]
    # URL-decode (handles spaces encoded as %20 etc)
    filename = urllib.parse.unquote(filename)
    # Replace spaces and special chars that are bad in filenames
    filename = filename.replace(" ", "_").replace("+", "_")
    # Truncate if too long
    if len(filename) > 120:
        filename = filename[-120:]
    return filename

def collect_urls():
    """Find all unique Squarespace CDN image URLs across all HTML files."""
    urls = set()
    for html_file in SITE_DIR.rglob("*.html"):
        content = html_file.read_text(encoding="utf-8", errors="ignore")
        found = CDN_PATTERN.findall(content)
        urls.update(found)
    return sorted(urls)

def download_image(url, dest_path):
    """Download one image. Returns True on success."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status == 200:
                dest_path.write_bytes(resp.read())
                return True
    except Exception as e:
        print(f"    ✗ FAILED: {e}")
    return False

def update_html_files(url_to_local):
    """Replace all CDN URLs in HTML files with local paths."""
    html_files = list(SITE_DIR.rglob("*.html"))
    print(f"\nUpdating {len(html_files)} HTML files with local image paths...")
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8", errors="ignore")
        original = content
        for cdn_url, local_path in url_to_local.items():
            content = content.replace(cdn_url, local_path)
        if content != original:
            html_file.write_text(content, encoding="utf-8")
    print("✅ HTML files updated.")

def main():
    print("🔍 Scanning HTML files for Squarespace CDN image URLs...")
    all_urls = collect_urls()
    total = len(all_urls)
    print(f"Found {total} unique image URLs.\n")

    url_to_local = {}  # cdn_url → /images/filename
    success = 0
    failed = []
    skipped = 0

    for i, url in enumerate(all_urls, 1):
        filename = url_to_filename(url)
        dest_path = IMAGES_DIR / filename

        # Track the local web path for HTML replacement
        local_web_path = f"/images/{filename}"
        url_to_local[url] = local_web_path

        if dest_path.exists():
            print(f"[{i}/{total}] ⏭  Already exists: {filename}")
            skipped += 1
            continue

        print(f"[{i}/{total}] ⬇  {filename}")
        ok = download_image(url, dest_path)
        if ok:
            success += 1
        else:
            failed.append(url)

        time.sleep(0.15)  # be polite to Squarespace servers

    print(f"\n✅ Download complete: {success} downloaded, {skipped} skipped, {len(failed)} failed")

    if failed:
        print("\n❌ Failed URLs (saved to failed_images.txt):")
        failed_log = Path("failed_images.txt")
        failed_log.write_text("\n".join(failed))
        for f in failed[:10]:
            print(f"  {f}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more (see failed_images.txt)")

    # Update HTML files to use local paths
    update_html_files(url_to_local)

    print("\n🎉 All done! Next steps:")
    print("  1. Run: npm start  (to preview locally)")
    print("  2. Check the site looks good")
    print("  3. Run: vercel --prod  (to deploy)")

if __name__ == "__main__":
    main()
