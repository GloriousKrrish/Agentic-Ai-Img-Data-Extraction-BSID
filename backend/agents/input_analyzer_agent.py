"""
Phase 1: Universal Input Analyzer Agent
Inspects incoming binary content, text streams, image dimensions, tables, and document markers
to construct a rich InputAnalysis object for the Agentic Planner.
"""
import io
import re
from pathlib import Path
from PIL import Image
import pypdf
from backend.agents.agentic_models import InputAnalysis
from backend.services.file_parser import parse_file_content

class InputAnalyzerAgent:
    def analyze(self, file_bytes: bytes, filename: str, mime_type: str = "") -> InputAnalysis:
        ext = Path(filename).suffix.lower().replace(".", "") or "bin"
        size = len(file_bytes)
        parsed = parse_file_content(file_bytes, filename, mime_type)
        
        file_type = parsed.get("file_type", ext)
        text_content = parsed.get("text_content", "")
        page_count = parsed.get("page_count", 1)
        has_vision = parsed.get("has_vision", False)
        
        is_scanned = False
        contains_tables = False
        contains_images = has_vision
        contains_text = bool(text_content and len(text_content.strip()) > 10)
        
        # Analyze Scanned PDF vs Text PDF
        if file_type == "pdf":
            if page_count > 0 and len(text_content.strip()) < (50 * page_count):
                is_scanned = True
        elif file_type == "image":
            is_scanned = True
            
        # Analyze Tabular Content
        if file_type in ["xlsx", "csv", "json"]:
            contains_tables = True
        elif text_content:
            # Check for table indicators (column separators like |, tabs, multiple numbers per line)
            table_lines = sum(1 for line in text_content.splitlines() if line.count('|') >= 2 or line.count('\t') >= 2 or len(re.findall(r'\b\d+[\.,]?\d*\b', line)) >= 3)
            if table_lines >= 3:
                contains_tables = True

        # Document Category / Domain Classification Heuristics
        lower_text = text_content.lower() + " " + filename.lower()
        doc_type = "general"
        doc_domain = "general"
        
        if any(w in lower_text for w in ["invoice", "bill", "tax invoice", "cash memo", "receipt", "gstin", "total amount"]):
            doc_type = "invoice"
            doc_domain = "finance"
        elif any(w in lower_text for w in ["patient", "doctor", "lab", "diagnosis", "hospital", "prescription", "blood", "report"]):
            doc_type = "medical_report"
            doc_domain = "healthcare"
        elif any(w in lower_text for w in ["aadhaar", "passport", "dob", "license", "voter", "identity card", "kyc"]):
            doc_type = "kyc_document"
            doc_domain = "identity"
        elif any(w in lower_text for w in ["student", "marks", "gpa", "university", "school", "semester", "grade"]):
            doc_type = "academic_result"
            doc_domain = "education"
        elif any(w in lower_text for w in ["agreement", "contract", "jurisdiction", "clause", "party a", "party b"]):
            doc_type = "legal_contract"
            doc_domain = "legal"
        elif any(w in lower_text for w in ["balance sheet", "revenue", "fiscal", "profit", "assets", "liabilities"]):
            doc_type = "financial_statement"
            doc_domain = "finance"
        elif file_type in ["csv", "xlsx", "zip"]:
            doc_type = "dataset_batch"
            doc_domain = "data"

        # Complexity & Strategy Requirements
        complexity = "medium"
        if size > 5_000_000 or page_count > 10 or (contains_tables and is_scanned):
            complexity = "high"
        elif size < 200_000 and page_count == 1 and not is_scanned:
            complexity = "low"

        requires_ocr = is_scanned or (contains_images and not contains_text)
        requires_vision = contains_images or is_scanned or file_type in ["image", "pdf"]
        requires_chunking = page_count > 5 or len(text_content) > 15_000
        requires_table_extraction = contains_tables

        difficulty = 0.3 if complexity == "low" else 0.6 if complexity == "medium" else 0.85

        return InputAnalysis(
            input_type=file_type,
            mime_type=mime_type or "application/octet-stream",
            file_size=size,
            page_count=page_count,
            is_scanned=is_scanned,
            contains_tables=contains_tables,
            contains_images=contains_images,
            contains_text=contains_text,
            language="en",
            document_type=doc_type,
            document_domain=doc_domain,
            complexity=complexity,
            requires_ocr=requires_ocr,
            requires_vision=requires_vision,
            requires_chunking=requires_chunking,
            requires_table_extraction=requires_table_extraction,
            estimated_extraction_difficulty=difficulty
        )

input_analyzer_agent = InputAnalyzerAgent()
