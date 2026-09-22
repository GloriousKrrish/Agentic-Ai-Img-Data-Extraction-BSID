import os
import json
import shutil
from pathlib import Path

ROOT = Path(r"c:\Users\admin\OneDrive\Desktop\PROJECTS\Agentic-Ai-Img-Data-Extraction-BSID-main")
BM_DIR = ROOT / "benchmark"
DS_DIR = BM_DIR / "datasets"
GT_DIR = BM_DIR / "ground_truth"
SCHEMA_DIR = BM_DIR / "schemas"
REPORTS_DIR = BM_DIR / "reports"

os.makedirs(DS_DIR, exist_ok=True)
os.makedirs(GT_DIR, exist_ok=True)
os.makedirs(SCHEMA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

print("Benchmark directory layout created successfully.")
