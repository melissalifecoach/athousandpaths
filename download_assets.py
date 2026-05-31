#!/usr/bin/env python3
"""
Download Squarespace CSS/JS assets and update all HTML files to use local paths.
Run from the project root: python3 download_assets.py
"""

import re
import urllib.request
from pathlib import Path

SITE_DIR = Path("www.athousandpaths.com")
ASSETS_DIR = SITE_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# The Squarespace CSS/JS files to download and their local filenames
ASSETS = [
    {
        "url": "https://static1.squarespace.com/static/vta/5c5a519771c10ba3470d8101/versioned-assets/1779474175394-BX8A77FBS93OTW10XH55/static.css",
        "local": "static.css",
    },
    {
        "url": "https://static1.squarespace.com/static/versioned-site-css/55762892e4b08f79780d92e7/128/5c5a519771c10ba3470d8101/659c6112d8953319b03ce742/1785/site.css?nocustom=true",
        "local": "site.css",
    },
    {
        "url": "https://static1.squarespace.com/static/vta/5c5a519771c10ba3470d8101/scripts/site-bundle.0fb88bb12daf6927e98393f87c27cbd7.js",
        "local": "site-bundle.js",
    },
]

def download(url, dest_path):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                dest_path.write_bytes(resp.read())
                size = dest_path.stat().st_size
                print(f"  ✓ {dest_path.name} ({size:,} bytes)")
                return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
    return False

def update_html_files(replacements):
    html_files = list(SITE_DIR.rglob("*.html"))
    print(f"\nUpdating {len(html_files)} HTML files...")
    updated = 0
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8", errors="ignore")
        original = content
        for old_url, new_path in replacements:
            content = content.replace(old_url, new_path)
        if content != original:
            html_file.write_text(content, encoding="utf-8")
            updated += 1
    print(f"✅ Updated {updated} files.")

def main():
    print("⬇  Downloading Squarespace CSS/JS assets...\n")
    replacements = []
    failed = []

    for asset in ASSETS:
        url = asset["url"]
        filename = asset["local"]
        dest = ASSETS_DIR / filename
        local_path = f"/assets/{filename}"

        print(f"Downloading {filename}...")
        ok = download(url, dest)
        if ok:
            replacements.append((url, local_path))
            # Also replace the URL without query string (for site.css)
            clean_url = url.split("?")[0]
            if clean_url != url:
                replacements.append((clean_url, local_path))
        else:
            failed.append(url)

    # Also replace the partial scripts path
    replacements.append((
        "https://static1.squarespace.com/static/vta/5c5a519771c10ba3470d8101/scripts/",
        "/assets/"
    ))

    if failed:
        print(f"\n❌ {len(failed)} assets failed to download:")
        for f in failed:
            print(f"  {f}")
    else:
        print("\n✅ All assets downloaded!")

    update_html_files(replacements)

    print("\n🎉 Done! CSS and JS are now hosted locally.")
    print("  Run: npm start  →  check the site looks right")
    print("  Then: npx vercel --prod  →  deploy")

if __name__ == "__main__":
    main()
