"""
Structured Data Models for Agentic Universal Data Extraction Engine
Defines Pydantic schemas for input analysis, planning, capabilities, execution logs, validation, and confidence scoring.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class InputAnalysis(BaseModel):
    input_type: str = Field(..., description="File extension or type (pdf, png, jpg, csv, xlsx, docx, json, zip, txt)")
    mime_type: str = Field("application/octet-stream", description="MIME type")
    file_size: int = Field(0, description="Size in bytes")
    page_count: int = Field(1, description="Total pages or sheets")
    is_scanned: bool = Field(False, description="True if document appears to be scanned image/PDF")
    contains_tables: bool = Field(False, description="True if tabular layout detected")
    contains_images: bool = Field(False, description="True if visual imagery present")
    contains_text: bool = Field(True, description="True if text content present")
    language: str = Field("en", description="Primary detected language code")
    document_type: str = Field("general", description="Inferred category (invoice, medical, kyc, academic, financial, legal, dataset)")
    document_domain: str = Field("general", description="Domain classification")
    complexity: str = Field("medium", description="Low, medium, or high complexity score")
    requires_ocr: bool = Field(False, description="True if OCR pass is recommended")
    requires_vision: bool = Field(True, description="True if Multimodal Vision LLM is recommended")
    requires_chunking: bool = Field(False, description="True if document exceeds single token context limit")
    requires_table_extraction: bool = Field(False, description="True if nested tabular data extraction is needed")
    estimated_extraction_difficulty: float = Field(0.5, description="Difficulty score 0.0 to 1.0")

class ProcessingStrategy(BaseModel):
    parallelizable: bool = True
    chunk_required: bool = False
    cross_page_context: bool = False
    pyramid_slicing: bool = False

class ValidationStrategy(BaseModel):
    ocr_consensus: bool = True
    arithmetic_validation: bool = True
    schema_validation: bool = True
    confidence_threshold: float = 0.70

class RetryPolicy(BaseModel):
    enabled: bool = True
    max_retries: int = 2
    max_replans: int = 2

class HumanReviewPolicy(BaseModel):
    enabled: bool = True
    threshold: float = 0.70

class ValidationReport(BaseModel):
    is_valid: bool = True
    passed_rules: List[str] = Field(default_factory=list)
    failed_rules: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

class ExtractionPlan(BaseModel):

    plan_id: str = Field(..., description="UUID for extraction plan")
    input_classification: Dict[str, Any] = Field(default_factory=dict)
    schema_strategy: str = Field("dynamic", description="dynamic, preset, or user_defined")
    target_category: str = Field("General Document")
    agents: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    processing_strategy: ProcessingStrategy = Field(default_factory=ProcessingStrategy)
    validation_strategy: ValidationStrategy = Field(default_factory=ValidationStrategy)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    human_review: HumanReviewPolicy = Field(default_factory=HumanReviewPolicy)
    output_formats: List[str] = Field(default_factory=lambda: ["json", "xlsx", "csv"])
    created_at: str = Field("")

class AgentCapability(BaseModel):
    name: str = Field(..., description="Agent or tool unique identifier")
    label: str = Field(..., description="Human readable display name")
    purpose: str = Field(..., description="Functional purpose description")
    supported_input_types: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    required_parameters: List[str] = Field(default_factory=list)
    output_type: str = Field("dict")
    can_run_parallel: bool = True
    retry_on_failure: bool = True

class ExecutionStepLog(BaseModel):
    step_id: str
    agent_or_tool: str
    stage: str
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, REPLANNING
    start_time: float
    end_time: Optional[float] = None
    input_summary: str = ""
    output_summary: str = ""
    error: Optional[str] = None
    confidence: float = 0.0
    retry_count: int = 0
    validation_passed: bool = True

class FieldConfidence(BaseModel):
    field_key: str
    value: Any
    confidence: float = 0.0
    sources: List[str] = Field(default_factory=list)  # e.g., ["vision", "ocr", "math_audit"]
    validations: Dict[str, bool] = Field(default_factory=dict)  # {"schema": True, "regex": True, "arithmetic": True}

class ConfidenceScoreCard(BaseModel):
    overall_confidence: float = 0.0
    is_trusted: bool = True
    field_scores: Dict[str, FieldConfidence] = Field(default_factory=dict)
    flagged_fields: List[str] = Field(default_factory=list)
    human_review_required: bool = False
    review_reasons: List[str] = Field(default_factory=list)
