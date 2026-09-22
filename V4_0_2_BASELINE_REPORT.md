# v4.0.2 Benchmark Report (BASELINE)

## Summary Metrics

- **Total Documents Benchmarked**: 50
- **Total Expected Ground Truth Fields**: 200
- **Correct Fields**: 195
- **Incorrect Fields**: 4
- **Missing Fields**: 1
- **Hallucinated Fields**: 12
- **Overall Field Accuracy**: `97.50%`
- **Independent Field Accuracy (Class A & B)**: `97.47%`
- **HITL Rate**: `4.00%` (2/50)
- **Average Latency**: `6.13s` / document

## Provenance Breakdown

| Source Class | Provenance Description | Total Fields | Correct | Accuracy |
|---|---|---|---|---|
| Class A | Source Class A (Real Reference) | 54 | 49 | `90.74%` |
| Class B | Source Class B (Annotated Fixture) | 144 | 144 | `100.00%` |
| Class C | Source Class C (Project Fixture) | 2 | 2 | `100.00%` |

## Confidence Calibration Bucketing

| Confidence Band | Total Fields | Correct Fields | Measured Accuracy |
|---|---|---|---|
| `0-50%` | 0 | 0 | `0.00%` |
| `50-70%` | 0 | 0 | `0.00%` |
| `70-80%` | 12 | 12 | `100.00%` |
| `80-90%` | 4 | 4 | `100.00%` |
| `90-95%` | 146 | 141 | `96.58%` |
| `95-100%` | 38 | 38 | `100.00%` |

## Per-Document Execution Breakdown

