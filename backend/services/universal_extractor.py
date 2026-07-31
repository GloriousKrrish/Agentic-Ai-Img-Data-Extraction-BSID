import base64
import json
import requests
import backend.config as config
import time
from backend.services.data_sanitizer import sanitize_extracted_dict

def extract_universal_document(
    file_bytes: bytes, 
    schema_info: dict, 
    mime_type: str = "image/jpeg", 
    text_content: str = ""
) -> dict:
    """
    Extracts structured values from ANY document based on dynamic schema.
    Returns clean key-value pairs, confidence score, and status without discarding partial valid extractions.
    """
    api_key = config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
        
    category = schema_info.get("documentCategory", "General Document")
    fields = schema_info.get("fields", [])
    
    # Construct dynamic JSON Schema properties for Gemini structured output
    json_properties = {}
    required_keys = []
    field_descriptions = []
    
    for f in fields:
        key = f.get("key")
        label = f.get("label", key)
        desc = f.get("description", label)
        if key:
            json_properties[key] = {
                "type": "string",
                "description": f"{label}: {desc}. Return null or empty string if not found."
            }
            required_keys.append(key)
            field_descriptions.append(f"- {key} ({label}): {desc}")
            
    gemini_schema = {
        "type": "object",
        "properties": json_properties,
        "required": required_keys
    }
    
    prompt = f"""You are an Enterprise Expert Senior Business Data Analyst.
Analyzing a document classified as: "{category}".

Your mission is to extract EVERY SINGLE requested field from this invoice with 100% precision.

Requested Fields:
{chr(10).join(field_descriptions)}

Strict Field Guidelines:
- Customer Name: Look for buyer, customer, M/S, to, or person name at the top.
- Customer Mobile: Look for 10-digit mobile numbers (e.g. 9848022334, 9440121991).
- Vehicle Number: Look for Indian license plates (e.g. AP39NT1461, MH12AB1234, DL01A1234).
- Invoice Number & Date: Look for bill no, invoice no, cash memo no, and date.
- Dealer Details: Extract shop name, dealer GSTIN (15 characters), and shop address.
- Tyre Specs: Extract tyre size (e.g. 235/65R17, 205/65 R16), pattern name (e.g. Wanderer, B390, Sturdo), DOT code (e.g. DOT 4223), and serial numbers.
- Financial Summary: Extract item quantity, unit cost, discount, tax, and final grand total amount.

Inspect printed text, handwritten text, stamp seals, and line item tables very carefully.
If a field is missing on the physical invoice, return null. Do not hallucinate fake values.
"""

    parts = [{"text": prompt}]
    
    if text_content and len(text_content.strip()) > 20:
        parts.append({"text": f"\nDOCUMENT OCR TEXT CONTENT:\n{text_content[:4000]}"})
        
    if file_bytes and len(file_bytes) > 0:
        base64_data = base64.b64encode(file_bytes).decode('utf-8')
        actual_mime = mime_type if mime_type and mime_type != "application/octet-stream" else "image/jpeg"
        if "pdf" in actual_mime.lower():
            actual_mime = "application/pdf"
        parts.append({
            "inlineData": {
                "mimeType": actual_mime,
                "data": base64_data
            }
        })
        
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": gemini_schema,
            "temperature": 0.0
        }
    }
    
    last_error = None
    for model_name in config.MODELS_PRIORITY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=45)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data['candidates'][0]['content']['parts'][0]['text']
                    parsed_extracted = json.loads(raw_text)
                    
                    total_fields = len(required_keys) if required_keys else 1
                    filled_count = sum(1 for k in required_keys if str(parsed_extracted.get(k, '') or '').strip())
                    confidence = round((filled_count / float(total_fields)) * 100, 1) if total_fields > 0 else 90.0
                    
                    schema = [{"key": f.get("key"), "label": f.get("label", f.get("key"))} for f in fields if f.get("key")]
                    row_fields = {col["key"]: parsed_extracted.get(col["key"]) for col in schema}
                    
                    sanitized_row_fields = sanitize_extracted_dict(row_fields, min_confidence=0.0, record_confidence=confidence)
                    sanitized_extracted = sanitize_extracted_dict(parsed_extracted, min_confidence=0.0, record_confidence=confidence)
                    
                    return {
                        "modelUsed": model_name,
                        "documentCategory": category,
                        "category": category,
                        "documentTitle": schema_info.get("documentTitle", "Extracted Document"),
                        "schema": schema,
                        "rows": [
                            {
                                "rowIndex": 1,
                                "fields": sanitized_row_fields,
                                "status": "COMPLETED",
                                "confidence": max(confidence, 60.0)
                            }
                        ],
                        "extractedFields": sanitized_extracted,
                        "confidence": max(confidence, 60.0),
                        "status": "SUCCESS"
                    }
                elif res.status_code == 429:
                    last_error = f"Model {model_name}: HTTP 429 Quota Exceeded"
                    time.sleep(2.0 * (attempt + 1))
                else:
                    last_error = f"Model {model_name}: HTTP {res.status_code}"
                    time.sleep(1.0)
            except Exception as e:
                last_error = f"Model {model_name}: Exception - {str(e)}"
                time.sleep(1.0)
            
    # Fallback response
    schema = [{"key": f.get("key"), "label": f.get("label", f.get("key"))} for f in fields if f.get("key")]
    fallback_fields = {col["key"]: "" for col in schema}

    return {
        "modelUsed": "fallback-engine",
        "documentCategory": category,
        "category": category,
        "documentTitle": schema_info.get("documentTitle", "Extracted Document"),
        "schema": schema,
        "rows": [
            {
                "rowIndex": 1,
                "fields": fallback_fields,
                "status": "FAILED",
                "confidence": 0.0
            }
        ],
        "extractedFields": fallback_fields,
        "confidence": 0.0,
        "status": "FAILED",
        "notice": f"API error or limit reached. {last_error or ''}"
    }
