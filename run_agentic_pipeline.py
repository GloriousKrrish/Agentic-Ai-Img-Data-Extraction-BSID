import time
from pathlib import Path
from backend.services.agentic_engine import (
    WorkbookAnalyzerAgent,
    URLValidatorAgent,
    DocumentFetcherAgent,
    ImagePreprocessorAgent,
    ExtractionAgent,
    SchemaEvolutionAgent,
    ValidationAgent,
    ResilientExcelWriterAgent
)

def run_supervisor_agentic_pipeline():
    excel_file = Path("testing.xlsx")
    output_excel = "extracted_testing_results_v3.xlsx"

    print("\n=========================================================================")
    print(">>> SUPERVISOR AGENT: INITIALIZING MULTI-AGENT DOCUMENT INTELLIGENCE ENGINE")
    print("=========================================================================\n")

    if not excel_file.exists():
        print("[FAIL] Input workbook 'testing.xlsx' not found!")
        return

    file_bytes = excel_file.read_bytes()

    # 1. AGENT 1 — WORKBOOK ANALYZER
    print("[AGENT 1: WORKBOOK ANALYZER] Inspecting workbook structure...")
    analyzer = WorkbookAnalyzerAgent()
    wb_analysis = analyzer.analyze(file_bytes, "testing.xlsx")
    tasks = wb_analysis["url_tasks"]
    print(f"  -> Discovered {wb_analysis['total_rows']} URL document tasks across sheets.\n")

    # Initialize Agents
    url_validator = URLValidatorAgent()
    fetcher = DocumentFetcherAgent()
    preprocessor = ImagePreprocessorAgent()
    extractor = ExtractionAgent()
    schema_agent = SchemaEvolutionAgent()
    validator_agent = ValidationAgent()
    excel_writer = ResilientExcelWriterAgent()

    processed_results = []

    # Process tasks row-by-row with live terminal updates
    for idx, task in enumerate(tasks, start=1):
        url = task["url"]
        row_num = task["row"]

        print(f"-------------------------------------------------------------------------")
        print(f"[SUPERVISOR] Processing Task {idx}/{len(tasks)} (Row #{row_num})")
        print(f"-------------------------------------------------------------------------")

        # AGENT 2 — URL VALIDATOR
        v_res = url_validator.validate(url)
        if not v_res["valid"]:
            print(f"  [AGENT 2: URL VALIDATOR] Invalid URL: {v_res['reason']}")
            continue
        print(f"  [AGENT 2: URL VALIDATOR] URL Validated: {url[:60]}...")

        # AGENT 3 — DOCUMENT FETCHER
        print(f"  [AGENT 3: DOCUMENT FETCHER] Downloading document...")
        f_res = fetcher.fetch(url, max_retries=3)
        if not f_res["success"]:
            print(f"  [AGENT 3: DOCUMENT FETCHER] Failed to download: {f_res.get('error')}")
            continue
        print(f"  [AGENT 3: DOCUMENT FETCHER] Downloaded {len(f_res['bytes'])} bytes ({f_res['mime_type']})")

        # AGENT 4 — IMAGE PREPROCESSOR
        print(f"  [AGENT 4: IMAGE PREPROCESSOR] Auto-rotating & enhancing contrast...")
        prep_bytes = preprocessor.preprocess(f_res["bytes"], f_res["mime_type"])
        print(f"  [AGENT 4: IMAGE PREPROCESSOR] Preprocessing complete.")

        # AGENT 5, 6, 7, 8 — CLASSIFIER, OCR & VISION AI EXTRACTION AGENTS
        print(f"  [AGENT 5/7/8: VISION AI & EXTRACTION] Extracting semantic fields with Gemini AI...")
        ext_data = extractor.extract(prep_bytes, f_res["mime_type"])
        fields = ext_data.get("fields", {})
        fields["sourceUrl"] = url
        category = ext_data.get("category", "Invoice Document")
        print(f"  [AGENT 5/7/8: EXTRACTION AGENT] Category: '{category}' | Extracted Fields: {list(fields.keys())}")

        # AGENT 9 — SCHEMA EVOLUTION AGENT
        current_schema = schema_agent.register(fields)
        print(f"  [AGENT 9: SCHEMA EVOLUTION] Active Schema Columns ({len(current_schema)}): {current_schema}")

        # AGENT 10 — VALIDATION AGENT
        val_res = validator_agent.validate(fields)
        print(f"  [AGENT 10: VALIDATION AGENT] Confidence Score: {val_res['confidence']}%")

        # Record Result
        record = {
            "rowIndex": row_num,
            "category": category,
            "confidence": val_res["confidence"],
            "fields": fields
        }
        processed_results.append(record)

        # AGENT 11 — RESILIENT EXCEL WRITER
        excel_writer.write_workbook(processed_results, output_excel)
        print(f"  [AGENT 11: RESILIENT EXCEL WRITER] Auto-saved Row #{row_num} to '{output_excel}'\n")

    print("=========================================================================")
    print("[SUPERVISOR AGENT] MULTI-AGENT BATCH EXECUTION COMPLETED SUCCESSFULLY!")
    print(f"Total Extracted Records: {len(processed_results)}")
    print(f"Output Workbook Created: '{output_excel}'")
    print("=========================================================================\n")

if __name__ == "__main__":
    run_supervisor_agentic_pipeline()
