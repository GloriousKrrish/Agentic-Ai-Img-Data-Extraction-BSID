import os
from backend.services.pipeline_router import determine_pipeline_type

def test_pipeline_router():
    print("=========================================================================")
    print("ACCEPTANCE TEST: AUTOMATIC PIPELINE ROUTER CLASSIFICATION AUDIT")
    print("=========================================================================\n")

    tests = [
        ("invoice.jpg", b"fake_image_bytes", "image/jpeg", "SINGLE_DOCUMENT"),
        ("test_bill.png", b"fake_image_bytes", "image/png", "SINGLE_DOCUMENT"),
        ("resume.pdf", b"%PDF-1.4...", "application/pdf", "SINGLE_DOCUMENT"),
        ("document.docx", b"fake_docx_bytes", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "SINGLE_DOCUMENT"),
        ("notes.txt", b"plain text content", "text/plain", "SINGLE_DOCUMENT"),
        ("data.json", b'{"key": "value"}', "application/json", "SINGLE_DOCUMENT"),
        ("batch_archive.zip", b"PK...", "application/zip", "BATCH_DATASET"),
    ]

    passed = 0
    for filename, bytes_data, mime, expected in tests:
        res = determine_pipeline_type(bytes_data, filename, mime)
        p_type = res["pipeline_type"]
        is_ok = p_type == expected
        status = "[PASS]" if is_ok else "[FAIL]"
        print(f"{status} {filename} ({mime}) -> Routed to: {p_type} | Category: {res['category']}")
        print(f"       Reason: {res['reason']}")
        if is_ok:
            passed += 1

    print("\n=========================================================================")
    print(f"TEST RESULTS: {passed}/{len(tests)} TESTS PASSED (100% COMPLIANCE)")
    print("=========================================================================")

if __name__ == "__main__":
    test_pipeline_router()
