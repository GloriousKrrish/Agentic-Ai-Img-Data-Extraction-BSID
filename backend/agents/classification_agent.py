class ClassificationAgent:
    """
    Step 5: Document Classification Agent
    Determines exact document category (Tax Invoice, Receipt, Medical Bill, Resume, Academic Result, PO, Warranty)
    and assigns a classification confidence score.
    """
    def classify(self, text_content: str, schema_info: dict = None) -> dict:
        text_lower = (text_content or "").lower()
        
        if schema_info and schema_info.get("documentCategory"):
            return {
                "category": schema_info.get("documentCategory"),
                "confidence": 95.0
            }
            
        if any(k in text_lower for k in ["tax invoice", "bill of supply", "invoice no", "gstin"]):
            return {"category": "Tax Invoice", "confidence": 98.0}
        elif any(k in text_lower for k in ["receipt", "payment voucher", "cash memo"]):
            return {"category": "Receipt", "confidence": 95.0}
        elif any(k in text_lower for k in ["patient", "doctor", "hospital", "diagnosis", "prescription"]):
            return {"category": "Medical Record", "confidence": 95.0}
        elif any(k in text_lower for k in ["resume", "curriculum vitae", "experience", "education"]):
            return {"category": "Resume / CV", "confidence": 95.0}
        elif any(k in text_lower for k in ["report card", "marksheet", "grade", "gpa", "semester"]):
            return {"category": "Academic Result", "confidence": 95.0}
        elif any(k in text_lower for k in ["purchase order", "po number"]):
            return {"category": "Purchase Order", "confidence": 95.0}
        elif any(k in text_lower for k in ["delivery challan", "dispatch note"]):
            return {"category": "Delivery Challan", "confidence": 95.0}
            
        return {"category": "General Document", "confidence": 85.0}
