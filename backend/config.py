import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ENGINE_DIR = BASE_DIR

load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_EXCEL_FILENAME = "Invoice_data_capture.xlsx"
EXCEL_PATH = PROJECT_ENGINE_DIR / DEFAULT_EXCEL_FILENAME
QUEUE_DIR = PROJECT_ENGINE_DIR / "queue"
RESULTS_DIR = PROJECT_ENGINE_DIR / "results"

def load_config_vars():
    global GEMINI_API_KEY, GEMINI_PRIMARY_MODEL, MODELS_PRIORITY
    load_dotenv(BASE_DIR / ".env", override=True)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_PRIMARY_MODEL = os.getenv("GEMINI_PRIMARY_MODEL", "gemini-2.5-flash")
    raw_priority = os.getenv(
        "MODELS_PRIORITY",
        "gemini-2.5-flash,gemini-2.5-flash-lite,gemini-1.5-flash,gemini-1.5-flash-8b,gemini-flash-latest"
    )
    MODELS_PRIORITY = [m.strip() for m in raw_priority.split(",") if m.strip()]
    if GEMINI_PRIMARY_MODEL not in MODELS_PRIORITY:
        MODELS_PRIORITY.insert(0, GEMINI_PRIMARY_MODEL)

load_config_vars()


