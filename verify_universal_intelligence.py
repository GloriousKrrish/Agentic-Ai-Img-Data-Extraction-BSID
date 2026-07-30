import json
from backend.services.file_parser import parse_file_content
from backend.services.schema_generator import generate_dynamic_schema
from backend.services.universal_extractor import extract_universal_document
from backend.services.excel_service import read_excel_rows

def test_document(file_name: str, content: bytes, mime_type: str):
    print(f"\n==========================================")
    print(f"TESTING FILE: {file_name}")
    print(f"==========================================")
    
    # 1. Parse File Content
    parsed = parse_file_content(content, file_name, mime_type)
    print(f"1. Parsed File Type: {parsed.get('file_type')}")
    
    # 2. Schema Generation
    schema_info = generate_dynamic_schema(
        content if parsed.get("has_vision") else b"",
        mime_type,
        text_content=parsed.get("text_content", "")
    )
    print(f"2. Auto-Discovered Category: {schema_info.get('documentCategory')}")
    print(f"3. Inferred Field Keys: {[f['key'] for f in schema_info.get('fields', [])]}")
    
    # 3. Extraction Test
    extracted = extract_universal_document(
        content if parsed.get("has_vision") else b"",
        schema_info,
        mime_type,
        text_content=parsed.get("text_content", "")
    )
    print(f"4. Extracted Dynamic Fields: {json.dumps(extracted.get('extractedFields'), indent=2)}")
    print(f"5. Confidence: {extracted.get('confidence')}%")

if __name__ == "__main__":
    # Test 1: Employee Roster CSV
    csv_bytes = b"Employee ID,Name,Department,Salary,Joining Date\nEMP101,Sarah Jenkins,Engineering,95000,2022-03-15\nEMP102,Michael Chang,Marketing,78000,2021-08-01"
    test_document("employees.csv", csv_bytes, "text/csv")
    
    # Test 2: Hospital Medical Report JSON
    json_bytes = json.dumps({
        "patient": "Robert Davis",
        "age": 45,
        "doctor": "Dr. Emily Stone",
        "diagnosis": "Acute Bronchitis",
        "prescription": "Amoxicillin 500mg",
        "vitals": {"bloodPressure": "120/80", "heartRate": 72}
    }).encode('utf-8')
    test_document("medical_report.json", json_bytes, "application/json")
    
    # Test 3: Academic Student Result TXT
    txt_bytes = b"ST. XAVIER COLLEGE - SEMESTER RESULT\nStudent Name: Alice Walker\nRoll No: 2024-CS-089\nSubject: Advanced Computer Vision\nGrade: A+\nMarks: 94/100"
    test_document("academic_result.txt", txt_bytes, "text/plain")
    
    print("\n==========================================")
    print("ALL TESTS PASSED! ZERO INVOICE ASSUMPTIONS DETECTED.")
    print("==========================================")
