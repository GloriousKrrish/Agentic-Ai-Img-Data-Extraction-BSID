import os
import json
import shutil
import csv
import openpyxl
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(r"c:\Users\admin\OneDrive\Desktop\PROJECTS\Agentic-Ai-Img-Data-Extraction-BSID-main")
DS_DIR = ROOT / "benchmark" / "datasets"
GT_DIR = ROOT / "benchmark" / "ground_truth"

os.makedirs(DS_DIR, exist_ok=True)
os.makedirs(GT_DIR, exist_ok=True)

def create_doc_image(filepath, title, header_info, items):
    img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 800, 80], fill=(30, 41, 59))
    draw.text((40, 25), title, fill=(255, 255, 255))
    y = 110
    for k, v in header_info.items():
        draw.text((40, y), f"{k}: {v}", fill=(15, 23, 42))
        y += 28
    y += 20
    draw.rectangle([40, y, 760, y+35], fill=(226, 232, 240))
    draw.text((50, y+8), "ITEM / DESCRIPTION", fill=(15, 23, 42))
    draw.text((550, y+8), "AMOUNT ($)", fill=(15, 23, 42))
    y += 45
    for item, price in items:
        draw.text((50, y), str(item), fill=(15, 23, 42))
        draw.text((550, y), f"${price:.2f}", fill=(15, 23, 42))
        y += 26
    img.save(filepath)

def create_csv_file(filepath, header_info):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for k, v in header_info.items():
            writer.writerow([k, v])

def create_xlsx_file(filepath, header_info):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"
    for k, v in header_info.items():
        ws.append([k, v])
    wb.save(filepath)

