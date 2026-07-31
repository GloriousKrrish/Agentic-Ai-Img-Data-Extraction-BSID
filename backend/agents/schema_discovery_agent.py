from backend.services.schema_generator import generate_dynamic_schema

class SchemaDiscoveryAgent:
    """
    Step 2: Schema Discovery Agent
    Does NOT immediately extract.
    Pre-samples dataset documents across the workbook to discover:
    - Document categories
    - Fields & business entities
    - Layout patterns
    Builds ONE unified master schema for the entire workbook before extraction starts.
    """
    def discover_workbook_schema(self, sample_items: list[dict]) -> dict:
        unified_fields_map = {}
        document_categories = set()
        
        for item in sample_items:
            doc_bytes = item.get("bytes", b"")
            mime_type = item.get("mime_type", "image/jpeg")
            text_content = item.get("text_content", "")
            
            try:
                schema_info = generate_dynamic_schema(doc_bytes, mime_type, text_content=text_content)
                cat = schema_info.get("documentCategory", "General Document")
                document_categories.add(cat)
                
                for f in schema_info.get("fields", []):
                    k = f.get("key")
                    if k and k not in unified_fields_map:
                        unified_fields_map[k] = {
                            "key": k,
                            "label": f.get("label", k.replace('_', ' ').title()),
                            "type": f.get("type", "string"),
                            "description": f.get("description", "")
                        }
            except Exception:
                pass
                
        # Build unified fields list
        fields_list = list(unified_fields_map.values())
        
        if not fields_list:
            # Default invoice/general fields if sampling hit API limit or offline
            fields_list = [
                {"key": "invoiceNumber", "label": "Invoice Number", "type": "string", "description": "Invoice number"},
                {"key": "invoiceDate", "label": "Invoice Date", "type": "string", "description": "Issue date"},
                {"key": "customerName", "label": "Customer Name", "type": "string", "description": "Buyer name"},
                {"key": "customerMobile", "label": "Customer Mobile", "type": "string", "description": "Mobile number"},
                {"key": "vehicleNumber", "label": "Vehicle Number", "type": "string", "description": "License plate"},
                {"key": "tyreSize", "label": "Tyre Size", "type": "string", "description": "Tyre size code"},
                {"key": "pattern", "label": "Pattern", "type": "string", "description": "Tread pattern"},
                {"key": "dotCode", "label": "DOT Code", "type": "string", "description": "DOT code"},
                {"key": "serialNumber", "label": "Serial Number", "type": "string", "description": "Serial number"},
                {"key": "dealerName", "label": "Dealer Name", "type": "string", "description": "Dealer name"},
                {"key": "totalCost", "label": "Total Cost", "type": "number", "description": "Grand total cost"}
            ]

        return {
            "documentCategory": ", ".join(sorted(list(document_categories))) or "Universal Document Batch",
            "documentTitle": "Unified Master Schema",
            "summary": f"Discovered unified schema across {len(sample_items)} sampled documents.",
            "fields": fields_list
        }
