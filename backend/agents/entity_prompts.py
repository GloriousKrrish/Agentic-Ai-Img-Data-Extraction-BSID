"""
Dedicated Business Entity Extraction Schemas & Prompts
Each entity pass focuses exclusively on its designated business domain and ignores all other fields.
"""

ENTITY_SCHEMAS = {
    "customer": {
        "domain": "Customer Information",
        "fields": [
            {"key": "customerName", "label": "Customer Name", "description": "Full name of customer / buyer person ONLY. Do not include dealer or company shop name."},
            {"key": "customerMobile", "label": "Customer Mobile Number", "description": "10-digit mobile phone number of customer starting with 6-9."}
        ],
        "prompt": "Inspect the document ONLY for Customer / Buyer personal details. Extract the full name of the customer person and their 10-digit mobile number. Ignore dealer name, shop name, vehicle, tyres, and prices."
    },

    "dealer": {
        "domain": "Dealer Information",
        "fields": [
            {"key": "dealerName", "label": "Dealer Name", "description": "Full company / dealership / shop name issuing the invoice."},
            {"key": "dealerGst", "label": "Dealer GSTIN", "description": "15-character GSTIN tax number of the dealer / seller."},
            {"key": "dealerAddress", "label": "Dealer Address", "description": "Full shop or business address of the dealer."}
        ],
        "prompt": "Inspect the document ONLY for Dealer / Seller information. Extract the dealer shop name, dealer GSTIN number, and dealer address. Ignore customer details, vehicle, tyres, and invoice numbers."
    },

    "vehicle": {
        "domain": "Vehicle Information",
        "fields": [
            {"key": "vehicleNumber", "label": "Vehicle Registration Number", "description": "Vehicle license plate registration number (e.g. AP39NT1461, MH12AB1234)."},
            {"key": "vehicleModel", "label": "Vehicle Model", "description": "Vehicle model name or brand (e.g. Swift, Innova, Creta)."}
        ],
        "prompt": "Inspect the document ONLY for Vehicle details. Extract the vehicle registration license plate number and vehicle model name. Ignore prices, dealer names, and customer phone numbers."
    },

    "invoice_meta": {
        "domain": "Invoice Metadata",
        "fields": [
            {"key": "invoiceNumber", "label": "Invoice Number", "description": "Invoice number, bill reference, or cash memo number."},
            {"key": "invoiceDate", "label": "Invoice Date", "description": "Issue date of invoice (DD/MM/YYYY or YYYY-MM-DD)."}
        ],
        "prompt": "Inspect the document ONLY for Invoice Metadata. Extract the invoice number/bill reference and the invoice issue date. Ignore items, prices, and customer details."
    },

    "tyre": {
        "domain": "Tyre & Product Information",
        "fields": [
            {"key": "tyreSize", "label": "Tyre Size", "description": "Tyre specification size code (e.g. 235/65R17, 185/65 R15)."},
            {"key": "pattern", "label": "Tyre Pattern", "description": "Tyre tread pattern or design name (e.g. Wanderer, Dueler, Turanza)."},
            {"key": "dotCode", "label": "DOT Code", "description": "DOT manufacturing batch code (e.g. DOT 4223)."},
            {"key": "serialNumber", "label": "Serial Number", "description": "Product or tyre serial number."}
        ],
        "prompt": "Inspect the document ONLY for Tyre & Product specifications. Extract tyre size code, tread pattern name, DOT batch code, and serial numbers. Ignore prices, totals, and customer phone numbers."
    },

    "financial": {
        "domain": "Financial Summary",
        "fields": [
            {"key": "quantity", "label": "Quantity", "description": "Total number of units purchased."},
            {"key": "unitCost", "label": "Unit Cost", "description": "Price per single unit before tax/discount."},
            {"key": "discount", "label": "Discount", "description": "Discount amount applied."},
            {"key": "tax", "label": "Tax Amount", "description": "Total GST or VAT tax amount."},
            {"key": "grandTotal", "label": "Grand Total", "description": "Final total payable amount."}
        ],
        "prompt": "Inspect the document ONLY for Financial Summary figures. Extract item quantity, unit cost, discount, tax, and final grand total amount. Ignore names, addresses, and vehicle numbers."
    },

    "remarks": {
        "domain": "Remarks & Notes",
        "fields": [
            {"key": "remarks", "label": "Remarks / Notes", "description": "Additional notes, terms, or warranty comments."},
            {"key": "paymentMode", "label": "Payment Mode", "description": "Payment method (Cash, UPI, Credit Card, Bank Transfer)."}
        ],
        "prompt": "Inspect the document ONLY for Additional Notes & Payment Mode. Extract payment mode and any remarks or warranty notes. Ignore line items, prices, and vehicle numbers."
    }
}

VERIFICATION_AUDIT_PROMPT = """You are a Senior Business Data Audit Specialist.
Below is the merged extraction dictionary from an invoice document alongside the original document text:

MERGED EXTRACTION DATA:
{merged_json}

DOCUMENT OCR TEXT:
{ocr_text}

AUDIT INSTRUCTIONS:
1. Verify if Customer Name is a person's name or if it accidentally contains the Dealer / Shop name.
2. Verify if Customer Mobile is a valid 10-digit number.
3. Verify if Vehicle Registration number is valid.
4. Verify if Grand Total equals (Unit Cost * Quantity) - Discount + Tax.
5. Identify any missed fields or incorrect mappings.

Return the audited and corrected dictionary. If a field is uncertain or missing, set its value to null.
Do not invent data.
"""
