"""
v5.0 Tenant Knowledge & Pattern Intelligence Building Engine
Stores reusable schema templates, field alias dictionaries, and domain taxonomies
isolated per tenant across processing jobs.
"""
import uuid
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class TenantKnowledgePattern:
    pattern_id: str
    tenant_id: str
    category: str
    schema_fields: List[str]
    field_aliases: Dict[str, List[str]]
    sample_count: int = 1
    updated_at: float = field(default_factory=time.time)

class KnowledgeBuildingEngine:
    """
    Tenant-isolated knowledge store that learns domain patterns and field aliases over time.
    """

    def __init__(self):
        # tenant_id -> {category -> TenantKnowledgePattern}
        self._store: Dict[str, Dict[str, TenantKnowledgePattern]] = {}

    def index_document_result(
        self,
        tenant_id: str,
        category: str,
        extracted_fields: Dict[str, Any]
    ) -> TenantKnowledgePattern:
        """
        Indexes extracted keys and updates tenant knowledge patterns.
        """
        if tenant_id not in self._store:
            self._store[tenant_id] = {}

        category_upper = (category or "GENERAL").upper()
        current_fields = list(extracted_fields.keys())

        if category_upper in self._store[tenant_id]:
            pattern = self._store[tenant_id][category_upper]
            # Merge fields
            merged_fields = list(set(pattern.schema_fields + current_fields))
            pattern.schema_fields = merged_fields
            pattern.sample_count += 1
            pattern.updated_at = time.time()
            return pattern
        else:
            pattern = TenantKnowledgePattern(
                pattern_id=f"pat-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                category=category_upper,
                schema_fields=current_fields,
                field_aliases={k: [k.lower(), k.replace("_", " ")] for k in current_fields},
                sample_count=1
            )
            self._store[tenant_id][category_upper] = pattern
            return pattern

    def get_tenant_pattern(self, tenant_id: str, category: str) -> Optional[TenantKnowledgePattern]:
        """
        Retrieves learned pattern for a given tenant and category.
        """
        tenant_dict = self._store.get(tenant_id, {})
        return tenant_dict.get(category.upper())

knowledge_building_engine = KnowledgeBuildingEngine()
