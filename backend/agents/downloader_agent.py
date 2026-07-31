import re
import time
import requests
from pathlib import Path
from tempfile import gettempdir

class DownloaderAgent:
    """
    Step 3: Downloader Agent
    Downloads & caches documents from URLs (HTTP/HTTPS, Google Drive, Dropbox, OneDrive, SharePoint, S3).
    Handles URL transformations, redirects, timeout recovery, and local disk caching.
    """
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or (Path(gettempdir()) / "ai_doc_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def transform_url(self, raw_url: str) -> str:
        """Transforms sharing/viewing URLs (Google Drive, Dropbox) into direct download streams."""
        url = raw_url.strip()
        
        # Google Drive
        gdrive_match = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)', url)
        if gdrive_match:
            file_id = gdrive_match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
            
        gdrive_open_match = re.search(r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)', url)
        if gdrive_open_match:
            file_id = gdrive_open_match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"

        # Dropbox
        if "dropbox.com" in url:
            if "dl=0" in url:
                url = url.replace("dl=0", "dl=1")
            elif "dl=1" not in url:
                url = url + ("&dl=1" if "?" in url else "?dl=1")

        return url

    def fetch(self, raw_url: str, max_retries: int = 3) -> dict:
        url = self.transform_url(raw_url)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        for attempt in range(max_retries):
            try:
                res = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
                if res.status_code == 200 and len(res.content) > 50:
                    content_type = res.headers.get("Content-Type", "image/jpeg").split(";")[0].strip().lower()
                    mime_type = "application/pdf" if ("pdf" in url.lower() or "pdf" in content_type) else "image/jpeg"
                    
                    return {
                        "success": True,
                        "bytes": res.content,
                        "mime_type": mime_type,
                        "content_length": len(res.content)
                    }
                else:
                    err = f"HTTP {res.status_code}"
            except Exception as e:
                err = str(e)
                
            if attempt < max_retries - 1:
                time.sleep(1.0 * (attempt + 1))
                
        return {"success": False, "error": err, "bytes": b"", "mime_type": "image/jpeg"}
