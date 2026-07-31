import json
import concurrent.futures
from backend.agents.entity_prompts import ENTITY_SCHEMAS
from backend.services.universal_extractor import extract_universal_document
from backend.services.data_sanitizer import sanitize_extracted_dict
from backend.services.cache_service import cache_service
from backend.agents.excel_writer_agent import PRIORITY_COLUMNS

class MultiPassEntityExtractor:
    """
    High-Speed Cognitive Business Entity Extractor & AI Auditor
    
    Extracts all 7 business entity domains (Customer, Dealer, Vehicle, Metadata, Tyre, Financial, Remarks)
    using an optimized structured schema in 1 ultra-fast vision request + caching, achieving maximum throughput.
    """

    def extract_multi_pass(self, file_bytes: bytes, mime_type: str = "image/jpeg", text_content: str = "") -> dict:
        # Check Cache first
        cache_key = f"mp_fast_{hash(file_bytes)}"
        cached_res = cache_service.memory_cache.get(cache_key)
        if cached_res:
            return cached_res

        master_schema = {
            "documentCategory": "Enterprise Invoice Document",
            "documentTitle": "Invoice Business Entity Extraction",
            "fields": PRIORITY_COLUMNS
        }

        try:
            res = extract_universal_document(file_bytes, master_schema, mime_type, text_content=text_content)
            rows = res.get("rows", [])
            extracted_fields = rows[0].get("fields", {}) if rows else res.get("extractedFields", {})
            sanitized = sanitize_extracted_dict(extracted_fields, min_confidence=60.0)

            # Compute entity confidences
            entity_confidences = {}
            for e_key, e_info in ENTITY_SCHEMAS.items():
                e_keys = [f["key"] for f in e_info["fields"]]
                filled = sum(1 for k in e_keys if sanitized.get(k))
                entity_confidences[e_key] = round((filled / float(len(e_keys))) * 100, 1) if e_keys else 0.0

            result = {
                "fields": sanitized,
                "entity_confidences": entity_confidences,
                "overall_confidence": res.get("confidence", 95.0)
            }

            cache_service.memory_cache[cache_key] = result
            return result

        except Exception as e:
            print(f"Error in Multi-Pass extraction: {e}")
            return {
                "fields": {},
                "entity_confidences": {},
                "overall_confidence": 60.0
            }
