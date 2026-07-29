import base64
import json
import re
import requests
from backend.config import GEMINI_API_KEY, MODELS_PRIORITY

def clean_mobile(val: str) -> str:
    if not val:
        return ""
    cleaned = re.sub(r'[^\d]', '', str(val).strip())
    if len(cleaned) == 12 and cleaned.startswith("91"):
        cleaned = cleaned[2:]
    if len(cleaned) == 11 and cleaned.startswith("0"):
        cleaned = cleaned[1:]
    if re.match(r'^[6-9]\d{9}$', cleaned):
        return cleaned
    return ""

def clean_vehicle(val: str) -> str:
    if not val:
        return ""
    return re.sub(r'[^a-zA-Z0-9]', '', str(val).strip()).upper()

def clean_cost(val: str) -> str:
    if not val:
        return ""
    match = re.search(r'(\d+[\d,]*(\.\d+)?)', str(val).strip())
    if match:
        return match.group(1).replace(',', '')
    return ""

SCHEMA = {
    "type": "object",
    "properties": {
        "CustomerName": {"type": "string", "description": "Customer Name. Return null if missing."},
        "CustomerMobile": {"type": "string", "description": "10-digit customer mobile number starting with 6-9. Return null if missing."},
        "VehicleNumber": {"type": "string", "description": "Alphanumeric vehicle license plate format. Return null if missing."},
        "Size": {"type": "string", "description": "Automotive tire size format e.g. 205/55R16. Return null if missing."},
        "Pattern": {"type": "string", "description": "Tire model/tread design name string, e.g. STURDO. Return null if missing."},
        "DOT": {"type": "string", "description": "Tire manufacturing code starting with 'DOT'. Return null if missing."},
        "Cost": {"type": "string", "description": "Individual unit price of a single tire. Return null if missing."},
        "TotalCost": {"type": "string", "description": "Final invoice grand total price. Return null if missing."},
        "DealerName": {"type": "string", "description": "The business banner name of the tire dealer. Return null if missing."}
    },
    "required": ["CustomerName", "CustomerMobile", "VehicleNumber", "Size", "Pattern", "DOT", "Cost", "TotalCost", "DealerName"]
}

PROMPT = """You are a high-precision extraction system for Bridgestone. Analyze the invoice image and extract the following fields.
Check printed and handwritten text carefully.

1. CustomerName: Customer name. Strip vehicle numbers if written inside.
2. CustomerMobile: 10-digit mobile number starting with 6-9.
3. VehicleNumber: Vehicle license plate format (e.g. KA03ME4662, AP05EY5775).
4. Size: Tire size format (e.g. 205/65R16).
5. Pattern: Tire pattern name (e.g. STURDO, B390, DUELER). Do not write BRIDGESTONE as pattern.
6. DOT: Tire serial code starting with DOT.
7. Cost: Single tire unit price before tax.
8. TotalCost: Grand total net amount after tax.
9. DealerName: Business banner name at top of invoice.
"""

def extract_invoice_from_bytes(file_bytes: bytes, mime_type: str = "image/jpeg"):
    base64_data = base64.b64encode(file_bytes).decode('utf-8')
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": PROMPT},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA
        }
    }
    
    api_key = GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in backend environment.")
        
    last_error = None
    
    for model_name in MODELS_PRIORITY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            res = requests.post(url, json=payload, timeout=45)
            if res.status_code == 200:
                data = res.json()
                raw_text = data['candidates'][0]['content']['parts'][0]['text']
                parsed = json.loads(raw_text)
                
                c_name = parsed.get("CustomerName") or ""
                c_mob = clean_mobile(parsed.get("CustomerMobile") or "")
                veh = clean_vehicle(parsed.get("VehicleNumber") or "")
                size = parsed.get("Size") or ""
                pattern = parsed.get("Pattern") or ""
                dot = parsed.get("DOT") or ""
                if dot and not dot.startswith("DOT"):
                    dot = f"DOT {dot}"
                cost = clean_cost(parsed.get("Cost") or "")
                total_cost = clean_cost(parsed.get("TotalCost") or "")
                dealer = parsed.get("DealerName") or ""
                
                # Confidence calculation
                filled = sum(1 for x in [c_name, c_mob, veh, size, pattern, dot, cost, total_cost, dealer] if str(x).strip())
                confidence = round((filled / 9.0) * 100, 1)
                
                return {
                    "modelUsed": model_name,
                    "customerName": c_name,
                    "customerMobile": c_mob,
                    "vehicleNumber": veh,
                    "size": size,
                    "pattern": pattern,
                    "dot": dot,
                    "cost": cost,
                    "totalCost": total_cost,
                    "dealerName": dealer,
                    "confidence": confidence,
                    "status": "SUCCESS"
                }
            else:
                last_error = f"Model {model_name} HTTP {res.status_code}: {res.text}"
        except Exception as e:
            last_error = str(e)
            
    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")
