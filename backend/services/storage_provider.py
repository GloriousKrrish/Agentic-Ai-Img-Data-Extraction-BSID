import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

class StorageProvider:
    """
    v4.2 StorageProvider Abstraction.
    Abstracts local disk storage and cloud S3-compatible object storage.
    """
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(r"c:\Users\admin\OneDrive\Desktop\PROJECTS\Agentic-Ai-Img-Data-Extraction-BSID-main\uploads")
        os.makedirs(self.base_dir, exist_ok=True)

    def put(self, key: str, data_bytes: bytes, content_type: str = "application/octet-stream") -> str:
        filepath = self.base_dir / key
        os.makedirs(filepath.parent, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(data_bytes)
        return str(filepath)

    def get(self, key: str) -> Optional[bytes]:
        filepath = self.base_dir / key
        if not filepath.exists():
            return None
        with open(filepath, "rb") as f:
            return f.read()

    def delete(self, key: str) -> bool:
        filepath = self.base_dir / key
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def exists(self, key: str) -> bool:
        return (self.base_dir / key).exists()

    def generate_download_url(self, key: str, expires_in_sec: int = 3600) -> str:
        return f"/api/storage/download/{key}"

storage_provider = StorageProvider()
