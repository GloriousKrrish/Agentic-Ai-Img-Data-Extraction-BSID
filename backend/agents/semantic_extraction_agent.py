from backend.services.data_sanitizer import sanitize_extracted_dict

class SemanticExtractionAgent:
    """
    Step 8: Semantic Extraction Agent
    Zero hardcoded templates. Zero fixed coordinate assumptions.
    Extracts all meaningful semantic fields dynamically and returns any new fields discovered.
    """
    def extract_semantic_fields(self, vision_result: dict) -> dict:
        extracted_fields = vision_result.get("extractedFields", {})
        if not extracted_fields and vision_result.get("rows"):
            extracted_fields = vision_result["rows"][0].get("fields", {})
            
        record_confidence = vision_result.get("confidence", 95.0)
        return sanitize_extracted_dict(extracted_fields, min_confidence=70.0, record_confidence=record_confidence)
