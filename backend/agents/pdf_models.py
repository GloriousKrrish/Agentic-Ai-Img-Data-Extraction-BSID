"""
Pydantic Models for Advanced Multi-Page & Scanned PDF Intelligence Engine.
Defines schemas for page classification, PDF document analysis, cross-page context, and aggregated document results.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class PageClassification(BaseModel):
    page_number: int = Field(..., description="1-indexed page number")
    type: str = Field("TEXT", description="TEXT, SCANNED, MIXED, TABLE_HEAVY, IMAGE_HEAVY, BLANK, UNKNOWN")
    text_density: float = Field(0.0, description="Characters per unit area")
    image_density: float = Field(0.0, description="Image coverage ratio")
    char_count: int = Field(0, description="Raw character count")
    image_count: int = Field(0, description="Number of embedded images")
    requires_ocr: bool = Field(False, description="True if page requires OCR rendering")
    requires_vision: bool = Field(True, description="True if Vision model pass is recommended")
    contains_table: bool = Field(False, description="True if table structure detected")
    rotation: int = Field(0, description="Page rotation angle (0, 90, 180, 270)")
    width: float = Field(0.0, description="Page width in points")
    height: float = Field(0.0, description="Page height in points")

class PDFDocumentAnalysis(BaseModel):
    total_pages: int = Field(1, description="Total document page count")
    scanned_page_count: int = Field(0, description="Count of scanned image pages")
    text_page_count: int = Field(0, description="Count of native text pages")
    table_page_count: int = Field(0, description="Count of pages with tables")
    is_scanned_pdf: bool = Field(False, description="True if majority of pages are scanned")
    is_mixed_pdf: bool = Field(False, description="True if document contains mix of text and scanned pages")
    recommended_chunk_size: int = Field(5, description="Adaptive chunk size for processing")
    estimated_complexity: str = Field("medium", description="low, medium, high")
    page_classifications: List[PageClassification] = Field(default_factory=list)

class PageMeta(BaseModel):
    page_number: int
    role: str = "content"  # header, content, line_items, totals, appendix
    contains_header_data: bool = False
    contains_totals: bool = False

class CrossPageContext(BaseModel):
    document_id: str = Field(..., description="Unique document ID")
    total_pages: int = Field(1, description="Total pages")
    document_type: str = Field("invoice", description="Inferred category")
    pages_meta: List[PageMeta] = Field(default_factory=list)
    global_header_fields: Dict[str, Any] = Field(default_factory=dict)
    known_keys: List[str] = Field(default_factory=list)

class ExtractedPageResult(BaseModel):
    page_number: int
    chunk_number: int = 1
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    status: str = "COMPLETED"
    is_scanned: bool = False

class AggregatedDocumentResult(BaseModel):
    document_fields: Dict[str, Any] = Field(default_factory=dict)
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    page_references: Dict[str, List[int]] = Field(default_factory=dict)
    field_sources: Dict[str, str] = Field(default_factory=dict)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    overall_confidence: float = 0.0
    status: str = "COMPLETED"
