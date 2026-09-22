# v4.0.2 Benchmark Report (BASELINE)

## Summary Metrics

- **Total Documents Benchmarked**: 30
- **Total Expected Ground Truth Fields**: 118
- **Correct Fields**: 113
- **Incorrect Fields**: 4
- **Missing Fields**: 1
- **Hallucinated Fields**: 12
- **Overall Field Accuracy**: `95.76%`
- **Independent Field Accuracy (Class A & B)**: `95.69%`
- **HITL Rate**: `6.67%` (2/30)
- **Average Latency**: `4.70s` / document

## Provenance Breakdown

| Source Class | Provenance Description | Total Fields | Correct | Accuracy |
|---|---|---|---|---|
| Class A | Source Class A (Real Reference) | 14 | 9 | `64.29%` |
| Class B | Source Class B (Annotated Fixture) | 102 | 102 | `100.00%` |
| Class C | Source Class C (Project Fixture) | 2 | 2 | `100.00%` |

## Confidence Calibration Bucketing

| Confidence Band | Total Fields | Correct Fields | Measured Accuracy |
|---|---|---|---|
| `0-50%` | 0 | 0 | `0.00%` |
| `50-70%` | 0 | 0 | `0.00%` |
| `70-80%` | 12 | 12 | `100.00%` |
| `80-90%` | 0 | 0 | `0.00%` |
| `90-95%` | 80 | 75 | `93.75%` |
| `95-100%` | 26 | 26 | `100.00%` |

## Per-Document Execution Breakdown

| Document ID | Filename | Class | Status | Fields | Accuracy | Latency |
|---|---|---|---|---|---|---|
| None | `01_Tech_Hardware_Invoice.png` | Class B | Completed | 6 | `100.0%` | `4.12s` |
| None | `02_FreshMart_Grocery_Receipt.png` | Class B | Completed | 6 | `100.0%` | `4.1s` |
| None | `03_Global_Logistics_Manifest.png` | Class B | Completed | 5 | `100.0%` | `4.08s` |
| None | `04_Annual_Property_Tax.png` | Class B | Completed | 5 | `100.0%` | `16.15s` |
| None | `05_Diagnostic_Lab_Invoice.png` | Class B | Completed | 4 | `100.0%` | `4.07s` |
| None | `06_Bistro_Dinner_Bill.png` | Class B | Completed | 6 | `100.0%` | `4.75s` |
| None | `07_Employee_Onboarding_Record.png` | Class B | Completed | 5 | `100.0%` | `4.08s` |
| None | `08_Auto_Service_Invoice.png` | Class B | Completed | 6 | `100.0%` | `6.11s` |
| None | `09_Enterprise_Purchase_Order.csv` | Class B | Completed | 2 | `100.0%` | `4.15s` |
| None | `10_City_Power_Utility_Bill.xlsx` | Class B | Completed | 6 | `100.0%` | `3.13s` |
| None | `MedicalBill.png` | Class A | WaitingForReview | 9 | `100.0%` | `6.15s` |
| None | `test_bill.png` | Class A | Completed | 5 | `0.0%` | `5.11s` |
| None | `13_Cloud_Hosting_Invoice.png` | Class B | Completed | 4 | `100.0%` | `5.12s` |
| None | `14_Coffee_Shop_Receipt.png` | Class B | Completed | 3 | `100.0%` | `4.12s` |
| None | `15_Freight_Shipping_Order.csv` | Class B | Completed | 4 | `100.0%` | `3.14s` |
| None | `16_Water_Utility_Statement.xlsx` | Class B | Completed | 3 | `100.0%` | `9.17s` |
| None | `17_Legal_Services_Bill.png` | Class B | Completed | 4 | `100.0%` | `5.12s` |
| None | `18_Dental_Clinic_Statement.png` | Class B | Completed | 4 | `100.0%` | `4.1s` |
| None | `19_Software_License_PO.csv` | Class B | Completed | 3 | `100.0%` | `3.15s` |
| None | `20_Telecom_Monthly_Bill.xlsx` | Class B | Completed | 3 | `100.0%` | `3.08s` |
| None | `21_Adversarial_Missing_Fields.png` | Class B | Completed | 2 | `100.0%` | `3.1s` |
| None | `22_Adversarial_Math_Mismatch.png` | Class B | WaitingForReview | 3 | `100.0%` | `4.06s` |
| None | `23_Adversarial_Conflicting_Dates.png` | Class B | Completed | 2 | `100.0%` | `4.09s` |
| None | `24_Corporate_Travel_Receipt.png` | Class B | Completed | 3 | `100.0%` | `4.08s` |
| None | `25_Warehouse_Inventory_Manifest.csv` | Class B | Completed | 2 | `100.0%` | `4.14s` |
| None | `26_Equipment_Rental_Invoice.png` | Class B | Completed | 3 | `100.0%` | `4.14s` |
| None | `27_Pharma_Supply_Invoice.png` | Class B | Completed | 3 | `100.0%` | `4.11s` |
| None | `28_Construction_Materials_PO.xlsx` | Class B | Completed | 3 | `100.0%` | `3.12s` |
| None | `29_MultiPage_Stitched_Invoice.png` | Class B | Completed | 2 | `100.0%` | `3.2s` |
| None | `30_Legacy_Project_Fixture.png` | Class C | Completed | 2 | `100.0%` | `4.07s` |
