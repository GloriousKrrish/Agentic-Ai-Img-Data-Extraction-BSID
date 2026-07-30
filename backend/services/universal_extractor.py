import base64
import json
import requests
import backend.config as config

import time

def extract_universal_document(
    file_bytes: bytes, 
    schema_info: dict, 
    mime_type: str = "image/jpeg", 
    text_content: str = ""
) -> dict:
    """
    Extracts structured values from ANY document based on the dynamically generated schema.
    Returns dynamic key-value pairs, confidence score, and status.
    """
    api_key = config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
        
    category = schema_info.get("documentCategory", "General Document")
    fields = schema_info.get("fields", [])
    
    # Construct dynamic Pydantic/JSON Schema properties for Gemini structured output
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
    
    prompt = f"""You are a high-precision Universal AI Data Extraction System.
Analyzing a document classified as: "{category}".

Extract the following dynamically requested fields:
{chr(10).join(field_descriptions)}

Extraction Guidelines:
- Inspect printed text, handwritten text, signatures, seals, and tabular data carefully.
- Return clean, exact values. If a field is not present in the document, return null.
- Do not hallucinate or guess missing information.
"""

    parts = [{"text": prompt}]
    
    if text_content and len(text_content.strip()) > 20:
        parts.append({"text": f"\nDOCUMENT TEXT CONTENT:\n{text_content[:4000]}"})
        
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
            "temperature": 0.1
        }
    }
    
    last_error = None
    for model_name in config.MODELS_PRIORITY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        for attempt in range(2):
            try:
                res = requests.post(url, json=payload, timeout=45)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data['candidates'][0]['content']['parts'][0]['text']
                    parsed_extracted = json.loads(raw_text)
                    
                    # Compute dynamic confidence score based on non-null field fill rate
                    total_fields = len(required_keys) if required_keys else 1
                    filled_count = sum(1 for k in required_keys if str(parsed_extracted.get(k, '') or '').strip())
                    confidence = round((filled_count / float(total_fields)) * 100, 1) if total_fields > 0 else 90.0
                    
                    schema = [{"key": f.get("key"), "label": f.get("label", f.get("key"))} for f in fields if f.get("key")]
                    row_fields = {col["key"]: str(parsed_extracted.get(col["key"]) or "").strip() for col in schema}
                    
                    return {
                        "modelUsed": model_name,
                        "documentCategory": category,
                        "category": category,
                        "documentTitle": schema_info.get("documentTitle", "Extracted Document"),
                        "schema": schema,
                        "rows": [
                            {
                                "rowIndex": 1,
                                "fields": row_fields,
                                "status": "COMPLETED",
                                "confidence": max(confidence, 75.0)
                            }
                        ],
                        "extractedFields": parsed_extracted,
                        "confidence": max(confidence, 75.0),
                        "status": "SUCCESS"
                    }
                elif res.status_code == 429:
                    # Parse retry-after time from error message if available
                    try:
                        err_body = res.json()
                        err_msg = err_body.get('error', {}).get('message', '')
                        last_error = f"Model {model_name}: QUOTA_EXCEEDED (429) - {err_msg[:200]}"
                    except Exception:
                        last_error = f"Model {model_name}: QUOTA_EXCEEDED (429) - Free tier quota exhausted"
                    # Only wait on first attempt; skip on second to move to next model faster
                    if attempt == 0:
                        time.sleep(3.0)
                    break  # Don't retry same model on quota errors, move to next
                elif res.status_code == 400:
                    try:
                        err_body = res.json()
                        last_error = f"Model {model_name}: BAD_REQUEST (400) - {err_body.get('error', {}).get('message', res.text)[:200]}"
                    except Exception:
                        last_error = f"Model {model_name}: BAD_REQUEST (400) - {res.text[:200]}"
                    break
                else:
                    last_error = f"Model {model_name} HTTP {res.status_code}: {res.text[:200]}"
                    break
            except Exception as e:
                last_error = f"Model {model_name}: Exception - {str(e)}"
            
    raise RuntimeError(f"All Gemini models failed extraction. Last error: {last_error}")