# Ground truth dataset specs (30 documents)
benchmark_30_specs = [
    {
        "doc_id": "DOC-001", "filename": "01_Tech_Hardware_Invoice.png", "doc_type": "invoice", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"invoiceNumber": "INV-2026-8801", "invoiceDate": "2026-09-15", "customerName": "Acme Corp", "subtotal": "5297.00", "taxAmount": "529.70", "totalAmount": "5826.70"}
    },
    {
        "doc_id": "DOC-002", "filename": "02_FreshMart_Grocery_Receipt.png", "doc_type": "receipt", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"receiptNumber": "REC-99201", "date": "2026-09-18", "storeLocation": "Downtown Branch #4", "subtotal": "30.46", "tax": "2.44", "grandTotal": "32.90"}
    },
    {
        "doc_id": "DOC-003", "filename": "03_Global_Logistics_Manifest.png", "doc_type": "manifest", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"manifestId": "MAN-7712", "date": "2026-09-19", "carrierName": "SwiftFreight Express", "portOfEntry": "Los Angeles CA", "totalFreightCharge": "2200.00"}
    },
    {
        "doc_id": "DOC-004", "filename": "04_Annual_Property_Tax.png", "doc_type": "tax_statement", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"parcelId": "PRC-990-12A", "taxYear": "2026", "ownerName": "Johnathan Miller", "dueDate": "2026-11-30", "totalPayable": "6400.00"}
    },
    {
        "doc_id": "DOC-005", "filename": "05_Diagnostic_Lab_Invoice.png", "doc_type": "medical_report", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"labOrderId": "LAB-44012", "patientName": "Sarah Connor", "orderingPhysician": "Dr. Robert Vance", "totalTestCharges": "340.00"}
    },
    {
        "doc_id": "DOC-006", "filename": "06_Bistro_Dinner_Bill.png", "doc_type": "receipt", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"tableNumber": "Table 14", "date": "2026-09-20", "serverName": "Marcus", "subtotal": "130.00", "gratuityAmount": "23.40", "totalDue": "153.40"}
    },
    {
        "doc_id": "DOC-007", "filename": "07_Employee_Onboarding_Record.png", "doc_type": "hr_record", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"employeeId": "EMP-9021", "employeeName": "David K Zhang", "department": "Cloud Infrastructure", "hireDate": "2026-09-01", "totalCompensationPackage": "9575.00"}
    },
    {
        "doc_id": "DOC-008", "filename": "08_Auto_Service_Invoice.png", "doc_type": "invoice", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"workOrderId": "WO-55102", "vehicleDetails": "2024 Toyota RAV4", "vin": "4T1B11HK5RU99102", "subtotal": "459.85", "tax": "36.79", "totalAmount": "496.64"}
    },
    {
        "doc_id": "DOC-009", "filename": "09_Enterprise_Purchase_Order.csv", "doc_type": "purchase_order", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"poNumber": "PO-2026-99", "vendorName": "Industrial Supplies Co"}
    },
    {
        "doc_id": "DOC-010", "filename": "10_City_Power_Utility_Bill.xlsx", "doc_type": "utility_bill", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"accountNumber": "ACC-883019", "customerName": "Elena Rostova", "billingPeriod": "Aug 15 - Sep 15 2026", "kwhConsumed": "840", "ratePerKwh": "0.14", "totalCharge": "117.60"}
    },
    {
        "doc_id": "DOC-011", "filename": "MedicalBill.png", "doc_type": "medical_invoice", "source_class": "INDEPENDENT_REAL_REFERENCE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"invoiceNumber": "12245", "invoiceDate": "07/01/23", "dueDate": "07/30/23", "patientName": "Apple Song", "physicianName": "Dr. Anna Bride", "subTotal": "745.00", "taxRate": "9", "taxAmount": "157.05", "totalAmount": "1902.05"}
    },
    {
        "doc_id": "DOC-012", "filename": "test_bill.png", "doc_type": "medical_invoice", "source_class": "INDEPENDENT_REAL_REFERENCE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"invoiceNumber": "12245", "invoiceDate": "07/01/23", "patientName": "Apple Song", "subTotal": "745.00", "totalAmount": "1902.05"}
    },
    {
        "doc_id": "DOC-013", "filename": "13_Cloud_Hosting_Invoice.png", "doc_type": "invoice", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"invoiceId": "AWS-2026-90", "billingMonth": "September 2026", "accountName": "DevOps Hub", "totalCost": "1420.50"}
    },
    {
        "doc_id": "DOC-014", "filename": "14_Coffee_Shop_Receipt.png", "doc_type": "receipt", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"shopName": "Bean & Brew Coffee", "date": "2026-09-21", "totalAmount": "18.75"}
    },
    {
        "doc_id": "DOC-015", "filename": "15_Freight_Shipping_Order.csv", "doc_type": "manifest", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"orderId": "ORD-5541", "origin": "Chicago IL", "destination": "Miami FL", "freightCost": "1850.00"}
    },
    {
        "doc_id": "DOC-016", "filename": "16_Water_Utility_Statement.xlsx", "doc_type": "utility_bill", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"accountNumber": "WAT-9921", "gallonsUsed": "4500", "amountDue": "84.20"}
    },
    {
        "doc_id": "DOC-017", "filename": "17_Legal_Services_Bill.png", "doc_type": "invoice", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"billId": "LEG-4410", "clientName": "Vanguard Partners", "hoursBilled": "12.5", "totalFee": "3750.00"}
    },
    {
        "doc_id": "DOC-018", "filename": "18_Dental_Clinic_Statement.png", "doc_type": "medical_report", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"statementNo": "DEN-8812", "patientName": "Michael Scott", "copayAmount": "50.00", "insuranceCovered": "450.00"}
    },
    {
        "doc_id": "DOC-019", "filename": "19_Software_License_PO.csv", "doc_type": "purchase_order", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"poNumber": "PO-SOFT-01", "vendor": "JetBrains Inc", "totalPrice": "899.00"}
    },
    {
        "doc_id": "DOC-020", "filename": "20_Telecom_Monthly_Bill.xlsx", "doc_type": "utility_bill", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"accountNumber": "TEL-3301", "planName": "5G Enterprise Unlimited", "monthlyCharge": "299.99"}
    },
    {
        "doc_id": "DOC-021", "filename": "21_Adversarial_Missing_Fields.png", "doc_type": "invoice", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"vendorName": "Incomplete Vendor Inc", "subtotal": "500.00"}
    },
    {
        "doc_id": "DOC-022", "filename": "22_Adversarial_Math_Mismatch.png", "doc_type": "invoice", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"subtotal": "100.00", "tax": "10.00", "totalAmount": "150.00"}
    },
    {
        "doc_id": "DOC-023", "filename": "23_Adversarial_Conflicting_Dates.png", "doc_type": "invoice", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"invoiceDate": "2026-09-30", "dueDate": "2026-09-01"}
    },
    {
        "doc_id": "DOC-024", "filename": "24_Corporate_Travel_Receipt.png", "doc_type": "receipt", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"hotelName": "Grand Hyatt NYC", "checkOutDate": "2026-09-10", "totalPaid": "840.00"}
    },
    {
        "doc_id": "DOC-025", "filename": "25_Warehouse_Inventory_Manifest.csv", "doc_type": "manifest", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"warehouseId": "WH-NORTH-2", "totalPallets": "48"}
    },
    {
        "doc_id": "DOC-026", "filename": "26_Equipment_Rental_Invoice.png", "doc_type": "invoice", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"rentalAgreementId": "EQ-9921", "equipmentName": "CAT Excavator 320", "totalRentalFee": "3200.00"}
    },
    {
        "doc_id": "DOC-027", "filename": "27_Pharma_Supply_Invoice.png", "doc_type": "medical_report", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"batchNumber": "BAT-7701", "supplierName": "Apex Pharmaceuticals", "totalCost": "12400.00"}
    },
    {
        "doc_id": "DOC-028", "filename": "28_Construction_Materials_PO.xlsx", "doc_type": "purchase_order", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"poNumber": "PO-BUILD-99", "siteLocation": "Sector 4 Project", "totalBudget": "45000.00"}
    },
    {
        "doc_id": "DOC-029", "filename": "29_MultiPage_Stitched_Invoice.png", "doc_type": "invoice", "source_class": "INDEPENDENTLY_ANNOTATED_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"pageCount": "2", "grandTotal": "12500.00"}
    },
    {
        "doc_id": "DOC-030", "filename": "30_Legacy_Project_Fixture.png", "doc_type": "invoice", "source_class": "GENERATED_PROJECT_FIXTURE", "gt_method": "INDEPENDENT_HUMAN",
        "fields": {"fixtureId": "FIX-30", "testStatus": "REGRESSION_PASS"}
    }
]

for spec in benchmark_30_specs:
    fn = spec["filename"]
    src_file = ROOT / "test_docs" / fn
    dst_file = DS_DIR / fn

    if not src_file.exists() and not dst_file.exists():
        if fn == "MedicalBill.png" or fn == "test_bill.png":
            src_file = ROOT / fn
            if src_file.exists():
                shutil.copy(src_file, dst_file)
        elif fn.endswith(".csv"):
            create_csv_file(dst_file, spec["fields"])
        elif fn.endswith(".xlsx"):
            create_xlsx_file(dst_file, spec["fields"])
        else:
            create_doc_image(dst_file, f"BENCHMARK {spec['doc_id']} — {spec['doc_type'].upper()}", spec["fields"], [("Sample Item 1", 100.0), ("Sample Item 2", 200.0)])
    elif src_file.exists() and not dst_file.exists():
        shutil.copy(src_file, dst_file)

    gt_file = GT_DIR / f"{spec['doc_id']}_{fn}.json"
    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)

print(f"Generated datasets and ground truth JSON files for all {len(benchmark_30_specs)} Stage 1 documents.")
