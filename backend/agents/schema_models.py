"""
Phase 4: Universal Custom Schema Intelligence — Data Models
Defines the full schema definition contract for user-defined extraction schemas.
"""
from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
import uuid
import time


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SchemaFieldType(str, Enum):
    STRING     = "string"
    NUMBER     = "number"
    DATE       = "date"
    BOOLEAN    = "boolean"
    ARRAY      = "array"
    OBJECT     = "object"
    CURRENCY   = "currency"
    PERCENTAGE = "percentage"

class RuleSeverity(str, Enum):
    ERROR   = "error"
    WARNING = "warning"
    INFO    = "info"

class SchemaStrategy(str, Enum):
    DYNAMIC      = "dynamic"
    PRESET       = "preset"
    USER_DEFINED = "user_defined"


# ---------------------------------------------------------------------------
# Schema Field
# ---------------------------------------------------------------------------

class SchemaField(BaseModel):
    key: str = Field(..., description="camelCase unique field identifier")
    label: str = Field(..., description="Human-readable display label")
    field_type: SchemaFieldType = Field(SchemaFieldType.STRING, description="Expected value type")
    required: bool = Field(False, description="True if field must be present for a valid extraction")
    description: str = Field("", description="Extraction guidance / instruction for the AI agent")
    extraction_hint: str = Field("", description="Optional OCR / visual region hint")
    regex_pattern: Optional[str] = Field(None, description="Regex validation pattern for the extracted value")
    min_value: Optional[float] = Field(None, description="Minimum numeric value (for number / currency types)")
    max_value: Optional[float] = Field(None, description="Maximum numeric value (for number / currency types)")
    allowed_values: List[str] = Field(default_factory=list, description="Enumerated allowed values (enum-like constraint)")
    default_value: Optional[Any] = Field(None, description="Default value if field cannot be found in document")
    confidence_threshold: float = Field(0.65, description="Minimum confidence before HITL escalation for this field")

    @field_validator("key")
    @classmethod
    def key_must_be_camel(cls, v: str) -> str:
        return v.strip().replace(" ", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# Schema Table Column / Schema Table
# ---------------------------------------------------------------------------

class SchemaTableColumn(BaseModel):
    key: str = Field(..., description="Column identifier key")
    label: str = Field(..., description="Column display header")
    field_type: SchemaFieldType = Field(SchemaFieldType.STRING)
    required: bool = Field(False)
    description: str = Field("")

class SchemaTable(BaseModel):
    table_id: str = Field(default_factory=lambda: f"tbl-{uuid.uuid4().hex[:6]}")
    label: str = Field(..., description="Table display name")
    description: str = Field("")
    columns: List[SchemaTableColumn] = Field(default_factory=list)
    min_rows: int = Field(0, description="Minimum expected rows (0 = optional)")
    max_rows: Optional[int] = Field(None, description="Maximum rows cap")


# ---------------------------------------------------------------------------
# Cross-Field Validation Rule
# ---------------------------------------------------------------------------

class CrossFieldRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: f"rule-{uuid.uuid4().hex[:6]}")
    formula: str = Field(..., description="Python-evaluable formula referencing field keys, e.g. 'grand_total == subtotal + tax'")
    description: str = Field("", description="Human-readable rule description")
    error_message: str = Field("", description="Message shown when rule fails")
    severity: RuleSeverity = Field(RuleSeverity.WARNING)
    fields_involved: List[str] = Field(default_factory=list, description="List of field keys involved in this rule")


# ---------------------------------------------------------------------------
# Full Extraction Schema
# ---------------------------------------------------------------------------

class ExtractionSchema(BaseModel):
    schema_id: str = Field(default_factory=lambda: f"schema-{uuid.uuid4().hex[:8]}")
    name: str = Field(..., description="Schema name / title")
    version: str = Field("1.0.0", description="Semantic version string")
    domain: str = Field("general", description="Document domain (invoice, medical, kyc, academic, financial, legal, custom)")
    description: str = Field("", description="Schema purpose and usage notes")
    fields: List[SchemaField] = Field(default_factory=list, description="Ordered list of extraction fields")
    tables: List[SchemaTable] = Field(default_factory=list, description="Expected table structures")
    cross_field_rules: List[CrossFieldRule] = Field(default_factory=list, description="Cross-field validation rules")
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    updated_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    created_by: str = Field("user", description="Source: user, nl_converter, json_import, preset")
    tags: List[str] = Field(default_factory=list, description="User-defined tags for search")

    @property
    def required_fields(self) -> List[SchemaField]:
        return [f for f in self.fields if f.required]

    @property
    def optional_fields(self) -> List[SchemaField]:
        return [f for f in self.fields if not f.required]

    def get_field(self, key: str) -> Optional[SchemaField]:
        for f in self.fields:
            if f.key == key:
                return f
        return None


