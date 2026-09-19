"""
Pydantic Data Models for Phase 3 — Advanced Extraction Accuracy, Evidence, Consensus & Self-Correction.
Defines schemas for ExtractionEvidence, FieldEvidence, CandidateValue, ConsensusResult, DocumentQualityAssessment, ErrorTaxonomyReport, and AccuracyMetrics.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x1: float = Field(0.0, description="Top-left X coordinate")
    y1: float = Field(0.0, description="Top-left Y coordinate")
    x2: float = Field(0.0, description="Bottom-right X coordinate")
    y2: float = Field(0.0, description="Bottom-right Y coordinate")

class CandidateValue(BaseModel):
    source_type: str = Field(..., description="OCR, VISION, LLM, PDF_TEXT, TABLE_STRUCTURE, REGEX, CALCULATION, INFERENCE, HUMAN_CORRECTION")
    raw_value: str = Field("", description="Raw value from source")
    normalized_value: Any = Field(None, description="Normalized typed value")
    confidence: float = Field(1.0, description="Source extraction confidence score")
    bounding_box: Optional[BoundingBox] = None
    page_number: int = Field(1, description="Source page number")

class ExtractionEvidence(BaseModel):
    document_id: str = Field(..., description="Unique document ID")
    page_number: int = Field(1, description="1-indexed page number")
    chunk_number: int = Field(1, description="Chunk number")
    table_id: Optional[str] = None
    row_id: Optional[str] = None
    column_id: Optional[str] = None
    field_name: str = Field(..., description="Field key name")
    raw_value: str = Field("", description="Unprocessed raw extracted string")
    normalized_value: Any = Field(None, description="Cleaned/parsed value in native type")
    source_type: str = Field("OCR+VISION", description="OCR, VISION, LLM, PDF_TEXT, TABLE_STRUCTURE, REGEX, CALCULATION, INFERENCE, HUMAN_CORRECTION")
    bounding_box: Optional[BoundingBox] = None
    source_text: str = Field("", description="Surrounding raw text snippet")
    extraction_method: str = Field("DIRECT", description="DIRECT, CONSENSUS, REEXTRACTION, DERIVED")
    timestamp: str = Field("", description="ISO timestamp")
    evidence_status: str = "AVAILABLE"  # AVAILABLE, UNAVAILABLE, INFERRED

class FieldEvidence(BaseModel):
    field_key: str
    selected_value: Any
    confidence: float = 1.0
    evidence: ExtractionEvidence
    candidate_values: List[CandidateValue] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    is_trusted: bool = True

class ConsensusResult(BaseModel):
    field_key: str
    reconciled_value: Any
    consensus_score: float = 1.0
    agreed_sources: List[str] = Field(default_factory=list)
    disagreed_sources: List[str] = Field(default_factory=list)
    candidates: List[CandidateValue] = Field(default_factory=list)
    has_conflict: bool = False
    conflict_resolution: Optional[str] = None

class DocumentQualityAssessment(BaseModel):
    resolution_dpi: int = Field(300, description="Estimated resolution DPI")
    blur_score: float = Field(0.0, description="Blur level score (0.0 clear -> 1.0 blurry)")
    contrast_score: float = Field(1.0, description="Contrast level (0.0 low -> 1.0 high)")
    skew_angle: float = Field(0.0, description="Rotation skew angle")
    text_density: float = Field(0.0, description="Character density ratio")
    ocr_difficulty: str = Field("LOW", description="LOW, MEDIUM, HIGH, EXTREME")
    recommended_strategy: str = Field("STANDARD", description="STANDARD, CONSENSUS, HIGH_RES_CROP, HITL_ESCALATE")

class ErrorTaxonomyReport(BaseModel):
    error_category: str = Field(..., description="OCR_ERROR, VISION_ERROR, TEXT_EXTRACTION_ERROR, CELL_ALIGNMENT_ERROR, ROW_ALIGNMENT_ERROR, COLUMN_SHIFT, MERGED_CELL_ERROR, HEADER_MAPPING_ERROR, TYPE_ERROR, NORMALIZATION_ERROR, MISSING_VALUE, DUPLICATE_VALUE, CROSS_PAGE_CONFLICT, ARITHMETIC_MISMATCH, LOW_SOURCE_QUALITY, MODEL_DISAGREEMENT, SCHEMA_MISMATCH, UNKNOWN_ERROR")
    severity: str = Field("LOW", description="LOW, MEDIUM, HIGH, CRITICAL")
    field_key: Optional[str] = None
    page_number: int = Field(1)
    description: str = Field("")
    evidence_snippet: Optional[str] = None
    recommended_action: str = Field("NONE")

class AccuracyMetrics(BaseModel):
    document_classification_accuracy: float = 100.0
    table_detection_accuracy: float = 100.0
    row_detection_accuracy: float = 100.0
    column_detection_accuracy: float = 100.0
    cell_extraction_accuracy: float = 100.0
    field_extraction_accuracy: float = 100.0
    header_mapping_accuracy: float = 100.0
    numeric_accuracy: float = 100.0
    cross_page_consistency: float = 100.0
    evidence_coverage: float = 100.0
    consensus_accuracy: float = 100.0
    reextraction_recovery_rate: float = 100.0
