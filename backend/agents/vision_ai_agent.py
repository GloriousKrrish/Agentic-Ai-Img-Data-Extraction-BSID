from backend.services.universal_extractor import extract_universal_document

class VisionAIAgent:
    """
    Step 7: Vision AI Agent (Gemini)
    Uses Google Gemini Vision AI API to analyze:
    - Layout & document structure
    - Tables & line items
    - Printed & handwritten text
    - Logos, seals & signatures
    """
    def extract_with_vision(self, file_bytes: bytes, schema_info: dict, mime_type: str = "image/jpeg", text_content: str = "") -> dict:
        return extract_universal_document(file_bytes, schema_info, mime_type, text_content=text_content)
