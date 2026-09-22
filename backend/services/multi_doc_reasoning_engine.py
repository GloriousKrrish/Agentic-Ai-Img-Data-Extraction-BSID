"""
v5.0 Multi-Document Reasoning & Entity Cross-Referencing Engine
Enables multi-document correlation, entity matching, cross-document discrepancy detection,
and batch-level consensus scoring across document sets.
"""
import uuid
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

def _normalize_key(k: str) -> str:
    return k.lower().replace("_", "").replace("-", "").replace(" ", "")

@dataclass
class DocumentExtractionResult:
    doc_id: str
    filename: str
    category: str
    extracted_fields: Dict[str, Any]
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 100.0

@dataclass
class EntityMatch:
    entity_key: str
    common_value: Any
    doc_ids: List[str]
    is_unanimous: bool

@dataclass
class EntityDiscrepancy:
    entity_key: str
    variations: Dict[str, Any]  # doc_id -> value
    severity: str  # "HIGH", "MEDIUM", "LOW"
    recommendation: str

@dataclass
class CrossDocumentCorrelation:
    correlation_id: str
    tenant_id: str
    total_documents: int
    matched_entities: List[EntityMatch] = field(default_factory=list)
    discrepancies: List[EntityDiscrepancy] = field(default_factory=list)
    consensus_score: float = 100.0
    batch_summary: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

class MultiDocReasoningEngine:
    """
    Analyzes multiple extracted document results to find cross-document correlations,
    entity matches, and conflicting field values across batches.
    """

    KEY_ENTITY_PATTERNS = [
        "invoice_number", "invoicenumber", "po_number", "ponumber",
        "vendor_name", "vendorname", "customer_name", "patient_name",
        "total_amount", "subtotal", "tax", "date", "invoice_date"
    ]

    def correlate_documents(
        self,
        doc_results: List[DocumentExtractionResult],
        tenant_id: str
    ) -> CrossDocumentCorrelation:
        """
        Correlates extracted fields across multiple documents in a batch or collection.
        """
        if not doc_results:
            return CrossDocumentCorrelation(
                correlation_id=f"corr-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                total_documents=0,
                consensus_score=100.0
            )

        if len(doc_results) == 1:
            doc = doc_results[0]
            return CrossDocumentCorrelation(
                correlation_id=f"corr-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                total_documents=1,
                consensus_score=doc.confidence,
                batch_summary={
                    "doc_count": 1,
                    "categories": [doc.category],
                    "total_line_items": len(doc.line_items)
                }
            )

        # Map fields across all documents using normalized key lookup
        field_maps: Dict[str, Dict[str, Any]] = {}  # norm_key -> {doc_id: raw_val}
        key_display_names: Dict[str, str] = {}

        for doc in doc_results:
            for raw_k, val in doc.extracted_fields.items():
                norm_k = _normalize_key(raw_k)
                if norm_k not in field_maps:
                    field_maps[norm_k] = {}
                    key_display_names[norm_k] = raw_k
                field_maps[norm_k][doc.doc_id] = val

        matched_entities: List[EntityMatch] = []
        discrepancies: List[EntityDiscrepancy] = []

        for norm_k, val_map in field_maps.items():
            display_k = key_display_names[norm_k]
            unique_vals = set()
            for v in val_map.values():
                if v is not None and str(v).strip() != "":
                    unique_vals.add(str(v).strip().lower())

            doc_ids_present = list(val_map.keys())

            if len(unique_vals) == 1 and len(doc_ids_present) > 1:
                matched_entities.append(EntityMatch(
                    entity_key=display_k,
                    common_value=list(val_map.values())[0],
                    doc_ids=doc_ids_present,
                    is_unanimous=(len(doc_ids_present) == len(doc_results))
                ))
            elif len(unique_vals) > 1 and len(doc_ids_present) > 1:
                # Discrepancy found across documents for shared key
                severity = "HIGH" if any(p in norm_k for p in ["amount", "total", "subtotal", "tax"]) else "MEDIUM"
                discrepancies.append(EntityDiscrepancy(
                    entity_key=display_k,
                    variations=val_map,
                    severity=severity,
                    recommendation=f"Review inconsistent values for '{display_k}' across {len(doc_ids_present)} documents."
                ))

        # Calculate consensus score
        total_shared_keys = len([k for k, v in field_maps.items() if len(v) > 1])
        if total_shared_keys > 0:
            consensus_score = round(max(0.0, 100.0 - (len(discrepancies) * (100.0 / total_shared_keys))), 1)
        else:
            consensus_score = 100.0

        categories = list(set(d.category for d in doc_results))
        total_items = sum(len(d.line_items) for d in doc_results)

        return CrossDocumentCorrelation(
            correlation_id=f"corr-{uuid.uuid4().hex[:8]}",
            tenant_id=tenant_id,
            total_documents=len(doc_results),
            matched_entities=matched_entities,
            discrepancies=discrepancies,
            consensus_score=consensus_score,
            batch_summary={
                "doc_count": len(doc_results),
                "categories": categories,
                "total_shared_keys": total_shared_keys,
                "matched_key_count": len(matched_entities),
                "discrepancy_count": len(discrepancies),
                "total_line_items": total_items
            }
        )

multi_doc_reasoning_engine = MultiDocReasoningEngine()
