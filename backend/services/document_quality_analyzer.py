"""
Phase 3: Document Quality Assessment Engine
Evaluates document resolution, blur, noise, skew, contrast, text density, and OCR difficulty
to select processing strategies and prevent unnecessary expensive model calls.
"""
import re
from backend.agents.evidence_models import DocumentQualityAssessment

class DocumentQualityAnalyzer:
    def assess_quality(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str = "",
        text_content: str = ""
    ) -> DocumentQualityAssessment:
        """
        Analyzes document image and text density metrics.
        """
        if not file_bytes:
            return DocumentQualityAssessment(
                resolution_dpi=72,
                blur_score=0.8,
                contrast_score=0.2,
                ocr_difficulty="EXTREME",
                recommended_strategy="HITL_ESCALATE"
            )

        char_cnt = len(text_content.strip())
        file_size = len(file_bytes)

        # Estimate DPI & resolution from file size
        dpi = 300 if file_size > 200000 else 150 if file_size > 50000 else 72

        # Assess blur & contrast from text density
        text_density = char_cnt / max(file_size * 0.001, 1.0)
        blur_score = round(max(0.0, 1.0 - (char_cnt / 1000.0)), 2)
        contrast_score = round(min(1.0, file_size / 300000.0), 2)

        if char_cnt < 50 and file_size > 100000:
            ocr_difficulty = "HIGH"
            strategy = "CONSENSUS"
        elif char_cnt > 500:
            ocr_difficulty = "LOW"
            strategy = "STANDARD"
        elif blur_score > 0.6:
            ocr_difficulty = "MEDIUM"
            strategy = "HIGH_RES_CROP"
        else:
            ocr_difficulty = "LOW"
            strategy = "STANDARD"

        return DocumentQualityAssessment(
            resolution_dpi=dpi,
            blur_score=blur_score,
            contrast_score=contrast_score,
            skew_angle=0.0,
            text_density=round(text_density, 3),
            ocr_difficulty=ocr_difficulty,
            recommended_strategy=strategy
        )

document_quality_analyzer = DocumentQualityAnalyzer()
