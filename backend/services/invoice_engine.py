import io
import re
import csv
import requests
from pathlib import Path
import openpyxl
from backend.services.schema_generator import generate_dynamic_schema
from backend.services.universal_extractor import extract_universal_document

# Comprehensive Semantic Field Extraction Schema for Invoices/Receipts
INVOICE_SEMANTIC_PROMPT_SCHEMA = {
    "documentCategory": "Invoice / Transaction Document",
    "documentTitle": "Intelligent Extracted Invoice Data",
    "summary": "Extracted semantic key-value fields from invoice or transaction document",
    "fields": [
        {"key": "invoiceNumber", "label": "Invoice Number", "type": "string", "description": "Invoice number, bill number, or invoice reference code"},
        {"key": "invoiceDate", "label": "Invoice Date", "type": "string", "description": "Date invoice was issued (DD/MM/YYYY or YYYY-MM-DD)"},
        {"key": "customerName", "label": "Customer Name", "type": "string", "description": "Full name of buyer or customer"},
        {"key": "customerMobile", "label": "Customer Mobile", "type": "string", "description": "Customer phone number or mobile number"},
        {"key": "vehicleNumber", "label": "Vehicle Number", "type": "string", "description": "Vehicle registration number (e.g. AP39NT1461, MH12AB1234)"},
        {"key": "vehicleModel", "label": "Vehicle Model", "type": "string", "description": "Vehicle model name (e.g. Swift, Innova, Creta)"},
        {"key": "vehicleBrand", "label": "Vehicle Brand", "type": "string", "description": "Vehicle brand/make (e.g. Maruti, Toyota, Hyundai)"},
        {"key": "tyreSize", "label": "Tyre Size", "type": "string", "description": "Tyre specification or size code (e.g. 235/65R17, 185/65 R15)"},
        {"key": "pattern", "label": "Pattern / Tread", "type": "string", "description": "Tyre pattern or tread design name"},
        {"key": "dotCode", "label": "DOT Code", "type": "string", "description": "DOT manufacturing batch code"},
        {"key": "serialNumber", "label": "Serial Number", "type": "string", "description": "Tyre or product serial number"},
        {"key": "hsn", "label": "HSN / SAC Code", "type": "string", "description": "HSN code for GST tax classification"},
        {"key": "gstNumber", "label": "Customer GST Number", "type": "string", "description": "GSTIN number of customer"},
        {"key": "dealerName", "label": "Dealer / Seller Name", "type": "string", "description": "Name of dealership, shop, or company issuing invoice"},
        {"key": "dealerGst", "label": "Dealer GSTIN", "type": "string", "description": "GSTIN number of dealer or seller"},
        {"key": "dealerAddress", "label": "Dealer Address", "type": "string", "description": "Full address of dealer"},
        {"key": "unitCost", "label": "Unit Cost", "type": "number", "description": "Price per single unit"},
        {"key": "quantity", "label": "Quantity", "type": "number", "description": "Number of units or items purchased"},
        {"key": "totalCost", "label": "Total Cost / Subtotal", "type": "number", "description": "Subtotal cost before tax and discount"},
        {"key": "discount", "label": "Discount Amount", "type": "number", "description": "Discount amount applied"},
        {"key": "taxAmount", "label": "Tax Amount (GST/VAT)", "type": "number", "description": "Total tax amount"},
        {"key": "grandTotal", "label": "Grand Total", "type": "number", "description": "Final total payable amount"},
        {"key": "paymentMode", "label": "Payment Mode", "type": "string", "description": "Payment mode (Cash, UPI, Credit Card, Bank Transfer)"},
        {"key": "remarks", "label": "Remarks / Notes", "type": "string", "description": "Additional notes, terms, or comments"}
    ]
}

def detect_url_column_in_excel(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Scans any Excel or CSV workbook and automatically extracts HTTP/HTTPS URLs from any column or row.
    Returns: [{"rowIndex": 2, "url": "https://..."}]
    """
    ext = Path(filename).suffix.lower()
    urls = []
    url_pattern = re.compile(r'https?://[^\s,\"\']+')

    try:
        if ext == '.csv':
            decoded = file_bytes.decode('utf-8', errors='ignore')
            reader = csv.reader(io.StringIO(decoded))
            for row_idx, row in enumerate(reader, start=1):
                for cell in row:
                    cell_str = str(cell).strip()
                    match = url_pattern.search(cell_str)
                    if match:
                        urls.append({"rowIndex": row_idx, "url": match.group(0)})
        elif ext in ['.xlsx', '.xls']:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            sheet = wb.active
            for row_idx in range(1, sheet.max_row + 1):
                for col_idx in range(1, sheet.max_column + 1):
                    val = sheet.cell(row=row_idx, column=col_idx).value
                    val_str = str(val).strip() if val is not None else ""
                    match = url_pattern.search(val_str)
                    if match:
                        urls.append({"rowIndex": row_idx, "url": match.group(0)})
            wb.close()
    except Exception as e:
        print(f"Error scanning workbook for URLs: {e}")

    return urls

def process_invoice_document(doc_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Processes an invoice document (image or PDF) through Vision AI and extracts all semantic fields.
    """
    try:
        ext_res = extract_universal_document(
            doc_bytes, 
            INVOICE_SEMANTIC_PROMPT_SCHEMA, 
            mime_type
        )
        rows = ext_res.get("rows", [])
        if rows and len(rows) > 0:
            return rows[0].get("fields", {})
        return {}
    except Exception as e:
        print(f"Error processing invoice document: {e}")
        return {}
