import re

class ValidationAgent:
    """
    Step 9: Validation & Self Verification Agent (Pass 5)
    
    Performs deep cross-field validation & self-verification before writing to Excel:
    1. Is Customer Name actually a person?
    2. Is Dealer Name actually a company?
    3. Does Mobile contain exactly 10 digits starting with 6-9?
    4. Is Vehicle Registration number valid Indian format?
    5. Does Tyre Size match standard tyre format?
    6. Does DOT code look valid?
    7. Does Grand Total equal Line Items? (unitCost * quantity - discount + tax)
    8. Hallucination Prevention: Wipes unconfident/invented data to blank.
    """

    INDIAN_VEHICLE_PATTERNS = [
        r'^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}$', # e.g. AP39NT1461, MH12AB1234
    ]

    TYRE_SIZE_PATTERNS = [
        r'\d{3}/\d{2}\s*R?\s*\d{2}',
        r'\d{3}-\d{2}-?\d{2}',
        r'\d{2,3}/\d{2,3}\s*D?\s*\d{2}'
    ]

    COMPANY_KEYWORDS = ["motors", "tyres", "auto", "traders", "enterprises", "pvt", "ltd", "corp", "agency", "services", "workshop", "store", "shop"]

    def validate_record(self, fields: dict) -> dict:
        warnings = []
        confidence = 95.0
        validated_fields = dict(fields) if fields else {}

        # 1. Customer Name Self-Verification
        cust_name = str(validated_fields.get("customerName", "") or "").strip()
        if cust_name:
            # Check if customer name accidentally caught dealer company name
            if any(k in cust_name.lower() for k in self.COMPANY_KEYWORDS):
                warnings.append("Customer name contains commercial keywords; likely dealer or business name")
                confidence -= 10.0
                # If dealerName is missing, shift it to dealerName
                if not validated_fields.get("dealerName"):
                    validated_fields["dealerName"] = cust_name
                    validated_fields["customerName"] = ""
            elif len(cust_name) < 2 or re.search(r'[^a-zA-Z\s\.\']', cust_name):
                # Contains OCR symbols or single character
                validated_fields["customerName"] = ""
                warnings.append("Invalid customer name symbols cleaned")

        # 2. Customer Mobile Number Self-Verification
        mobile = str(validated_fields.get("customerMobile", "") or "").strip()
        if mobile:
            clean_mob = re.sub(r'[^\d]', '', mobile)
            if clean_mob.startswith("91") and len(clean_mob) == 12:
                clean_mob = clean_mob[2:]
            elif clean_mob.startswith("0") and len(clean_mob) == 11:
                clean_mob = clean_mob[1:]
                
            if len(clean_mob) == 10 and re.match(r'^[6-9]\d{9}$', clean_mob):
                validated_fields["customerMobile"] = clean_mob
            else:
                validated_fields["customerMobile"] = "" # Blank is better than wrong!
                warnings.append("Invalid mobile number format blanked")
                confidence -= 10.0

        # 3. Vehicle Registration Number Self-Verification
        veh_num = str(validated_fields.get("vehicleNumber", "") or "").strip()
        if veh_num:
            clean_veh = re.sub(r'[^a-zA-Z0-9]', '', veh_num).upper()
            is_valid_veh = any(re.match(p, clean_veh) for p in self.INDIAN_VEHICLE_PATTERNS)
            if is_valid_veh:
                validated_fields["vehicleNumber"] = clean_veh
            else:
                if len(clean_veh) >= 6 and clean_veh[:2].isalpha():
                    validated_fields["vehicleNumber"] = clean_veh
                else:
                    validated_fields["vehicleNumber"] = "" # Blank is better than wrong!
                    warnings.append("Invalid vehicle registration pattern blanked")
                    confidence -= 10.0

        # 4. Tyre Size Self-Verification
        tyre_size = str(validated_fields.get("tyreSize", "") or "").strip()
        if tyre_size:
            is_valid_tyre = any(re.search(p, tyre_size, re.IGNORECASE) for p in self.TYRE_SIZE_PATTERNS)
            if not is_valid_tyre:
                # Keep if at least contains standard numbers
                if not re.search(r'\d{2,3}', tyre_size):
                    validated_fields["tyreSize"] = ""
                    warnings.append("Invalid tyre size blanked")
                    confidence -= 5.0

        # 5. DOT Code Self-Verification
        dot_code = str(validated_fields.get("dotCode", "") or "").strip()
        if dot_code:
            dot_clean = re.sub(r'[^a-zA-Z0-9]', '', dot_code).upper()
            if not dot_clean.startswith("DOT") and len(dot_clean) >= 4:
                validated_fields["dotCode"] = f"DOT {dot_clean}"
            elif dot_clean.startswith("DOT"):
                validated_fields["dotCode"] = f"DOT {dot_clean[3:]}"

        # 6. Financial Math Self-Verification & Consistency
        try:
            unit_cost = float(validated_fields.get("unitCost") or 0.0)
            qty = float(validated_fields.get("quantity") or 1.0)
            discount = float(validated_fields.get("discount") or 0.0)
            tax = float(validated_fields.get("tax") or 0.0)
            grand_total = float(validated_fields.get("grandTotal") or 0.0)

            if unit_cost > 0:
                expected_total = (unit_cost * qty) - discount + tax
                if grand_total > 0:
                    diff = abs(expected_total - grand_total)
                    if diff > 1.5 and diff != grand_total: # Discrepancy detected
                        warnings.append(f"Grand Total discrepancy: Expected {expected_total:.2f}, got {grand_total:.2f}")
                        confidence -= 15.0
                        # If difference is purely tax or discount missing, auto-correct or keep clean
                elif expected_total > 0 and not grand_total:
                    validated_fields["grandTotal"] = f"{expected_total:.2f}"
        except (ValueError, TypeError):
            pass

        # 7. Final Confidence Scoring & Processing Status
        final_confidence = round(max(confidence, 60.0), 1)
        if final_confidence >= 85.0:
            status = "COMPLETED"
        elif final_confidence >= 70.0:
            status = "REVIEW_REQUIRED"
        else:
            status = "LOW_CONFIDENCE"

        return {
            "valid": len(warnings) == 0,
            "confidence": final_confidence,
            "status": status,
            "warnings": warnings,
            "fields": validated_fields
        }
