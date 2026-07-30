import io
import json
import csv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def generate_dynamic_excel(extracted_items: list[dict]) -> bytes:
    """
    Creates a styled Excel workbook (.xlsx) dynamically from ANY list of extracted documents.
    Dynamic headers are automatically generated from extracted fields.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Extracted Intelligence Data"
    
    if not extracted_items:
        ws.append(["No Data Extracted"])
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()
        
    # Gather all unique keys across all items
    headers = ["File Name", "Document Category", "Confidence Score"]
    field_keys = []
    
    for item in extracted_items:
        fields = item.get("extractedFields", {})
        for k in fields.keys():
            if k not in field_keys:
                field_keys.append(k)
                
    headers.extend([k.replace('_', ' ').title() for k in field_keys])
    
    # 1. Header Styling
    ws.append(headers)
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    # 2. Append Data Rows
    for row_idx, item in enumerate(extracted_items, 2):
        fields = item.get("extractedFields", {})
        row = [
            item.get("fileName", f"Document_{row_idx-1}"),
            item.get("category", "General Document"),
            f"{item.get('confidence', 95.0)}%"
        ]
        for fk in field_keys:
            row.append(str(fields.get(fk, "") or ""))
        ws.append(row)
        
        # Apply zebra striping and borders
        row_fill = PatternFill(start_color="F8FAFC" if row_idx % 2 == 0 else "FFFFFF", fill_type="solid")
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_num)
            cell.fill = row_fill
            cell.border = thin_border
            cell.font = Font(name="Calibri", size=10)
            
    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
        
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def generate_dynamic_csv(extracted_items: list[dict]) -> str:
    """Generates CSV text content dynamically."""
    if not extracted_items:
        return "File Name,Category,Status\n"
        
    field_keys = []
    for item in extracted_items:
        for k in item.get("extractedFields", {}).keys():
            if k not in field_keys:
                field_keys.append(k)
                
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = ["File Name", "Category", "Confidence"] + field_keys
    writer.writerow(headers)
    
    for item in extracted_items:
        fields = item.get("extractedFields", {})
        row = [
            item.get("fileName", ""),
            item.get("category", ""),
            item.get("confidence", 95.0)
        ] + [fields.get(fk, "") for fk in field_keys]
        writer.writerow(row)
        
    return output.getvalue()
