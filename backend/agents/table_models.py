"""
Pydantic Data Models for Advanced Table Intelligence & Structural Table Understanding (Phase 2).
Defines schemas for TableRegion, TableColumn, TableRow, TableCell, TableStructure, TableValidationReport, TableAnomaly, and TableExecutionResult.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x1: float = Field(0.0, description="Top-left X coordinate")
    y1: float = Field(0.0, description="Top-left Y coordinate")
    x2: float = Field(0.0, description="Bottom-right X coordinate")
    y2: float = Field(0.0, description="Bottom-right Y coordinate")

class TableRegion(BaseModel):
    table_id: str = Field(..., description="Unique table ID")
    page_number: int = Field(1, description="1-indexed page number")
    chunk_number: int = Field(1, description="Chunk number in multi-page processing")
    bounding_box: BoundingBox = Field(default_factory=BoundingBox)
    rotation: int = Field(0, description="Rotation angle")
    confidence: float = Field(0.0, description="Table detection confidence score")
    table_type: str = Field("STANDARD", description="STANDARD, BORDERLESS, SCANNED, FINANCIAL, NESTED, ROTATED")

class TableColumn(BaseModel):
    column_id: str = Field(..., description="Unique column ID")
    name: str = Field(..., description="Original raw column header name")
    display_name: str = Field("", description="Formatted display name")
    semantic_type: str = Field("string", description="string, integer, float, currency, percentage, date, boolean, identifier")
    position: int = Field(0, description="0-indexed column position")
    x_start: float = Field(0.0, description="Start X coordinate")
    x_end: float = Field(0.0, description="End X coordinate")
    confidence: float = Field(1.0, description="Column mapping confidence")

class TableCell(BaseModel):
    cell_id: str = Field(..., description="Unique cell ID")
    row_id: str = Field(..., description="Parent row ID")
    column_id: str = Field(..., description="Parent column ID")
    raw_value: str = Field("", description="Unprocessed raw string extracted from document")
    normalized_value: Any = Field(None, description="Cleaned/parsed value in native type")
    data_type: str = Field("string", description="string, integer, float, currency, percentage, date, boolean, unknown")
    bounding_box: Optional[BoundingBox] = None
    row_span: int = Field(1, description="Row span count for merged cells")
    column_span: int = Field(1, description="Column span count for merged cells")
    confidence: float = Field(1.0, description="Cell extraction confidence score")
    source_page: int = Field(1, description="Source page number")
    source_region: Optional[Dict[str, float]] = None

class TableRow(BaseModel):
    row_id: str = Field(..., description="Unique row ID")
    row_type: str = Field("DATA", description="HEADER, DATA, SUBTOTAL, TOTAL, FOOTER, NOTE, CONTINUATION, UNKNOWN")
    page_number: int = Field(1, description="Page number where row resides")
    position: int = Field(0, description="0-indexed row position within table")
    confidence: float = Field(1.0, description="Row detection confidence")
    cells: List[TableCell] = Field(default_factory=list)
    raw_text: str = Field("", description="Concatenated raw line text")

class TableStructure(BaseModel):
    table_id: str = Field(..., description="Unique table ID")
    headers: List[str] = Field(default_factory=list, description="Raw column headers")
    columns: List[TableColumn] = Field(default_factory=list, description="Structured column metadata")
    rows: List[TableRow] = Field(default_factory=list, description="Ordered table rows")
    merged_cells: List[Dict[str, Any]] = Field(default_factory=list, description="Merged cell descriptors")
    nested_tables: List[Dict[str, Any]] = Field(default_factory=list, description="Nested child table structures")
    continuation_info: Optional[Dict[str, Any]] = Field(None, description="Multi-page continuation metadata")
    source_pages: List[int] = Field(default_factory=lambda: [1], description="Source page numbers")
    confidence: float = Field(1.0, description="Overall table structure confidence")

class TableAnomaly(BaseModel):
    anomaly_type: str = Field(..., description="COLUMN_SHIFT, MISSING_CELL, ARITHMETIC_MISMATCH, DUPLICATE_HEADER, UNEXPECTED_TYPE, BROKEN_CONTINUATION")
    severity: str = Field("LOW", description="LOW, MEDIUM, HIGH, CRITICAL")
    description: str = Field("", description="Human readable description")
    affected_row_id: Optional[str] = None
    affected_column_id: Optional[str] = None
    suggested_fix: Optional[str] = None

class TableValidationReport(BaseModel):
    structural_validity: bool = Field(True, description="True if table structure is coherent")
    numeric_validity: bool = Field(True, description="True if arithmetic checks pass")
    row_validity: bool = Field(True, description="True if row types and boundaries are valid")
    column_validity: bool = Field(True, description="True if column alignment is consistent")
    formula_consistency: bool = Field(True, description="True if calculated fields match sum formulas")
    duplicate_headers: List[str] = Field(default_factory=list)
    missing_cells: int = Field(0, description="Count of missing/null cells")
    anomalies: List[TableAnomaly] = Field(default_factory=list)
    confidence: float = Field(1.0, description="Overall validation confidence score")

class TableExecutionResult(BaseModel):
    table_id: str
    page_number: int
    table_structure: TableStructure
    validation_report: TableValidationReport
    reconstructed_rows: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 1.0
    status: str = "COMPLETED"
