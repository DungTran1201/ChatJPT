import urllib.request
import re
import os
import sys
import json
import time
from pathlib import Path

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "ai-backend" / "data"

FOLDERS = {
    'N5': 'https://drive.google.com/drive/folders/14cvGKUh4Gu7ojd2JE6FzWL5hCTSFwhaz',
    'N4': 'https://drive.google.com/drive/folders/1HytgiK1tJaSGW4wUmHYQRbniPYu3-NLh',
    'N3': 'https://drive.google.com/drive/folders/1lwUZCcGfAl2HwhrQVz-R4s-dXMEKpuZD',
    'N2': 'https://drive.google.com/drive/folders/1lCVccq1e-dCWKR8CzZX7EbmRkuLPah7F',
    'N1': 'https://drive.google.com/drive/folders/1451604QICFd_zpWxYXLz5jJj6z2Xh4RI',
    'Kaiwa': 'https://drive.google.com/drive/folders/17JFLZlqVgwxJFS0BkHAv1I_szVJz-aQB'
}

REQ_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', '_', name)
    return cleaned.strip()

def extract_items_from_html(html: str):
    # Pattern matching aria-label="..." and ssk="...:33_CHAR_ID-..."
    pattern = re.compile(
        r'aria-label="([^"]+)"[^>]*?ssk=[\'\"][^:\'\"]+:[^:\'\"]+:([a-zA-Z0-9_-]{33})',
        re.DOTALL
    )
    items = []
    seen = set()
    for match in pattern.finditer(html):
        label, fid = match.groups()
        # Clean label suffixes
        name = label
        for suffix in [' PDF Shared', ' Audio Shared', ' Document Shared', ' Shared folder', ' Shared']:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
        
        # Skip folders
        if 'folder' in label.lower() or 'thư mục' in label.lower():
            continue

        fid_clean = fid[:33]
        if fid_clean not in seen:
            seen.add(fid_clean)
            items.append((name, fid_clean))

    return items

def download_file(fid: str, target_path: Path):
    if target_path.exists() and target_path.stat().st_size > 2048:
        return True, f"Cached ({target_path.stat().st_size:,} bytes)"
    
    url = f"https://drive.usercontent.google.com/download?id={fid}&export=download"
    try:
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = resp.read()
            # If Google Drive returns HTML confirmation page for large files
            if len(data) < 2000 and b"confirm=" in data:
                confirm_token = re.search(r'confirm=([0-9a-zA-Z_-]+)', data.decode('utf-8', errors='ignore'))
                if confirm_token:
                    confirm_url = f"{url}&confirm={confirm_token.group(1)}"
                    req2 = urllib.request.Request(confirm_url, headers=REQ_HEADERS)
                    with urllib.request.urlopen(req2, timeout=60) as resp2:
                        data = resp2.read()
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'wb') as f:
                f.write(data)
            return True, f"Downloaded {len(data):,} bytes"
    except Exception as e:
        return False, str(e)

def main():
    download_summary = {}
    total_downloaded = 0

    for lvl, folder_url in FOLDERS.items():
        lvl_key = lvl.lower()
        target_dir = DATA_DIR / "reference_materials" / lvl_key
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n==========================================")
        print(f"Scanning Drive folder for {lvl}...")
        try:
            req = urllib.request.Request(folder_url, headers=REQ_HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            items = extract_items_from_html(html)
            print(f"Found {len(items)} downloadable files for {lvl}.")
            download_summary[lvl] = []

            for name, fid in items:
                safe_name = sanitize_filename(name)
                if not any(safe_name.lower().endswith(ext) for ext in ['.pdf', '.mp3', '.docx', '.zip']):
                    safe_name += '.pdf'
                target_file = target_dir / safe_name
                print(f"  -> Downloading [{lvl}] {safe_name}...")
                ok, msg = download_file(fid, target_file)
                print(f"     Status: {'OK' if ok else 'FAIL'} - {msg}")
                if ok:
                    total_downloaded += 1
                download_summary[lvl].append({
                    "name": name,
                    "safe_name": safe_name,
                    "id": fid,
                    "local_path": str(target_file.relative_to(BASE_DIR)).replace('\\', '/'),
                    "file_type": "pdf" if safe_name.lower().endswith('.pdf') else "audio" if safe_name.lower().endswith('.mp3') else "doc",
                    "success": ok,
                    "size_bytes": target_file.stat().st_size if target_file.exists() else 0
                })
                time.sleep(0.3)
        except Exception as e:
            print(f"Error scanning {lvl}: {e}")

    summary_file = DATA_DIR / "download_manifest.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(download_summary, f, ensure_ascii=False, indent=2)
    print(f"\nTotal files processed: {total_downloaded}. Manifest saved to {summary_file}")

if __name__ == '__main__':
    main()
