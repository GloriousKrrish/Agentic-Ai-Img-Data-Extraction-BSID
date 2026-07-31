import os
import multiprocessing
from pathlib import Path
from tempfile import gettempdir
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ENGINE_DIR = BASE_DIR

load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_EXCEL_FILENAME = "Invoice_data_capture.xlsx"
EXCEL_PATH = PROJECT_ENGINE_DIR / DEFAULT_EXCEL_FILENAME
QUEUE_DIR = PROJECT_ENGINE_DIR / "queue"
RESULTS_DIR = PROJECT_ENGINE_DIR / "results"

# Performance & Concurrency Tuning
MAX_WORKERS = int(os.getenv("MAX_WORKERS", max(multiprocessing.cpu_count() * 2, 10)))
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", 15))
OCR_TIMEOUT = int(os.getenv("OCR_TIMEOUT", 20))
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", 45))
RETRY_COUNT = int(os.getenv("RETRY_COUNT", 3))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 50))
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
CACHE_DIR = Path(os.getenv("CACHE_DIR", str(Path(gettempdir()) / "ai_cognitive_cache")))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_config_vars():
    global GEMINI_API_KEY, GEMINI_PRIMARY_MODEL, MODELS_PRIORITY, MAX_WORKERS
    load_dotenv(BASE_DIR / ".env", override=True)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_PRIMARY_MODEL = os.getenv("GEMINI_PRIMARY_MODEL", "gemini-3.1-flash-lite")
    raw_priority = os.getenv(
        "MODELS_PRIORITY",
        "gemini-3.1-flash-lite,gemini-flash-latest,gemini-3.5-flash,gemini-3.1-flash-image,gemini-flash-lite-latest"
    )
    MODELS_PRIORITY = [m.strip() for m in raw_priority.split(",") if m.strip()]
    if GEMINI_PRIMARY_MODEL not in MODELS_PRIORITY:
        MODELS_PRIORITY.insert(0, GEMINI_PRIMARY_MODEL)

load_config_vars()
