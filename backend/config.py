import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ENGINE_DIR = BASE_DIR / "Agentic-Ai-Img-Data-Extraction-BSID-main"

load_dotenv(PROJECT_ENGINE_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_EXCEL_FILENAME = "Invoice_data_capture.xlsx"
EXCEL_PATH = PROJECT_ENGINE_DIR / DEFAULT_EXCEL_FILENAME
QUEUE_DIR = PROJECT_ENGINE_DIR / "queue"
RESULTS_DIR = PROJECT_ENGINE_DIR / "results"

MODELS_PRIORITY = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-1.5-flash"
]
