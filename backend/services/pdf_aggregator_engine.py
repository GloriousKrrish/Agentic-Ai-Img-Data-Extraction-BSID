"""
Phase 9 & 10: PDF Aggregator Engine & Cross-Page Table Continuation
Consolidates extracted page-level results, stitches cross-page continuation tables,
deduplicates repeated headers/footers, and detects cross-page field conflicts.
"""
from typing import List, Dict, Any
from backend.agents.pdf_models import (
    ExtractedPageResult, AggregatedDocumentResult
)

class PDFAggregatorEngine:
    def aggregate_pages(self, page_results: List[ExtractedPageResult]) -> AggregatedDocumentResult:
        if not page_results:
            return AggregatedDocumentResult(overall_confidence=0.0, status="FAILED")

        sorted_pages = sorted(page_results, key=lambda x: x.page_number)
        doc_fields: Dict[str, Any] = {}
        field_sources: Dict[str, str] = {}
        page_refs: Dict[str, List[int]] = {}
        all_line_items: List[Dict[str, Any]] = []
        conflicts: List[Dict[str, Any]] = []

        seen_item_keys = set()
        overall_confs = []

        for p in sorted_pages:
            p_num = p.page_number
            p_fields = p.extracted_fields or {}
            p_items = p.line_items or []
            overall_confs.append(p.confidence)

            # 1. Process Field Values
            for k, val in p_fields.items():
                if k in ["line_items", "lineItems", "serNo", "invoiceImageLink"]:
                    continue

                val_str = str(val or "").strip()
                if not val_str or val_str.lower() in ["null", "none", "n/a"]:
                    continue

                if k not in doc_fields:
                    doc_fields[k] = val_str
                    field_sources[k] = f"Page {p_num}"
                    page_refs[k] = [p_num]
                else:
                    existing_val = str(doc_fields[k]).strip()
                    if p_num not in page_refs[k]:
                        page_refs[k].append(p_num)

                    # Conflict detection for different non-empty values
                    if existing_val.lower() != val_str.lower():
                        # Standardize numbers for soft check
                        clean_exist = existing_val.replace(',', '').replace('$', '').replace('₹', '')
                        clean_val = val_str.replace(',', '').replace('$', '').replace('₹', '')

                        if clean_exist != clean_val:
                            conflicts.append({
                                "field_key": k,
                                "existing_val": existing_val,
                                "existing_source": field_sources[k],
                                "conflicting_val": val_str,
                                "conflicting_source": f"Page {p_num}"
                            })

            # 2. Cross-Page Table Continuation (Line Items)
            if p_items and isinstance(p_items, list):
                for item in p_items:
                    if isinstance(item, dict):
                        # Add page and chunk metadata
                        item_copy = {"page_number": p_num, "chunk_number": p.chunk_number}
                        item_copy.update(item)

                        # Deduplicate exact duplicate items across page breaks
                        item_sig = " | ".join([f"{k}:{v}" for k, v in item.items() if k not in ["page_number", "chunk_number"]])
                        if item_sig not in seen_item_keys:
                            seen_item_keys.add(item_sig)
                            all_line_items.append(item_copy)

        avg_conf = round(sum(overall_confs) / float(len(overall_confs)), 1) if overall_confs else 85.0
        if conflicts:
            avg_conf = max(avg_conf - 10.0, 50.0)

        # Attach stitched line items to document fields
        if all_line_items:
            doc_fields["line_items"] = all_line_items

        return AggregatedDocumentResult(
            document_fields=doc_fields,
            line_items=all_line_items,
            page_references=page_refs,
            field_sources=field_sources,
            conflicts=conflicts,
            overall_confidence=avg_conf,
            status="COMPLETED" if not conflicts else "WAITING_FOR_HUMAN_REVIEW"
        )

pdf_aggregator_engine = PDFAggregatorEngine()
