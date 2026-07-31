import re

class ReflectionAgent:
    """
    Reflection Review Agent
    
    Acts as a second-pass human operator quality check:
    Reviews every mapped field and evaluates:
    "Would an experienced enterprise human data-entry operator place this value in this column?"
    
    If confidence is insufficient, wipes the field to blank and logs uncertainty details.
    """

    COMPANY_TERMS = ["motors", "tyres", "auto", "traders", "enterprises", "pvt", "ltd", "corp", "agency", "services", "workshop", "store", "shop"]

    def reflect_and_review(self, fields: dict, confidence: float = 95.0) -> dict:
        reviewed_fields = dict(fields) if fields else {}
        reflection_logs = []
        confidence_delta = 0.0

        # 1. Reflection on Customer Name
        cust_name = str(reviewed_fields.get("customerName", "") or "").strip()
        if cust_name:
            if any(term in cust_name.lower() for term in self.COMPANY_TERMS):
                reflection_logs.append(f"Reflection: '{cust_name}' looks like a company name, not a customer person name. Moving to Dealer Name.")
                if not reviewed_fields.get("dealerName"):
                    reviewed_fields["dealerName"] = cust_name
                reviewed_fields["customerName"] = ""
                confidence_delta -= 5.0
            elif len(cust_name) < 2 or re.search(r'[\$\*_\-\|\+\=\#\@\!\?]', cust_name):
                reflection_logs.append(f"Reflection: '{cust_name}' contains OCR noise symbols. Blanked.")
                reviewed_fields["customerName"] = ""

        # 2. Reflection on Customer Mobile
        mobile = str(reviewed_fields.get("customerMobile", "") or "").strip()
        if mobile:
            digits = re.sub(r'[^\d]', '', mobile)
            if digits.startswith("91") and len(digits) == 12:
                digits = digits[2:]
            elif digits.startswith("0") and len(digits) == 11:
                digits = digits[1:]
                
            if not (len(digits) == 10 and re.match(r'^[6-9]\d{9}$', digits)):
                reflection_logs.append(f"Reflection: Mobile '{mobile}' does not form a valid 10-digit Indian mobile starting with 6-9. Blanked.")
                reviewed_fields["customerMobile"] = ""
                confidence_delta -= 10.0
            else:
                reviewed_fields["customerMobile"] = digits

        # 3. Reflection on Vehicle Number
        veh = str(reviewed_fields.get("vehicleNumber", "") or "").strip()
        if veh:
            clean_veh = re.sub(r'[^A-Za-z0-9]', '', veh).upper()
            if not (len(clean_veh) >= 6 and clean_veh[:2].isalpha()):
                reflection_logs.append(f"Reflection: Vehicle Number '{veh}' fails Indian license plate format. Blanked.")
                reviewed_fields["vehicleNumber"] = ""
                confidence_delta -= 10.0
            else:
                reviewed_fields["vehicleNumber"] = clean_veh

        # 4. Reflection on Tyre Size
        tyre_size = str(reviewed_fields.get("tyreSize", "") or "").strip()
        if tyre_size:
            if not re.search(r'\d{2,3}', tyre_size):
                reflection_logs.append(f"Reflection: Tyre Size '{tyre_size}' lacks standard numeric dimensions. Blanked.")
                reviewed_fields["tyreSize"] = ""

        # 5. Reflection on Financial Totals Math
        try:
            unit_cost = float(reviewed_fields.get("unitCost") or 0.0)
            qty = float(reviewed_fields.get("quantity") or 1.0)
            discount = float(reviewed_fields.get("discount") or 0.0)
            tax = float(reviewed_fields.get("tax") or 0.0)
            grand_total = float(reviewed_fields.get("grandTotal") or 0.0)

            if unit_cost > 0:
                expected_total = (unit_cost * qty) - discount + tax
                if grand_total > 0:
                    diff = abs(expected_total - grand_total)
                    if diff > 2.0 and diff != grand_total:
                        reflection_logs.append(f"Reflection Math Warning: Line total ({expected_total:.2f}) differs from Grand Total ({grand_total:.2f}).")
                        confidence_delta -= 15.0
                elif expected_total > 0 and not grand_total:
                    reviewed_fields["grandTotal"] = f"{expected_total:.2f}"
        except (ValueError, TypeError):
            pass

        final_confidence = round(max(confidence + confidence_delta, 60.0), 1)

        return {
            "fields": reviewed_fields,
            "confidence": final_confidence,
            "reflection_logs": reflection_logs
        }