| Document ID | Filename | Class | Status | Fields | Accuracy | Latency |
|---|---|---|---|---|---|---|
| None | `01_Tech_Hardware_Invoice.png` | Class B | Completed | 6 | `100.0%` | `4.17s` |
| None | `02_FreshMart_Grocery_Receipt.png` | Class B | Completed | 6 | `100.0%` | `5.15s` |
| None | `03_Global_Logistics_Manifest.png` | Class B | Completed | 5 | `100.0%` | `5.15s` |
| None | `04_Annual_Property_Tax.png` | Class B | Completed | 5 | `100.0%` | `6.29s` |
| None | `05_Diagnostic_Lab_Invoice.png` | Class B | Completed | 4 | `100.0%` | `4.17s` |
| None | `06_Bistro_Dinner_Bill.png` | Class B | Completed | 6 | `100.0%` | `4.13s` |
| None | `07_Employee_Onboarding_Record.png` | Class B | Completed | 5 | `100.0%` | `4.17s` |
| None | `08_Auto_Service_Invoice.png` | Class B | Completed | 6 | `100.0%` | `5.16s` |
| None | `09_Enterprise_Purchase_Order.csv` | Class B | Completed | 2 | `100.0%` | `3.09s` |
| None | `10_City_Power_Utility_Bill.xlsx` | Class B | Completed | 6 | `100.0%` | `3.28s` |
| None | `MedicalBill.png` | Class A | WaitingForReview | 9 | `100.0%` | `4.15s` |
| None | `test_bill.png` | Class A | Completed | 5 | `0.0%` | `4.15s` |
| None | `13_Cloud_Hosting_Invoice.png` | Class B | Completed | 4 | `100.0%` | `4.17s` |
| None | `14_Coffee_Shop_Receipt.png` | Class B | Completed | 3 | `100.0%` | `4.14s` |
| None | `15_Freight_Shipping_Order.csv` | Class B | Completed | 4 | `100.0%` | `3.15s` |
| None | `16_Water_Utility_Statement.xlsx` | Class B | Completed | 3 | `100.0%` | `3.12s` |
| None | `17_Legal_Services_Bill.png` | Class B | Completed | 4 | `100.0%` | `4.12s` |
| None | `18_Dental_Clinic_Statement.png` | Class B | Completed | 4 | `100.0%` | `4.21s` |
| None | `19_Software_License_PO.csv` | Class B | Completed | 3 | `100.0%` | `3.08s` |
| None | `20_Telecom_Monthly_Bill.xlsx` | Class B | Completed | 3 | `100.0%` | `4.15s` |
| None | `21_Adversarial_Missing_Fields.png` | Class B | Completed | 2 | `100.0%` | `3.08s` |
| None | `22_Adversarial_Math_Mismatch.png` | Class B | WaitingForReview | 3 | `100.0%` | `10.2s` |
| None | `23_Adversarial_Conflicting_Dates.png` | Class B | Completed | 2 | `100.0%` | `3.11s` |
| None | `24_Corporate_Travel_Receipt.png` | Class B | Completed | 3 | `100.0%` | `3.12s` |
| None | `25_Warehouse_Inventory_Manifest.csv` | Class B | Completed | 2 | `100.0%` | `2.14s` |
| None | `26_Equipment_Rental_Invoice.png` | Class B | Completed | 3 | `100.0%` | `4.12s` |
| None | `27_Pharma_Supply_Invoice.png` | Class B | Completed | 3 | `100.0%` | `5.15s` |
| None | `28_Construction_Materials_PO.xlsx` | Class B | Completed | 3 | `100.0%` | `3.17s` |
| None | `29_MultiPage_Stitched_Invoice.png` | Class B | Completed | 2 | `100.0%` | `3.14s` |
| None | `30_Legacy_Project_Fixture.png` | Class C | Completed | 2 | `100.0%` | `4.13s` |
| DOC-031 | `31_Real_Hospital_Statement.png` | Class A | Completed | 6 | `100.0%` | `9.18s` |
| DOC-032 | `32_Real_Hotel_Folio.png` | Class A | Completed | 6 | `100.0%` | `23.35s` |
| DOC-033 | `33_Real_Utility_Tax_Notice.png` | Class A | Completed | 4 | `100.0%` | `11.18s` |
| DOC-034 | `34_Real_Corporate_PO.png` | Class A | Completed | 4 | `100.0%` | `8.16s` |
| DOC-035 | `35_Real_Shipping_Bill_Lading.png` | Class A | Completed | 4 | `100.0%` | `9.21s` |
| DOC-036 | `36_Real_Pharmacy_Rx_Bill.png` | Class A | Completed | 5 | `100.0%` | `7.19s` |
| DOC-037 | `37_Real_Automotive_Repair_Invoice.png` | Class A | Completed | 6 | `100.0%` | `8.17s` |
| DOC-038 | `38_Real_Telecom_Wireless_Bill.png` | Class A | Completed | 5 | `100.0%` | `7.22s` |
| DOC-039 | `39_Cloud_Infrastructure_Monthly_Invoice.png` | Class B | Completed | 6 | `100.0%` | `7.18s` |
| DOC-040 | `40_Restaurant_Catering_Receipt.png` | Class B | Completed | 6 | `100.0%` | `10.19s` |
| DOC-041 | `41_Industrial_Steel_PO.csv` | Class B | Completed | 3 | `100.0%` | `5.17s` |
| DOC-042 | `42_Gas_Electric_Utility_Statement.xlsx` | Class B | Completed | 3 | `100.0%` | `5.1s` |
| DOC-043 | `43_Surgical_Clinic_Invoice.png` | Class B | Completed | 4 | `100.0%` | `14.25s` |
| DOC-044 | `44_Executive_Airport_Shuttle_Receipt.png` | Class B | Completed | 4 | `100.0%` | `15.25s` |
| DOC-045 | `45_Heavy_Equipment_Lease_Manifest.csv` | Class B | Completed | 3 | `100.0%` | `5.18s` |
| DOC-046 | `46_Commercial_Property_Insurance_Bill.xlsx` | Class B | Completed | 3 | `100.0%` | `6.26s` |
| DOC-047 | `47_Adversarial_Unusual_Currency_Format.png` | Class B | Completed | 2 | `100.0%` | `7.19s` |
| DOC-048 | `48_Adversarial_Zero_Line_Items.png` | Class B | Completed | 2 | `100.0%` | `8.18s` |
| DOC-049 | `49_Adversarial_Duplicate_Subtotals.png` | Class B | Completed | 3 | `100.0%` | `7.17s` |
| DOC-050 | `50_MultiPage_Cross_Table_Invoice.png` | Class B | Completed | 3 | `100.0%` | `7.14s` |
