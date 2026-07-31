import base64
import json
import requests
import backend.config as config

SCHEMA_INFERENCE_PROMPT = """You are an Enterprise AI Document Intelligence Architect. 
Analyze the provided document (image, text, or file content) and automatically determine:
1. "documentCategory": The exact category of document (e.g. "Invoice", "Medical Report", "Employee Record", "Financial Statement", "Tax Form", "Academic Result", "Technical Spec", "Contract/Agreement", "Shipping Manifest", "General Document").
2. "documentTitle": A short human-readable title describing the document content.
3. "dynamicSchema": A list of extracted fields relevant to this SPECIFIC document. For each field, specify:
   - "key": CamelCase variable name (e.g., "patientName", "totalCost", "diagnosis", "employeeId")
   - "label": Clear display title (e.g., "Patient Name", "Total Cost", "Diagnosis")
   - "type": Data type ("string", "number", "date", "boolean", "array")
   - "description": Instructions on how to extract this field accurately.

Output MUST be strictly valid JSON matching this structure:
{
  "documentCategory": "Category Name",
  "documentTitle": "Document Title",
  "summary": "Brief 1-sentence overview",
  "fields": [
    {
      "key": "fieldKey",
      "label": "Field Display Label",
      "type": "string",
      "description": "Extraction guidelines for this field"
    }
  ]
}
"""

import time

def generate_dynamic_schema(file_bytes: bytes, mime_type: str = "image/jpeg", text_content: str = "") -> dict:
    """
    Uses Gemini Multimodal LLM to dynamically inspect any document and generate a bespoke JSON schema.
    Zero hardcoded domain assumptions.
    """
    api_key = config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
        
    parts = [{"text": SCHEMA_INFERENCE_PROMPT}]
    
    if text_content and len(text_content.strip()) > 20:
        parts.append({"text": f"\nDOCUMENT EXTRACTED TEXT:\n{text_content[:3000]}"})
    
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
            "temperature": 0.1
        }
    }
    
    last_error = None
    for model_name in config.MODELS_PRIORITY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        for attempt in range(2):
            try:
                res = requests.post(url, json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data['candidates'][0]['content']['parts'][0]['text']
                    parsed = json.loads(raw_text)
                    return parsed
                elif res.status_code == 429:
                    try:
                        err_body = res.json()
                        err_msg = err_body.get('error', {}).get('message', '')
                        last_error = f"Model {model_name}: QUOTA_EXCEEDED (429) - {err_msg[:200]}"
                    except Exception:
                        last_error = f"Model {model_name}: QUOTA_EXCEEDED (429) - Free tier quota exhausted"
                    if attempt == 0:
                        time.sleep(3.0)
                    break  # Move to next model on quota errors
                elif res.status_code in [400, 404]:
                    try:
                        err_body = res.json()
                        last_error = f"Model {model_name}: HTTP {res.status_code} - {err_body.get('error', {}).get('message', res.text)[:200]}"
                    except Exception:
                        last_error = f"Model {model_name}: HTTP {res.status_code} - {res.text[:200]}"
                    break
                else:
                    last_error = f"Model {model_name} HTTP {res.status_code}: {res.text[:200]}"
                    break
            except Exception as e:
                last_error = f"Model {model_name}: Exception - {str(e)}"
            
    # Universal fallback schema if offline or API limit reached
    return {
        "documentCategory": "General Document",
        "documentTitle": "Extracted Document Data",
        "summary": "Auto-extracted generic schema",
        "fields": [
            {"key": "title", "label": "Document Title", "type": "string", "description": "Title or main heading"},
            {"key": "date", "label": "Date", "type": "string", "description": "Primary date on document"},
            {"key": "referenceNumber", "label": "Reference ID", "type": "string", "description": "Reference code or ID"},
            {"key": "primaryEntity", "label": "Primary Name", "type": "string", "description": "Primary entity or subject name"},
            {"key": "amountOrValue", "label": "Total / Value", "type": "string", "description": "Numerical amount or value"},
            {"key": "notes", "label": "Notes & Details", "type": "string", "description": "Key notes or details"}
        ]
    }
