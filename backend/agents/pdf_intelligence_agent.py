"""
Phase 1: PDF Intelligence Agent
Performs deterministic PDF inspection using PyMuPDF (fitz) or pypdf fallback.
Classifies each page (TEXT, SCANNED, MIXED, TABLE_HEAVY, BLANK) and renders high-res page JPEGs.
"""
import io
import re
from typing import Dict, Any, List, Optional
from PIL import Image

try:
    import pymupdf as fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    try:
        import fitz
        HAS_FITZ = True
    except ImportError:
        HAS_FITZ = False


import pypdf
from backend.agents.pdf_models import (
    PageClassification, PDFDocumentAnalysis
)

class PDFIntelligenceAgent:
    def analyze_pdf(self, pdf_bytes: bytes) -> PDFDocumentAnalysis:
        if not pdf_bytes:
            return PDFDocumentAnalysis(total_pages=0, estimated_complexity="low")

        if HAS_FITZ:
            return self._analyze_with_fitz(pdf_bytes)
        else:
            return self._analyze_with_pypdf(pdf_bytes)

    def _analyze_with_fitz(self, pdf_bytes: bytes) -> PDFDocumentAnalysis:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(doc)
        except Exception as err:
            print(f"PDF Intelligence: Could not parse PDF stream ({err}). Returning fallback analysis.")
            return PDFDocumentAnalysis(total_pages=0, estimated_complexity="low")

        classifications: List[PageClassification] = []


        scanned_cnt = 0
        text_cnt = 0
        table_cnt = 0

        for i in range(total_pages):
            page = doc[i]
            text = page.get_text("text") or ""
            char_cnt = len(text.strip())
            images = page.get_images()
            img_cnt = len(images)
            rect = page.rect
            area = max(rect.width * rect.height, 1.0)
            text_density = char_cnt / area

            is_scanned = (char_cnt < 50 and img_cnt >= 1) or (text_density < 0.0001 and img_cnt >= 1)
            is_blank = char_cnt < 10 and img_cnt == 0

            # Table detection heuristic
            contains_table = False
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            num_pattern_lines = sum(1 for l in lines if l.count('|') >= 2 or l.count('\t') >= 2 or len(re.findall(r'\b\d+[\.,]?\d*\b', l)) >= 3)
            if num_pattern_lines >= 3:
                contains_table = True

            # Page classification type
            if is_blank:
                page_type = "BLANK"
            elif is_scanned:
                page_type = "SCANNED"
                scanned_cnt += 1
            elif contains_table:
                page_type = "TABLE_HEAVY"
                table_cnt += 1
                text_cnt += 1
            elif img_cnt > 2:
                page_type = "IMAGE_HEAVY"
                text_cnt += 1
            elif char_cnt > 200:
                page_type = "TEXT"
                text_cnt += 1
            else:
                page_type = "MIXED"
                text_cnt += 1

            if contains_table:
                table_cnt += 1

            classifications.append(PageClassification(
                page_number=i + 1,
                type=page_type,
                text_density=round(text_density, 5),
                image_density=min(round(img_cnt * 0.1, 2), 1.0),
                char_count=char_cnt,
                image_count=img_cnt,
                requires_ocr=is_scanned or page_type in ["SCANNED", "IMAGE_HEAVY"],
                requires_vision=is_scanned or page_type in ["SCANNED", "IMAGE_HEAVY", "TABLE_HEAVY"],
                contains_table=contains_table,
                rotation=page.rotation,
                width=rect.width,
                height=rect.height
            ))

        doc.close()

        is_scanned_pdf = scanned_cnt > (total_pages * 0.5)
        is_mixed_pdf = (scanned_cnt > 0) and (text_cnt > 0)

        # Adaptive chunk size calculation
        chunk_size = 5
        if total_pages > 50:
            chunk_size = 10
        elif total_pages > 20:
            chunk_size = 8
        elif total_pages <= 5:
            chunk_size = total_pages

        complexity = "high" if (total_pages > 15 or scanned_cnt > 3 or table_cnt > 5) else "low" if total_pages <= 2 else "medium"

        return PDFDocumentAnalysis(
            total_pages=total_pages,
            scanned_page_count=scanned_cnt,
            text_page_count=text_cnt,
            table_page_count=table_cnt,
            is_scanned_pdf=is_scanned_pdf,
            is_mixed_pdf=is_mixed_pdf,
            recommended_chunk_size=chunk_size,
            estimated_complexity=complexity,
            page_classifications=classifications
        )

    def _analyze_with_pypdf(self, pdf_bytes: bytes) -> PDFDocumentAnalysis:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        classifications: List[PageClassification] = []

        scanned_cnt = 0
        text_cnt = 0

        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            char_cnt = len(txt.strip())
            is_scanned = char_cnt < 50
            if is_scanned:
                scanned_cnt += 1
                page_type = "SCANNED"
            else:
                text_cnt += 1
                page_type = "TEXT"

            classifications.append(PageClassification(
                page_number=i + 1,
                type=page_type,
                char_count=char_cnt,
                requires_ocr=is_scanned,
                requires_vision=True
            ))

        return PDFDocumentAnalysis(
            total_pages=total_pages,
            scanned_page_count=scanned_cnt,
            text_page_count=text_cnt,
            is_scanned_pdf=scanned_cnt > (total_pages * 0.5),
            is_mixed_pdf=(scanned_cnt > 0) and (text_cnt > 0),
            page_classifications=classifications
        )

    def render_page_to_jpeg(self, pdf_bytes: bytes, page_number: int, dpi: int = 300) -> bytes:
        """
        Renders a specific 1-indexed PDF page to a high-resolution JPEG byte stream.
        """
        if not HAS_FITZ:
            return b""

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if page_number < 1 or page_number > len(doc):
                doc.close()
                return b""

            page = doc[page_number - 1]
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("jpeg")
            doc.close()
            return img_bytes
        except Exception:
            return b""

pdf_intelligence_agent = PDFIntelligenceAgent()
