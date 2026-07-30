import os
import sys
import argparse
import openpyxl
from pathlib import Path
from backend.services.invoice_engine import (
    detect_url_column_in_excel,
    process_invoice_document
)
from backend.services.agentic_engine import (
    DocumentFetcherAgent,
    ImagePreprocessorAgent,
    ValidationAgent,
    ResilientExcelWriterAgent
)

def run_production_pipeline(input_path: str = "testing.xlsx", output_path: str = "output_extracted.xlsx"):
    print("\n=========================================================================")
    print(">>> PRODUCTION DOCUMENT INTELLIGENCE PIPELINE")
    print("=========================================================================\n")

    input_file = Path(input_path)
    if not input_file.exists():
        print(f"[FAIL] Input file '{input_path}' does not exist!")
        sys.exit(1)

    print(f"[1/5] Loading Input Workbook: '{input_path}'...")
    file_bytes = input_file.read_bytes()

    # Step 1: Detect URL tasks
    print("[2/5] Auto-Detecting Document URL Column...")
    tasks = detect_url_column_in_excel(file_bytes, input_file.name)
    if not tasks:
        print("[FAIL] No document image or PDF URLs found in workbook!")
        sys.exit(1)

    print(f"  -> Discovered {len(tasks)} document tasks.\n")

    # Step 2: Initialize Pipeline Components
    fetcher = DocumentFetcherAgent()
    preprocessor = ImagePreprocessorAgent()
    validator = ValidationAgent()
    writer = ResilientExcelWriterAgent()

    processed_records = []
    discovered_keys = set()

    # Step 3: Process Row-by-Row
    print("[3/5] Processing Documents & Extracting Fields with AI Vision...")
    print("-------------------------------------------------------------------------")

    for idx, task in enumerate(tasks, start=1):
        url = task["url"]
        row_num = task["rowIndex"]
        print(f"[{idx}/{len(tasks)}] Row #{row_num}: Fetching {url[:55]}...")

        # Download
        f_res = fetcher.fetch(url, max_retries=3)
        if not f_res["success"]:
            print(f"  [FAIL] Download Failed: {f_res.get('error')}")
            continue

        # Preprocess
        prep_bytes = preprocessor.preprocess(f_res["bytes"], f_res["mime_type"])

        # Vision AI Semantic Extraction
        fields = process_invoice_document(prep_bytes, f_res["mime_type"])
        fields["sourceUrl"] = url

        for k in fields.keys():
            discovered_keys.add(k)

        val_res = validator.validate(fields)

        record = {
            "rowIndex": row_num,
            "fields": fields,
            "confidence": val_res["confidence"]
        }
        processed_records.append(record)

        # Immediate Resilient Save
        writer.write_workbook(processed_records, output_path)
        print(f"  [SUCCESS] Extracted {len(fields)} fields | Auto-saved Row #{row_num} -> '{output_path}'")

    print("\n-------------------------------------------------------------------------")
    print(f"[4/5] Dynamic Schema Generation Complete ({len(discovered_keys)} Unified Columns)")
    print(f"      Active Schema: {sorted(list(discovered_keys))}")

    # Final Save
    writer.write_workbook(processed_records, output_path)
    print(f"[5/5] Saved Output Workbook: '{output_path}'")

    print("\n=========================================================================")
    print("[SUCCESS] PRODUCTION PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Total Extracted Rows: {len(processed_records)}")
    print(f"Output File: {output_path}")
    print("=========================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Production Document Intelligence Pipeline")
    parser.add_argument("--input", default="testing.xlsx", help="Path to input Excel or CSV workbook")
    parser.add_argument("--output", default="output_extracted.xlsx", help="Path to output Excel workbook")
    args = parser.parse_args()

    run_production_pipeline(args.input, args.output)
