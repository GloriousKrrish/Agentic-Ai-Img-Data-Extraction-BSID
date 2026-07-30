import io
import json
import csv
from pathlib import Path
from PIL import Image

def determine_pipeline_type(file_bytes: bytes, filename: str, mime_type: str = "") -> dict:
    """
    Automatic Pipeline Router.
    Determines whether an uploaded file MUST run the Single Document Pipeline or Batch Queue Engine.

    Rules:
    1. Images (JPG, PNG, WEBP, BMP), PDF, DOCX, TXT, JSON, XML -> SINGLE_DOCUMENT (NEVER enters batch queue).
    2. ZIP Archives -> BATCH_DATASET.
    3. XLSX / CSV -> Inspects content. If contains URL list or batch dataset -> BATCH_DATASET; otherwise SINGLE_DOCUMENT.
    """
    ext = Path(filename).suffix.lower()
    clean_mime = (mime_type or "").lower()

    # 1. Single Document Types (Images, PDF, DOCX, TXT, JSON, XML)
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.svg'}
    SINGLE_DOC_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.json', '.xml', '.rtf'}

    if ext in IMAGE_EXTENSIONS or 'image' in clean_mime:
        return {
            "pipeline_type": "SINGLE_DOCUMENT",
            "category": "Image Document",
            "is_batch": False,
            "reason": "Single image uploaded. Executing single document vision pipeline."
        }

    if ext in SINGLE_DOC_EXTENSIONS or 'pdf' in clean_mime or 'json' in clean_mime:
        return {
            "pipeline_type": "SINGLE_DOCUMENT",
            "category": "Single File Document",
            "is_batch": False,
            "reason": "Single document file uploaded. Executing single document pipeline."
        }

    # 2. ZIP Archives (Multi-file batch)
    if ext == '.zip' or 'zip' in clean_mime:
        return {
            "pipeline_type": "BATCH_DATASET",
            "category": "ZIP Archive Batch",
            "is_batch": True,
            "reason": "ZIP archive uploaded. Triggering batch processing engine."
        }

    # 3. Excel and CSV Inspection
    if ext in ['.xlsx', '.xls', '.csv'] or 'spreadsheet' in clean_mime or 'excel' in clean_mime:
        is_batch_dataset = _inspect_excel_or_csv_for_batch(file_bytes, ext)
        if is_batch_dataset:
            return {
                "pipeline_type": "BATCH_DATASET",
                "category": "Batch Dataset Queue",
                "is_batch": True,
                "reason": "Workbook detected as a multi-row URL batch dataset. Routing to Batch Queue Engine."
            }
        else:
            return {
                "pipeline_type": "SINGLE_DOCUMENT",
                "category": "Excel Sheet Document",
                "is_batch": False,
                "reason": "Excel sheet detected as single document dataset. Executing single document pipeline."
            }

    # Fallback to Single Document
    return {
        "pipeline_type": "SINGLE_DOCUMENT",
        "category": "General Document",
        "is_batch": False,
        "reason": "Defaulting to single document pipeline."
    }

def _inspect_excel_or_csv_for_batch(file_bytes: bytes, ext: str) -> bool:
    """
    Inspects Excel or CSV content to check if it's a batch queue containing image URLs or >20 dataset rows.
    """
    try:
        if ext == '.csv':
            decoded = file_bytes.decode('utf-8', errors='ignore')
            lines = [line for line in decoded.splitlines() if line.strip()]
            if len(lines) > 25:
                return True
            header = lines[0].lower() if lines else ""
            if any(k in header for k in ["url", "image_url", "imageurl", "file_url", "doc_url"]):
                return True
            return False

        elif ext in ['.xlsx', '.xls']:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
            sheet = wb.active
            row_count = 0
            has_url_column = False

            for i, row in enumerate(sheet.iter_rows(values_only=True)):
                if not row or not any(row):
                    continue
                row_count += 1
                if i == 0:
                    headers = [str(cell).lower() for cell in row if cell is not None]
                    if any(k in h for h in headers for k in ["url", "image_url", "imageurl", "file_url", "doc_url"]):
                        has_url_column = True

                if row_count > 25 or has_url_column:
                    wb.close()
                    return True

            wb.close()
            return False
    except Exception:
        return False

    return False
