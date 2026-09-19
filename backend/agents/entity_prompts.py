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

DOMAIN_PRESETS = {
    "Invoice / Bill": {
        "category": "Invoice",
        "fields": [
            {"key": "invoiceNumber", "label": "Invoice Number", "type": "string", "description": "Invoice reference number"},
            {"key": "invoiceDate", "label": "Invoice Date", "type": "string", "description": "Issue date"},
            {"key": "customerName", "label": "Customer Name", "type": "string", "description": "Name of customer / buyer"},
            {"key": "customerMobile", "label": "Customer Mobile", "type": "string", "description": "Customer mobile phone number"},
            {"key": "dealerName", "label": "Dealer Name", "type": "string", "description": "Dealer or seller company name"},
            {"key": "dealerGst", "label": "Dealer GSTIN", "type": "string", "description": "Tax ID / GSTIN"},
            {"key": "grandTotal", "label": "Grand Total", "type": "string", "description": "Final payable amount"}
        ]
    },
    "Medical / Lab Report": {
        "category": "Medical Report",
        "fields": [
            {"key": "patientName", "label": "Patient Name", "type": "string", "description": "Full name of patient"},
            {"key": "patientAgeGender", "label": "Age / Gender", "type": "string", "description": "Patient age and gender"},
            {"key": "doctorName", "label": "Doctor / Physician", "type": "string", "description": "Attending doctor name"},
            {"key": "reportDate", "label": "Report Date", "type": "string", "description": "Lab test / report date"},
            {"key": "diagnosis", "label": "Diagnosis / Impression", "type": "string", "description": "Medical diagnosis or impression"},
            {"key": "abnormalResults", "label": "Abnormal Flags", "type": "string", "description": "Any out-of-range lab results"}
        ]
    },
    "KYC / ID Card": {
        "category": "KYC Document",
        "fields": [
            {"key": "fullName", "label": "Full Name", "type": "string", "description": "Full name on ID card"},
            {"key": "idNumber", "label": "ID Number", "type": "string", "description": "Aadhaar / Passport / SSN / License number"},
            {"key": "dateOfBirth", "label": "Date of Birth", "type": "string", "description": "DOB (YYYY-MM-DD)"},
            {"key": "gender", "label": "Gender", "type": "string", "description": "Gender / Sex"},
            {"key": "address", "label": "Address", "type": "string", "description": "Residential address"},
            {"key": "expiryDate", "label": "Expiry Date", "type": "string", "description": "ID card expiration date"}
        ]
    },
    "Academic Result / Marksheet": {
        "category": "Academic Result",
        "fields": [
            {"key": "studentName", "label": "Student Name", "type": "string", "description": "Full student name"},
            {"key": "rollNumber", "label": "Roll / Registration No", "type": "string", "description": "Student roll or reg number"},
            {"key": "institutionName", "label": "School / University", "type": "string", "description": "Institution name"},
            {"key": "gpaOrMarks", "label": "Total Marks / GPA", "type": "string", "description": "Final score, GPA, or percentage"},
            {"key": "resultStatus", "label": "Pass / Fail Status", "type": "string", "description": "Pass, Fail, Distinction status"}
        ]
    },
    "Financial Statement": {
        "category": "Financial Statement",
        "fields": [
            {"key": "companyName", "label": "Company Name", "type": "string", "description": "Entity name"},
            {"key": "periodEnding", "label": "Fiscal Period", "type": "string", "description": "Quarter / Year ending date"},
            {"key": "totalRevenue", "label": "Total Revenue", "type": "string", "description": "Net sales or total revenue"},
            {"key": "netIncome", "label": "Net Income / Profit", "type": "string", "description": "Net profit or income"},
            {"key": "totalAssets", "label": "Total Assets", "type": "string", "description": "Total balance sheet assets"}
        ]
    },
    "Legal Contract": {
        "category": "Legal Contract",
        "fields": [
            {"key": "contractTitle", "label": "Contract Title", "type": "string", "description": "Agreement title"},
            {"key": "partyA", "label": "Party A", "type": "string", "description": "First contracting party"},
            {"key": "partyB", "label": "Party B", "type": "string", "description": "Second contracting party"},
            {"key": "effectiveDate", "label": "Effective Date", "type": "string", "description": "Start date"},
            {"key": "contractValue", "label": "Contract Value", "type": "string", "description": "Total monetary value"},
            {"key": "governingLaw", "label": "Governing Law", "type": "string", "description": "Jurisdiction / Law"}
        ]
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

