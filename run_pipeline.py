import os
import sys
import argparse
from pathlib import Path
from backend.agents.supervisor import SupervisorAgent

def main():
    parser = argparse.ArgumentParser(
        description="Enterprise Agentic AI Excel -> Document -> Data Extraction Engine"
    )
    parser.add_argument("--input", default="testing.xlsx", help="Path to input Excel workbook, CSV, or Image/PDF file")
    parser.add_argument("--output", default="output_extracted.xlsx", help="Path to output Excel workbook")
    parser.add_argument("--workers", type=int, default=3, help="Number of parallel worker threads")
    args = parser.parse_args()

    input_path = args.input.strip()
    output_path = args.output.strip()

    # Default fallback: if 'testing.xlsx' is default but doesn't exist, search for any .xlsx in current directory
    if input_path == "testing.xlsx" and not Path("testing.xlsx").exists():
        excel_files = [p for p in Path(".").glob("*.xlsx") if not p.name.startswith("output_") and not p.name.startswith("failed_")]
        if excel_files:
            input_path = excel_files[0].name
            print(f"[*] Default input 'testing.xlsx' not found. Auto-detected workbook: '{input_path}'")

    supervisor = SupervisorAgent(max_workers=args.workers)
    res = supervisor.execute_pipeline(input_path, output_path)

    if not res.get("success"):
        sys.exit(1)

if __name__ == "__main__":
    main()