# ---------------------------------------------------------------------------
# Schema Version Record
# ---------------------------------------------------------------------------

class SchemaVersion(BaseModel):
    version_id: str = Field(default_factory=lambda: f"ver-{uuid.uuid4().hex[:6]}")
    schema_id: str = Field(...)
    version: str = Field(...)
    diff_summary: str = Field("", description="Human-readable change summary")
    fields_added: List[str] = Field(default_factory=list)
    fields_removed: List[str] = Field(default_factory=list)
    fields_modified: List[str] = Field(default_factory=list)
    snapshot: Dict[str, Any] = Field(default_factory=dict, description="Full schema snapshot at this version")
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))


# ---------------------------------------------------------------------------
# Schema Validation Results
# ---------------------------------------------------------------------------

class FieldValidationOutcome(BaseModel):
    field_key: str
    value: Any = None
    passed: bool = True
    error: Optional[str] = None
    severity: RuleSeverity = RuleSeverity.ERROR
    confidence: float = Field(1.0, description="Extraction confidence for this field")
    corrected_value: Optional[Any] = None

class CrossFieldRuleOutcome(BaseModel):
    rule_id: str
    formula: str
    passed: bool = True
    error: Optional[str] = None
    severity: RuleSeverity = RuleSeverity.WARNING

class SchemaValidationResult(BaseModel):
    schema_id: str
    schema_name: str
    field_outcomes: List[FieldValidationOutcome] = Field(default_factory=list)
    rule_outcomes: List[CrossFieldRuleOutcome] = Field(default_factory=list)
    missing_required: List[str] = Field(default_factory=list)
    type_failures: List[str] = Field(default_factory=list)
    rule_failures: List[str] = Field(default_factory=list)
    completeness_score: float = Field(0.0, description="Percentage of required fields successfully extracted")
    overall_quality_score: float = Field(0.0, description="Combined schema quality score 0.0-1.0")
    passed: bool = Field(True)
    hitl_required: bool = Field(False)
    hitl_reasons: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Schema Extraction Report (attached to job output)
# ---------------------------------------------------------------------------

class SchemaExtractionReport(BaseModel):
    schema_id: str
    schema_name: str
    schema_version: str
    total_fields: int = 0
    required_fields_count: int = 0
    extracted_fields_count: int = 0
    missing_required: List[str] = Field(default_factory=list)
    type_coercion_applied: List[str] = Field(default_factory=list)
    type_failures: List[str] = Field(default_factory=list)
    cross_field_rules_passed: int = 0
    cross_field_rules_failed: int = 0
    completeness_pct: float = 0.0
    quality_score: float = 0.0
    field_outcomes: List[FieldValidationOutcome] = Field(default_factory=list)
    rule_outcomes: List[CrossFieldRuleOutcome] = Field(default_factory=list)
    hitl_required: bool = False
    hitl_reasons: List[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))


# ---------------------------------------------------------------------------
# Schema Semantic Coverage Analysis
# ---------------------------------------------------------------------------

class FieldCoverage(BaseModel):
    field_key: str
    label: str = Field("", description="Human-readable field label")
    estimated_coverage: float = Field(0.0, description="0.0 - 1.0 likelihood this field exists in the document")
    matching_snippets: List[str] = Field(default_factory=list)
    confidence: float = 0.0

class SchemaCoverageAnalysis(BaseModel):
    schema_id: str
    overall_coverage: float = 0.0
    field_coverages: List[FieldCoverage] = Field(default_factory=list)
    uncoverable_fields: List[str] = Field(default_factory=list)
    document_summary: str = ""
    analyzed_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
