import json
import concurrent.futures
from backend.agents.entity_prompts import ENTITY_SCHEMAS, VERIFICATION_AUDIT_PROMPT
from backend.services.universal_extractor import extract_universal_document
from backend.services.data_sanitizer import sanitize_extracted_dict
from backend.services.cache_service import cache_service

class MultiPassEntityExtractor:
    """
    Multi-Pass Business Entity Extractor & AI Auditor
    
    1. Executes 7 focused AI passes targeting distinct business entities:
       (Customer, Dealer, Vehicle, Invoice Metadata, Tyre Info, Financial Summary, Remarks)
    2. Merges entity results into one unified record.
    3. Executes AI Verification Pass (Audit Pass) using Gemini to check for missed fields, mismappings, or math errors.
    4. Computes entity-level confidence scores.
    """

    def extract_single_entity_pass(self, entity_key: str, entity_info: dict, file_bytes: bytes, mime_type: str, text_content: str) -> tuple[str, dict]:
        schema = {
            "documentCategory": f"Invoice - {entity_info['domain']}",
            "documentTitle": entity_info["domain"],
            "fields": entity_info["fields"]
        }

        # Check Cache for this specific entity pass
        cache_key = f"mp_{entity_key}_{hash(file_bytes)}"
        if cache_service.memory_cache.get(cache_key):
            return entity_key, cache_service.memory_cache[cache_key]

        try:
            res = extract_universal_document(file_bytes, schema, mime_type, text_content=text_content)
            rows = res.get("rows", [])
            extracted_fields = rows[0].get("fields", {}) if rows else res.get("extractedFields", {})
            sanitized = sanitize_extracted_dict(extracted_fields, min_confidence=60.0)
            cache_service.memory_cache[cache_key] = sanitized
            return entity_key, sanitized
        except Exception as e:
            print(f"Error in Multi-Pass {entity_key}: {e}")
            return entity_key, {}

    def extract_multi_pass(self, file_bytes: bytes, mime_type: str = "image/jpeg", text_content: str = "") -> dict:
        merged_record = {}
        entity_confidences = {}

        # 1. Parallel Execution of 7 Focused Business Entity Passes
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            futures = [
                executor.submit(self.extract_single_entity_pass, e_key, e_info, file_bytes, mime_type, text_content)
                for e_key, e_info in ENTITY_SCHEMAS.items()
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    e_key, fields = future.result()
                    for k, v in fields.items():
                        if v:
                            merged_record[k] = v
                    # Track fill rate per entity
                    filled_count = sum(1 for v in fields.values() if v)
                    entity_confidences[e_key] = round((filled_count / float(len(fields))) * 100, 1) if fields else 0.0
                except Exception as ex:
                    print(f"Multi-Pass worker exception: {ex}")

        # 2. AI Verification Pass (Auditor Pass)
        audited_record = self.execute_verification_audit(file_bytes, mime_type, merged_record, text_content)

        return {
            "fields": audited_record,
            "entity_confidences": entity_confidences,
            "overall_confidence": 95.0 if audited_record else 60.0
        }

    def execute_verification_audit(self, file_bytes: bytes, mime_type: str, merged_record: dict, text_content: str) -> dict:
        """AI Verification Pass: Audits merged extraction results against original document context."""
        audit_schema = {
            "documentCategory": "Invoice Audit Verification",
            "documentTitle": "Audited Invoice Record",
            "fields": [
                {"key": k, "label": k, "description": f"Audited value for {k}"}
                for k in merged_record.keys()
            ] if merged_record else [
                {"key": "customerName", "label": "Customer Name"},
                {"key": "customerMobile", "label": "Customer Mobile"},
                {"key": "vehicleNumber", "label": "Vehicle Number"},
                {"key": "invoiceNumber", "label": "Invoice Number"},
                {"key": "dealerName", "label": "Dealer Name"},
                {"key": "grandTotal", "label": "Grand Total"}
            ]
        }

        try:
            res = extract_universal_document(
                file_bytes, 
                audit_schema, 
                mime_type, 
                text_content=f"{text_content}\n\nEXISTING EXTRACTION FOR VERIFICATION:\n{json.dumps(merged_record, indent=2)}"
            )
            rows = res.get("rows", [])
            audited_fields = rows[0].get("fields", {}) if rows else res.get("extractedFields", {})
            
            # Merge back audited values
            final_record = dict(merged_record)
            for k, v in audited_fields.items():
                if v and str(v).strip():
                    final_record[k] = str(v).strip()

            return sanitize_extracted_dict(final_record, min_confidence=60.0)
        except Exception:
            return merged_record
