import os
import sys
import argparse
from pathlib import Path
from backend.agents.supervisor import SupervisorAgent

def print_audit_report(input_file, output_file, model_name):
    print("\n======================================================================")
    print("EXECUTION PATH AUDIT REPORT (UNIFIED PRODUCTION PIPELINE)")
    print("======================================================================")
    print(f"Entry Point:          run_pipeline.py")
    print(f"Input File:           {input_file}")
    print(f"Output File:          {output_file}")
    print(f"Modules Executed:     backend.agents.supervisor, backend.services.universal_extractor, backend.services.data_sanitizer, backend.agents.excel_writer_agent")
    print(f"Functions Executed:   SupervisorAgent.execute_pipeline() -> process_single_task() -> extract_universal_document() -> sanitize_extracted_dict() -> ExcelWriterAgent.write_row_incremental()")
    print(f"Prompt Schema Used:   INVOICE_SEMANTIC_PROMPT_SCHEMA (Enterprise 17-field Invoice Extraction)")
    print(f"Gemini Model Used:    {model_name}")
    print(f"OCR Engine Used:      Gemini Multimodal Vision API (Tesseract Secondary Fallback)")
    print(f"Output Writer Used:   ExcelWriterAgent (OpenPyXL Incremental Writer)")
    print("======================================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Unified Enterprise AI Invoice Processing Pipeline")
    parser.add_argument("--input", type=str, default="testing.xlsx", help="Path to input workbook or file")
    parser.add_argument("--output", type=str, default=None, help="Path to output extracted workbook")
    args = parser.parse_args()

    input_file = Path(args.input)
    if not input_file.exists():
        input_file = Path(f"input/{args.input}")

    if not input_file.exists():
        print(f"ERROR: {args.input} not found.")
        sys.exit(1)

    output_path_str = args.output or "output/output_extracted.xlsx"
    out_path_obj = Path(output_path_str)
    out_path_obj.parent.mkdir(parents=True, exist_ok=True)

    import backend.config as config
    print_audit_report(input_file, str(out_path_obj), getattr(config, "GEMINI_PRIMARY_MODEL", "gemini-3.1-flash-lite"))

    supervisor = SupervisorAgent()
    res = supervisor.execute_pipeline(str(input_file), output_path=str(out_path_obj))

    if not res.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()


