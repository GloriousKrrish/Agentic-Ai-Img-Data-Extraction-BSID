import re
import datetime

INVALID_STRINGS = {
    "null", "none", "n/a", "na", "undefined", "{}", "[]", "nullnull", 
    "[object object]", "unknown", "missing", "nan", "nil", "none/none"
}

def clean_field_value(val) -> str:
    """
    Cleans raw extracted field value:
    - Removes 'null', 'None', 'N/A', 'undefined', etc.
    - Strips OCR garbage characters, non-printable characters, and excessive whitespace.
    - Returns empty string '' if invalid or unparseable noise.
    """
    if val is None:
        return ""
    
    val_str = str(val).strip()
    if not val_str:
        return ""
        
    lower_val = val_str.lower()
    if lower_val in INVALID_STRINGS:
        return ""
        
    # Strip leading/trailing quotes, backticks, braces, brackets
    val_str = re.sub(r'^[\'"`\{\}\[\]]+|[\'"`\{\}\[\]]+$', '', val_str).strip()
    
    if val_str.lower() in INVALID_STRINGS:
        return ""
        
    # Remove OCR garbage / non-printable control characters
    val_str = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', val_str)
    
    # Check if value consists purely of OCR symbol noise
    if re.match(r'^[~\$\*_\-\|\+\=\#\@\!\?\:\;\,\. ]+$', val_str):
        return ""
        
    return val_str

def normalize_mobile(val_str: str) -> str:
    """Normalizes phone/mobile to standard 10-digit mobile number starting with 6-9."""
    if not val_str:
        return ""
    digits = re.sub(r'[^\d]', '', val_str)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
        
    if len(digits) == 10 and re.match(r'^[6-9]\d{9}$', digits):
        return digits
    return ""

def normalize_amount(val_str: str) -> str:
    """Normalizes currency / total cost / amount values to clean numeric string."""
    if not val_str:
        return ""
    match = re.search(r'(\d+[\d,]*(\.\d+)?)', val_str)
    if match:
        clean_num = match.group(1).replace(',', '')
        try:
            num_float = float(clean_num)
            return f"{num_float:.2f}" if '.' in clean_num else str(int(num_float)) if num_float.is_integer() else str(num_float)
        except ValueError:
            return ""
    return ""

def normalize_vehicle_number(val_str: str) -> str:
    """Normalizes vehicle registration numbers to standard uppercase alphanumeric."""
    if not val_str:
        return ""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', val_str).upper()
    if len(cleaned) >= 5:
        return cleaned
    return ""

def normalize_gst(val_str: str) -> str:
    """Normalizes GSTIN to standard 15-character uppercase alphanumeric format."""
    if not val_str:
        return ""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', val_str).upper()
    if len(cleaned) == 15 and re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', cleaned):
        return cleaned
    elif len(cleaned) == 15:
        return cleaned
    return ""

def normalize_field(key: str, val) -> str:
    """
    Applies field-specific semantic normalization rules based on field key names.
    """
    cleaned = clean_field_value(val)
    if not cleaned:
        return ""
        
    key_lower = key.lower()
    
    # Phone / Mobile
    if any(k in key_lower for k in ["mobile", "phone", "contact", "cell"]):
        return normalize_mobile(cleaned)
        
    # Amount / Cost / Price / Total / Tax / Discount
    if any(k in key_lower for k in ["unitcost", "discount", "tax", "grandtotal", "cost", "price", "total", "amount"]):
        norm_amt = normalize_amount(cleaned)
        return norm_amt if norm_amt else cleaned

    # Quantity
    if "quantity" in key_lower or "qty" in key_lower:
        match = re.search(r'\d+', cleaned)
        return match.group(0) if match else cleaned

    # GST Number
    if "gst" in key_lower:
        return normalize_gst(cleaned)
        
    # Vehicle Registration Number
    if "vehicle" in key_lower and ("number" in key_lower or "no" in key_lower or "plate" in key_lower or "reg" in key_lower):
        norm_v = normalize_vehicle_number(cleaned)
        return norm_v if norm_v else cleaned
        
    # DOT Code
    if key_lower in ["dot", "dotcode"]:
        cleaned_up = cleaned.upper().strip()
        if not cleaned_up.startswith("DOT"):
            return f"DOT {cleaned_up}"
        return cleaned_up
        
    # Clean text whitespace
    return re.sub(r'\s+', ' ', cleaned).strip()

def sanitize_extracted_dict(fields_dict: dict, min_confidence: float = 0.0, record_confidence: float = 95.0) -> dict:
    """
    Sanitizes an entire record dictionary:
    - Filters out 'null', 'None', 'N/A', OCR garbage.
    - Normalizes mobile, dates, amounts, vehicle numbers, GST.
    - NEVER discards valid non-empty fields!
    """
    if not fields_dict:
        return {}
        
    sanitized = {}
    for key, val in fields_dict.items():
        norm_val = normalize_field(key, val)
        if norm_val:
            sanitized[key] = norm_val
        
    return sanitized
