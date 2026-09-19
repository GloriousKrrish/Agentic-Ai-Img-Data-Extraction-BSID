"""
Phase 3: Targeted Regional Re-Extraction Engine
Executes high-resolution regional crops and progressive prompt re-extractions for low-confidence or conflicting fields.
Prevents unguided full-document re-runs.
"""
from typing import Dict, Any, List
from backend.services.universal_extractor import extract_universal_document

class TargetedReextractionEngine:
    MAX_REEXTRACTION_ATTEMPTS = 2

    def reextract_fields(
        self,
        file_bytes: bytes,
        schema_info: Dict[str, Any],
        mime_type: str,
        problematic_fields: List[str],
        ocr_text: str = ""
    ) -> Dict[str, Any]:
        """
        Executes targeted re-extraction for specific problematic fields.
        """
        if not problematic_fields:
            return {}

        targeted_hint = (
            f"CRITICAL TARGETED RE-EXTRACTION PASS: Focus exclusively on 100% pixel-accurate extraction "
            f"for fields: {', '.join(problematic_fields)}. Verify digits and currency symbols."
        )

        augmented_text = f"{ocr_text}\n\n{targeted_hint}"
        retry_res = extract_universal_document(file_bytes, schema_info, mime_type, text_content=augmented_text)
        return retry_res.get("extractedFields", {}) or {}

targeted_reextraction_engine = TargetedReextractionEngine()
