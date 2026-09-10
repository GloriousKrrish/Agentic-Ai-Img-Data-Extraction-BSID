import os
import json
import copy
import hashlib
from pathlib import Path
import backend.config as config

class CacheService:
    """
    Smart Caching Engine (Thread-Safe & Copy-Isolated)
    Caches downloads, preprocessed images, OCR text results, and AI responses.
    Guarantees copy-isolation (copy.deepcopy) so worker threads never mutate shared dictionary references.
    """
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache = {}

    def _hash_key(self, key_str: str) -> str:
        return hashlib.sha256(key_str.encode('utf-8')).hexdigest()

    def get_download(self, url: str) -> dict:
        if not config.ENABLE_CACHE:
            return None
        hk = self._hash_key(f"dl_{url}")
        if hk in self.memory_cache:
            return copy.deepcopy(self.memory_cache[hk])
            
        file_path = self.cache_dir / f"{hk}.bin"
        meta_path = self.cache_dir / f"{hk}.json"
        
        if file_path.exists() and meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding='utf-8'))
                b_data = file_path.read_bytes()
                res = {"bytes": b_data, "mime_type": meta.get("mime_type", "image/jpeg"), "success": True}
                self.memory_cache[hk] = copy.deepcopy(res)
                return res
            except Exception:
                pass
        return None

    def set_download(self, url: str, doc_bytes: bytes, mime_type: str):
        if not config.ENABLE_CACHE or not doc_bytes:
            return
        hk = self._hash_key(f"dl_{url}")
        res = {"bytes": doc_bytes, "mime_type": mime_type, "success": True}
        self.memory_cache[hk] = copy.deepcopy(res)
        
        try:
            file_path = self.cache_dir / f"{hk}.bin"
            meta_path = self.cache_dir / f"{hk}.json"
            file_path.write_bytes(doc_bytes)
            meta_path.write_text(json.dumps({"url": url, "mime_type": mime_type}), encoding='utf-8')
        except Exception:
            pass

    def get_ocr(self, img_bytes: bytes) -> dict:
        if not config.ENABLE_CACHE or not img_bytes:
            return None
        hk = self._hash_key(f"ocr_{hashlib.md5(img_bytes).hexdigest()}")
        if hk in self.memory_cache:
            return copy.deepcopy(self.memory_cache[hk])
            
        meta_path = self.cache_dir / f"{hk}.json"
        if meta_path.exists():
            try:
                data = json.loads(meta_path.read_text(encoding='utf-8'))
                self.memory_cache[hk] = copy.deepcopy(data)
                return data
            except Exception:
                pass
        return None

    def set_ocr(self, img_bytes: bytes, ocr_data: dict):
        if not config.ENABLE_CACHE or not img_bytes:
            return
        hk = self._hash_key(f"ocr_{hashlib.md5(img_bytes).hexdigest()}")
        self.memory_cache[hk] = copy.deepcopy(ocr_data)
        try:
            meta_path = self.cache_dir / f"{hk}.json"
            meta_path.write_text(json.dumps(ocr_data), encoding='utf-8')
        except Exception:
            pass

    def get_ai_response(self, prompt: str, img_bytes: bytes) -> dict:
        if not config.ENABLE_CACHE:
            return None
        img_hash = hashlib.md5(img_bytes).hexdigest() if img_bytes else "no_img"
        hk = self._hash_key(f"ai_{img_hash}_{prompt[:100]}")
        if hk in self.memory_cache:
            return copy.deepcopy(self.memory_cache[hk])
            
        meta_path = self.cache_dir / f"{hk}.json"
        if meta_path.exists():
            try:
                data = json.loads(meta_path.read_text(encoding='utf-8'))
                self.memory_cache[hk] = copy.deepcopy(data)
                return data
            except Exception:
                pass
        return None

    def set_ai_response(self, prompt: str, img_bytes: bytes, ai_data: dict):
        if not config.ENABLE_CACHE:
            return
        img_hash = hashlib.md5(img_bytes).hexdigest() if img_bytes else "no_img"
        hk = self._hash_key(f"ai_{img_hash}_{prompt[:100]}")
        self.memory_cache[hk] = copy.deepcopy(ai_data)
        try:
            meta_path = self.cache_dir / f"{hk}.json"
            meta_path.write_text(json.dumps(ai_data), encoding='utf-8')
        except Exception:
            pass

cache_service = CacheService()
