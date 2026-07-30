from backend.services.file_parser import parse_file_content
from backend.services.schema_generator import generate_dynamic_schema
from backend.services.universal_extractor import extract_universal_document

def extract_invoice_from_bytes(file_bytes: bytes, mime_type: str = "image/jpeg"):
    """
    Legacy wrapper redirected to Universal Dynamic Extraction Engine.
    Ensures 100% dynamic schema inference with zero hardcoded fields.
    """
    parsed = parse_file_content(file_bytes, "document", mime_type)
    schema_info = generate_dynamic_schema(file_bytes, mime_type, text_content=parsed.get("text_content", ""))
    return extract_universal_document(file_bytes, schema_info, mime_type, text_content=parsed.get("text_content", ""))
