import os
import io
import json
import csv
from openpyxl import Workbook
import requests

BASE_URL = "http://127.0.0.1:8000"

def create_sample_files():
    samples = {}
    
    # 1. Invoice (Text/JSON simulation)
    invoice_text = """
    TAX INVOICE
    Invoice No: INV-99823
    Date: 2026-07-20
    Vendor: Apex Electronics Ltd
    Customer: Global Tech Solutions
    Total Amount: $4,500.00
    Payment Terms: Net 30
    """
    samples['Invoice.txt'] = ('Invoice.txt', invoice_text.encode('utf-8'), 'text/plain')

    # 2. Employee Excel
    wb = Workbook()
    ws = wb.active
    ws.append(["Employee ID", "Full Name", "Department", "Designation", "Salary"])
    ws.append(["EMP-101", "Alice Smith", "Engineering", "Senior Developer", "$120,000"])
    ws.append(["EMP-102", "Bob Jones", "Marketing", "Marketing Manager", "$95,000"])
    excel_buf = io.BytesIO()
    wb.save(excel_buf)
    excel_buf.seek(0)
    samples['Employee_Records.xlsx'] = ('Employee_Records.xlsx', excel_buf.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # 3. Hospital PDF / Text
    hospital_text = """
    CITY GENERAL HOSPITAL - ADMISSION RECORD
    Patient ID: PAT-77341
    Patient Name: Eleanor Rigby
    Age: 42
    Attending Doctor: Dr. Marcus Vance
    Diagnosis: Acute Appendicitis
    Room Number: 402B
    Admission Date: 2026-07-15
    """
    samples['Hospital_Record.txt'] = ('Hospital_Record.txt', hospital_text.encode('utf-8'), 'text/plain')

    # 4. Sales CSV
    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow(["Order ID", "Region", "Product Line", "Units Sold", "Revenue"])
    writer.writerow(["ORD-5001", "North America", "Cloud Servers", "25", "$50,000"])
    writer.writerow(["ORD-5002", "Europe", "Security Suite", "100", "$30,000"])
    samples['Sales_Data.csv'] = ('Sales_Data.csv', csv_buf.getvalue().encode('utf-8'), 'text/csv')

    # 5. Random JSON
    json_data = {
        "sensorId": "SENSOR-882A",
        "location": "Warehouse 4",
        "temperatureCelsius": 22.4,
        "humidityPercentage": 45,
        "status": "OPERATIONAL",
        "lastMaintenance": "2026-06-01"
    }
    samples['Sensor_Telemetry.json'] = ('Sensor_Telemetry.json', json.dumps(json_data).encode('utf-8'), 'application/json')

    # 6. Resume
    resume_text = """
    CURRICULUM VITAE
    Candidate Name: Sarah Jenkins
    Email: sarah.jenkins@email.com
    Degree: B.S. Computer Science
    Years of Experience: 8
    Core Competencies: Machine Learning, Python, FastAPI, React
    Current Employer: CyberTech Inc
    """
    samples['Resume_Sarah_Jenkins.txt'] = ('Resume_Sarah_Jenkins.txt', resume_text.encode('utf-8'), 'text/plain')

    # 7. Student Result
    result_text = """
    SPRINGFIELD ACADEMY - ANNUAL REPORT CARD
    Student Roll No: STU-2026-088
    Student Name: Michael Scott
    Grade Level: 10th Grade
    Mathematics: 95/100 (A+)
    Science: 91/100 (A)
    English: 88/100 (B+)
    Overall GPA: 3.85
    Final Result: PASSED WITH DISTINCTION
    """
    samples['Student_Result.txt'] = ('Student_Result.txt', result_text.encode('utf-8'), 'text/plain')

    return samples

def run_verification():
    print("\n=======================================================")
    print("UNIVERSAL AI DOCUMENT INTELLIGENCE SYSTEM VERIFICATION")
    print("=======================================================\n")

    samples = create_sample_files()
    results = {}

    for file_key, (filename, content_bytes, content_type) in samples.items():
        print(f"Testing Upload & Extraction for: [{filename}]")
        files = {'file': (filename, content_bytes, content_type)}
        
        try:
            res = requests.post(f"{BASE_URL}/api/extract/universal", files=files, timeout=45)
            if res.status_code == 200:
                data = res.json()
                schema = data.get("schema", [])
                rows = data.get("rows", [])
                
                print(f"  Status: SUCCESS")
                print(f"  Category: {data.get('documentCategory')}")
                print(f"  Title: {data.get('documentTitle')}")
                print(f"  Discovered Columns ({len(schema)}): {[col['label'] for col in schema]}")
                if rows and len(rows) > 0:
                    print(f"  Sample Extracted Fields: {rows[0].get('fields')}")
                
                # Check for lingering invoice fields
                invoice_keys = {"customerName", "vehicleNumber", "tyreSize", "pattern", "dot", "dealerName"}
                extracted_keys = {col["key"].lower() for col in schema}
                matched_invoice_keys = invoice_keys.intersection(extracted_keys)
                
                if "Invoice" not in filename and matched_invoice_keys:
                    print(f"  WARNING: Detected legacy invoice keys in non-invoice document: {matched_invoice_keys}")
                else:
                    print(f"  Clean dynamic schema verified!")
                    
                results[filename] = {
                    "schema": schema,
                    "rows": rows,
                    "clean": len(matched_invoice_keys) == 0 or "Invoice" in filename
                }
            else:
                print(f"  HTTP Error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"  Request Exception: {e}")

        print("-" * 55)

if __name__ == "__main__":
    run_verification()
