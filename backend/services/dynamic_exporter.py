import io
import json
import csv
import re
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from backend.services.data_sanitizer import clean_field_value, normalize_field

def generate_dynamic_excel(extracted_items: list[dict]) -> bytes:
    """
    Creates a professionally styled Excel workbook (.xlsx) dynamically from ANY list of extracted documents.
    Formatted like a trained business analyst report:
    - Pure blank cells for missing/invalid data (zero 'null'/'None'/'N/A' strings)
    - Type-based column alignments (Numbers right, IDs center, Text left)
    - Numeric cell types for sums and formulas
    - Professional slate headers, subtle zebra rows, and auto column widths
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Extracted Intelligence Data"
    
    if not extracted_items:
        ws.append(["No Data Extracted"])
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()
        
    field_keys = []
    for item in extracted_items:
        fields = item.get("fields") or item.get("extractedFields") or {}
        for k in fields.keys():
            if k not in field_keys:
                field_keys.append(k)
                
    if field_keys:
        headers = [k.replace('_', ' ').title() for k in field_keys]
    else:
        headers = ["File Name", "Document Category", "Confidence Score"]
    
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
        
    # 2. Append Data Rows with Professional Alignment & Numeric Types
    for row_idx, item in enumerate(extracted_items, 2):
        fields = item.get("fields") or item.get("extractedFields") or {}
        row_fill = PatternFill(start_color="F8FAFC" if row_idx % 2 == 0 else "FFFFFF", fill_type="solid")
        
        if field_keys:
            for col_idx, fk in enumerate(field_keys, 1):
                raw_v = fields.get(fk)
                norm_v = normalize_field(fk, raw_v)
                cell = ws.cell(row=row_idx, column=col_idx)
                
                if not norm_v:
                    cell.value = None
                else:
                    # Attempt numeric conversion for sums/financial metrics
                    fk_lower = fk.lower()
                    if any(num_k in fk_lower for num_k in ["amount", "cost", "price", "total", "salary", "revenue", "quantity", "units"]):
                        try:
                            if '.' in norm_v:
                                cell.value = float(norm_v)
                                cell.number_format = '#,##0.00'
                            else:
                                cell.value = int(norm_v)
                                cell.number_format = '#,##0'
                        except ValueError:
                            cell.value = norm_v
                    else:
                        cell.value = norm_v

                cell.fill = row_fill
                cell.border = thin_border
                cell.font = Font(name="Calibri", size=10)
                
                # Determine Alignment by Data Type & Field Key
                fk_lower = fk.lower()
                if any(num_k in fk_lower for num_k in ["amount", "cost", "price", "total", "salary", "revenue", "quantity", "units"]):
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif any(id_k in fk_lower for id_k in ["number", "id", "code", "mobile", "phone", "date", "vehicle"]):
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")
        else:
            c1 = ws.cell(row=row_idx, column=1, value=clean_field_value(item.get("fileName", f"Document_{row_idx-1}")))
            c2 = ws.cell(row=row_idx, column=2, value=clean_field_value(item.get("category", "General Document")))
            c3 = ws.cell(row=row_idx, column=3, value=f"{item.get('confidence', 95.0)}%")
            for c in (c1, c2, c3):
                c.fill = row_fill
                c.border = thin_border
                c.font = Font(name="Calibri", size=10)
            c1.alignment = Alignment(horizontal="left", vertical="center")
            c2.alignment = Alignment(horizontal="left", vertical="center")
            c3.alignment = Alignment(horizontal="center", vertical="center")
            
    # Auto-adjust column widths cleanly
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 5, 14)

    # 3. Check for Nested Line Items and generate secondary sheet if present
    all_line_items = []
    for row_idx, item in enumerate(extracted_items, 1):
        fields = item.get("fields") or item.get("extractedFields") or {}
        items_arr = fields.get("line_items") or fields.get("lineItems") or item.get("line_items") or []
        if isinstance(items_arr, list) and items_arr:
            for sub_item in items_arr:
                if isinstance(sub_item, dict):
                    entry = {"documentRow": row_idx}
                    entry.update(sub_item)
                    all_line_items.append(entry)

    if all_line_items:
        ws_items = wb.create_sheet(title="Line Items Detail")
        li_keys = []
        for li in all_line_items:
            for k in li.keys():
                if k not in li_keys:
                    li_keys.append(k)

        li_headers = [k.replace('_', ' ').title() for k in li_keys]
        ws_items.append(li_headers)

        header_fill_blue = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        for col_num, header in enumerate(li_headers, 1):
            cell = ws_items.cell(row=1, column=col_num)
            cell.fill = header_fill_blue
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for r_i, li in enumerate(all_line_items, 2):
            r_fill = PatternFill(start_color="F8FAFC" if r_i % 2 == 0 else "FFFFFF", fill_type="solid")
            for c_i, k in enumerate(li_keys, 1):
                val = li.get(k)
                cell = ws_items.cell(row=r_i, column=c_i)
                if val is None or val == "":
                    cell.value = None
                else:
                    k_lower = k.lower()
                    if any(nk in k_lower for nk in ["amount", "cost", "price", "total", "quantity", "qty", "rate", "tax"]):
                        try:
                            cell.value = float(val) if '.' in str(val) else int(val)
                        except ValueError:
                            cell.value = str(val)
                    else:
                        cell.value = str(val)

                cell.fill = r_fill
                cell.border = thin_border
                cell.font = Font(name="Calibri", size=10)

        for col in ws_items.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws_items.column_dimensions[col_letter].width = max(max_len + 5, 14)

    # 4. Table Intelligence Summary & Validation Report Sheets
    has_table_data = any(item.get("tableResult") or item.get("table_result") for item in extracted_items)
    if has_table_data:
        ws_tbl = wb.create_sheet(title="Table Summary")
        tbl_headers = ["Table ID", "Page", "Columns Count", "Rows Count", "Math Valid", "Structural Valid", "Confidence", "Anomalies Count"]
        ws_tbl.append(tbl_headers)

        header_fill_purple = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
        for col_num, header in enumerate(tbl_headers, 1):
            cell = ws_tbl.cell(row=1, column=col_num)
            cell.fill = header_fill_purple
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        r_counter = 2
        for item in extracted_items:
            tbl_res = item.get("tableResult") or item.get("table_result") or {}
            if not tbl_res:
                continue
            t_struct = tbl_res.get("table_structure") or {}
            val_rep = tbl_res.get("validation_report") or {}

            ws_tbl.cell(row=r_counter, column=1, value=str(tbl_res.get("table_id", "tbl-1")))
            ws_tbl.cell(row=r_counter, column=2, value=int(tbl_res.get("page_number", 1)))
            ws_tbl.cell(row=r_counter, column=3, value=len(t_struct.get("columns", [])))
            ws_tbl.cell(row=r_counter, column=4, value=len(t_struct.get("rows", [])))
            ws_tbl.cell(row=r_counter, column=5, value="YES" if val_rep.get("numeric_validity") else "NO")
            ws_tbl.cell(row=r_counter, column=6, value="YES" if val_rep.get("structural_validity") else "NO")
            ws_tbl.cell(row=r_counter, column=7, value=f"{tbl_res.get('confidence', 0.9)*100:.1f}%")
            ws_tbl.cell(row=r_counter, column=8, value=len(val_rep.get("anomalies", [])))

            for c_i in range(1, 9):
                c = ws_tbl.cell(row=r_counter, column=c_i)
                c.border = thin_border
                c.font = Font(name="Calibri", size=10)
                c.alignment = Alignment(horizontal="center", vertical="center")
            r_counter += 1

        for col in ws_tbl.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws_tbl.column_dimensions[col_letter].width = max(max_len + 5, 14)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def generate_dynamic_csv(extracted_items: list[dict]) -> str:
    """Generates clean CSV text content dynamically."""
    if not extracted_items:
        return "File Name,Category,Status\n"
        
    field_keys = []
    for item in extracted_items:
        fields = item.get("fields") or item.get("extractedFields") or {}
        for k in fields.keys():
            if k not in field_keys:
                field_keys.append(k)
                
    output = io.StringIO()
    writer = csv.writer(output)
    
    if field_keys:
        headers = [k.replace('_', ' ').title() for k in field_keys]
        writer.writerow(headers)
        for item in extracted_items:
            fields = item.get("fields") or item.get("extractedFields") or {}
            row = [normalize_field(fk, fields.get(fk)) for fk in field_keys]
            writer.writerow(row)
    else:
        headers = ["File Name", "Category", "Confidence"]
        writer.writerow(headers)
        for item in extracted_items:
            writer.writerow([
                clean_field_value(item.get("fileName", "")),
                clean_field_value(item.get("category", "")),
                item.get("confidence", 95.0)
            ])
            
    return output.getvalue()
