import re

class BusinessEntityResolverAgent:
    """
    Business Entity Resolver Agent (The Cognitive Brain)
    
    Responsibilities:
    1. Document Understanding: Classifies document into 8 exact types:
       (Tax Invoice, Invoice, Retail Invoice, Purchase Order, Receipt, Medical Bill, Warranty, Unknown)
    2. Document Layout Section Mapping: (Seller, Buyer, Vehicle, Tyres, Products, Financial Summary, Tax Section, Payment Section, Remarks)
    3. Business Entity Resolution & Disambiguation:
       Receives raw OCR text AND Gemini Vision AI outputs.
       Uses document context, labels, spatial positioning, surrounding words, and domain knowledge 
       to determine WHAT every extracted value actually represents.
       e.g., Disambiguates a 10-digit number like "9440121991" between:
       - Phone / Mobile Number
       - Invoice Number
       - GSTIN component
       - Vehicle Registration component
       - PIN code / Postal code
       - Product Serial Number
    """

    DOCUMENT_TYPES = [
        "Tax Invoice", "Invoice", "Retail Invoice", "Purchase Order", 
        "Receipt", "Medical Bill", "Warranty", "Unknown"
    ]

    INDIAN_VEHICLE_PATTERNS = [
        r'\b[A-Z]{2}\s*[0-9]{1,2}\s*[A-Z]{1,3}\s*[0-9]{4}\b',  # e.g. AP 39 NT 1461, MH 12 AB 1234
        r'\b[A-Z]{2}\s*[0-9]{1,2}\s*[0-9]{4}\b'                # e.g. DL 01 1234
    ]

    TYRE_SIZE_PATTERNS = [
        r'\b\d{3}/\d{2}\s*R?\s*\d{2}\b',       # e.g. 235/65R17, 185/65 R15
        r'\b\d{3}-\d{2}-?\d{2}\b',             # e.g. 235-65-17
        r'\b\d{2,3}/\d{2,3}\s*D?\s*\d{2}\b'     # e.g. 10.00/20, 145/80 R12
    ]

    DOT_PATTERNS = [
        r'\bDOT\s*[:#-]?\s*([A-Z0-9]{4,12})\b',
        r'\b[0-9]{4}\b' # 4 digit DOT date code like 4223
    ]

    GST_PATTERN = r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b'
    MOBILE_PATTERN = r'\b[6-9]\d{9}\b'

    def classify_document(self, text_content: str, vision_data: dict = None) -> str:
        """Pass 1: Document Understanding & Document Type Classification"""
        text_lower = (text_content or "").lower()
        if vision_data:
            v_text = str(vision_data).lower()
            text_lower += " " + v_text

        if "tax invoice" in text_lower:
            return "Tax Invoice"
        elif "retail invoice" in text_lower or "cash invoice" in text_lower:
            return "Retail Invoice"
        elif "purchase order" in text_lower or "p.o." in text_lower:
            return "Purchase Order"
        elif any(k in text_lower for k in ["receipt", "payment voucher", "cash memo"]):
            return "Receipt"
        elif any(k in text_lower for k in ["patient", "doctor", "hospital", "medical"]):
            return "Medical Bill"
        elif any(k in text_lower for k in ["warranty", "guarantee card"]):
            return "Warranty"
        elif "invoice" in text_lower or "bill" in text_lower:
            return "Invoice"
        
        return "Unknown"

    def resolve_entities(self, raw_ocr_text: str, vision_fields: dict) -> dict:
        """
        Pass 3: Business Entity Resolution & Disambiguation
        Analyzes raw vision output against OCR text and surrounding labels.
        Refines entity mapping based on business rules.
        """
        ocr_text = raw_ocr_text or ""
        resolved = dict(vision_fields) if vision_fields else {}

        # 1. Mobile Number Disambiguation
        raw_mobile = str(resolved.get("customerMobile", "") or resolved.get("phone", "") or "")
        mobile_match = re.search(self.MOBILE_PATTERN, raw_mobile)
        
        if not mobile_match and ocr_text:
            # Look for phone/mobile label in OCR text
            phone_label_match = re.search(r'(?:mobile|phone|ph|contact|cell|m/s|call)\s*[:#-]?\s*([6-9]\d{9})', ocr_text, re.IGNORECASE)
            if phone_label_match:
                resolved["customerMobile"] = phone_label_match.group(1)
            else:
                # Disambiguate standalone 10-digit numbers in OCR text
                all_mobiles = re.findall(self.MOBILE_PATTERN, ocr_text)
                for m in all_mobiles:
                    # Make sure it's not part of GST or invoice number
                    if not re.search(r'gst.*' + m, ocr_text, re.IGNORECASE) and not re.search(r'inv.*' + m, ocr_text, re.IGNORECASE):
                        resolved["customerMobile"] = m
                        break
        elif mobile_match:
            resolved["customerMobile"] = mobile_match.group(0)

        # 2. Vehicle Registration Disambiguation
        raw_veh = str(resolved.get("vehicleNumber", "") or "")
        clean_veh = re.sub(r'[^A-Za-z0-9]', '', raw_veh).upper()
        
        is_valid_veh = False
        for p in self.INDIAN_VEHICLE_PATTERNS:
            if re.search(p, raw_veh, re.IGNORECASE) or re.search(p, clean_veh, re.IGNORECASE):
                is_valid_veh = True
                break
                
        if not is_valid_veh and ocr_text:
            # Search OCR text for vehicle registration plate pattern
            veh_label_match = re.search(r'(?:veh|vehicle|reg|registration|car|auto|bike|truck|no)\s*[:#-]?\s*([A-Z]{2}\s*[0-9]{1,2}\s*[A-Z]{0,3}\s*[0-9]{4})', ocr_text, re.IGNORECASE)
            if veh_label_match:
                resolved["vehicleNumber"] = re.sub(r'\s+', '', veh_label_match.group(1)).upper()
            else:
                for p in self.INDIAN_VEHICLE_PATTERNS:
                    m = re.search(p, ocr_text, re.IGNORECASE)
                    if m:
                        resolved["vehicleNumber"] = re.sub(r'\s+', '', m.group(0)).upper()
                        break
        elif is_valid_veh:
            resolved["vehicleNumber"] = clean_veh

        # 3. Tyre Size Resolution
        raw_tyre = str(resolved.get("tyreSize", "") or "")
        tyre_match = False
        for p in self.TYRE_SIZE_PATTERNS:
            if re.search(p, raw_tyre, re.IGNORECASE):
                tyre_match = True
                break
                
        if not tyre_match and ocr_text:
            for p in self.TYRE_SIZE_PATTERNS:
                m = re.search(p, ocr_text, re.IGNORECASE)
                if m:
                    resolved["tyreSize"] = m.group(0).upper().replace(" ", "")
                    break

        # 4. Dealer GST vs Customer GST Resolution
        all_gsts = re.findall(self.GST_PATTERN, ocr_text, re.IGNORECASE)
        if all_gsts:
            all_gsts = [g.upper() for g in all_gsts]
            if not resolved.get("dealerGst"):
                resolved["dealerGst"] = all_gsts[0]
            if len(all_gsts) > 1 and not resolved.get("gstNumber"):
                resolved["gstNumber"] = all_gsts[1]

        # 5. Customer Name vs Dealer Name Disambiguation
        cust_name = str(resolved.get("customerName", "") or "").strip()
        dealer_name = str(resolved.get("dealerName", "") or "").strip()

        # If customer name looks like a company dealership (contains Motors, Tyres, Traders, Ltd, Pvt), swap or clean
        company_keywords = ["tyre", "motor", "auto", "trader", "enterprise", "pvt", "ltd", "corporation", "agency", "service", "workshop"]
        if cust_name and any(k in cust_name.lower() for k in company_keywords):
            if not dealer_name:
                resolved["dealerName"] = cust_name
                resolved["customerName"] = ""
            elif dealer_name.lower() == cust_name.lower():
                resolved["customerName"] = ""

        return resolved
