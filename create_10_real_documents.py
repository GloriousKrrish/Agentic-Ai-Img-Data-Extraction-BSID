import os
from PIL import Image, ImageDraw, ImageFont
import csv
import openpyxl

out_dir = r"c:\Users\admin\OneDrive\Desktop\PROJECTS\Agentic-Ai-Img-Data-Extraction-BSID-main\test_docs"
os.makedirs(out_dir, exist_ok=True)

# Helper to draw text invoice images
def create_invoice_image(filepath, title, data_rows, header_info):
    img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Title
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
    
    for item, price in data_rows:
        draw.text((50, y), str(item), fill=(15, 23, 42))
        draw.text((550, y), f"${price:.2f}", fill=(15, 23, 42))
        y += 26
        
    img.save(filepath)
    print(f"Created {filepath}")

# 1. Tech Hardware Invoice (Image)
create_invoice_image(
    os.path.join(out_dir, "01_Tech_Hardware_Invoice.png"),
    "APEX TECH SOLUTIONS - INVOICE",
    [("MacBook Pro 16 M3 Max", 3499.00), ("Studio Display 27", 1599.00), ("Magic Keyboard Touch ID", 199.00)],
    {"Invoice Number": "INV-2026-8801", "Date": "2026-09-15", "Customer Name": "Acme Corp", "Subtotal": "5297.00", "Tax (10%)": "529.70", "Total Amount": "5826.70"}
)

# 2. Grocery Store Receipt (Image)
create_invoice_image(
    os.path.join(out_dir, "02_FreshMart_Grocery_Receipt.png"),
    "FRESHMART SUPERMARKET RECEIPT",
    [("Organic Whole Milk 1Gal", 5.99), ("Avocado Bag 5ct", 4.99), ("Wild Sockeye Salmon 1lb", 14.99), ("Sourdough Bread", 4.49)],
    {"Receipt Number": "REC-99201", "Date": "2026-09-18", "Store Location": "Downtown Branch #4", "Subtotal": "30.46", "Tax": "2.44", "Grand Total": "32.90"}
)

# 3. Logistics Manifest (Image)
create_invoice_image(
    os.path.join(out_dir, "03_Global_Logistics_Manifest.png"),
    "GLOBAL LOGISTICS FREIGHT MANIFEST",
    [("Container A - Electronic Components", 1200.00), ("Container B - Plastic Enclosures", 850.00), ("Customs Inspection Fee", 150.00)],
    {"Manifest ID": "MAN-7712", "Date": "2026-09-19", "Carrier Name": "SwiftFreight Express", "Port of Entry": "Los Angeles CA", "Total Freight Charge": "2200.00"}
)

# 4. Tax Statement (Image)
create_invoice_image(
    os.path.join(out_dir, "04_Annual_Property_Tax.png"),
    "CITY PROPERTY TAX STATEMENT 2026",
    [("Base Property Assessment Tax", 4200.00), ("Local School District Levy", 1850.00), ("Municipal Infrastructure Fee", 350.00)],
    {"Parcel ID": "PRC-990-12A", "Tax Year": "2026", "Owner Name": "Johnathan Miller", "Due Date": "2026-11-30", "Total Payable": "6400.00"}
)

# 5. Diagnostic Lab Report (Image)
create_invoice_image(
    os.path.join(out_dir, "05_Diagnostic_Lab_Invoice.png"),
    "BIOMED DIAGNOSTICS LAB REPORT",
    [("Comprehensive Metabolic Panel (CMP)", 180.00), ("Lipid Panel Profile", 95.00), ("Hemoglobin A1c Test", 65.00)],
    {"Lab Order ID": "LAB-44012", "Patient Name": "Sarah Connor", "Ordering Physician": "Dr. Robert Vance", "Total Test Charges": "340.00"}
)

# 6. Restaurant Bill (Image)
create_invoice_image(
    os.path.join(out_dir, "06_Bistro_Dinner_Bill.png"),
    "L'ETOILE BISTRO DINNER BILL",
    [("Ribeye Steak 12oz", 48.00), ("Pan Seared Sea Bass", 42.00), ("Pinot Noir Glass x2", 28.00), ("Tiramisu Dessert", 12.00)],
    {"Table Number": "Table 14", "Date": "2026-09-20", "Server Name": "Marcus", "Subtotal": "130.00", "Gratuity 18%": "23.40", "Total Due": "153.40"}
)

# 7. HR Employee Record (Image)
create_invoice_image(
    os.path.join(out_dir, "07_Employee_Onboarding_Record.png"),
    "ENTERPRISE HR ONBOARDING SUMMARY",
    [("Base Monthly Salary", 8500.00), ("Health Insurance Benefit", 650.00), ("401k Employer Match", 425.00)],
    {"Employee ID": "EMP-9021", "Employee Name": "David K. Zhang", "Department": "Cloud Infrastructure", "Hire Date": "2026-09-01", "Total Compensation Package": "9575.00"}
)

# 8. Service Repair Invoice (Image)
create_invoice_image(
    os.path.join(out_dir, "08_Auto_Service_Invoice.png"),
    "PRECISION AUTO REPAIR INVOICE",
    [("Synthetic Oil Change & Filter", 89.95), ("Front Brake Pads Replacement", 249.95), ("Wheel Alignment Service", 119.95)],
    {"Work Order ID": "WO-55102", "Vehicle": "2024 Toyota RAV4", "VIN": "4T1B11HK5RU99102", "Subtotal": "459.85", "Tax": "36.79", "Total Amount": "496.64"}
)

# 9. Purchase Order (CSV Document)
csv_path = os.path.join(out_dir, "09_Enterprise_Purchase_Order.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["PO Number", "Vendor Name", "Item Code", "Quantity", "Unit Price", "Total Price"])
    w.writerow(["PO-2026-99", "Industrial Supplies Co", "IND-901", "50", "120.00", "6000.00"])
    w.writerow(["PO-2026-99", "Industrial Supplies Co", "IND-902", "20", "250.00", "5000.00"])
print(f"Created {csv_path}")

# 10. Utility Bill (Excel Document)
excel_path = os.path.join(out_dir, "10_City_Power_Utility_Bill.xlsx")
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Utility Billing Statement"
ws.append(["Account Number", "Customer Name", "Billing Period", "kWh Consumed", "Rate per kWh", "Total Charge"])
ws.append(["ACC-883019", "Elena Rostova", "Aug 15 - Sep 15 2026", "840", "$0.14", "$117.60"])
wb.save(excel_path)
print(f"Created {excel_path}")

print("\n10 Test Documents Ready in test_docs/")
