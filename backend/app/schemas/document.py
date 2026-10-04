from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    block_index: int = 0
    bbox: List[float] = Field(default_factory=list, description="[x0, y0, x1, y1] coordinates")
    text: str = ""
    block_type: str = "text"  # 'text', 'table', 'image', 'heading'


class TableCell(BaseModel):
    row: int
    col: int
    text: str
    is_header: bool = False


class ExtractedTable(BaseModel):
    table_index: int = 0
    num_rows: int = 0
    num_cols: int = 0
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    bbox: Optional[List[float]] = None


class DocumentPage(BaseModel):
    page_number: int
    text: str
    char_count: int = 0
    word_count: int = 0
    dimensions: Dict[str, float] = Field(default_factory=dict, description="e.g. {'width': 595.0, 'height': 842.0}")
    blocks: List[TextBlock] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)
    ocr_applied: bool = False
    ocr_confidence: Optional[float] = None
    ocr_error: Optional[str] = None


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_type: str  # 'pdf', 'docx', 'xlsx', 'png', 'tiff', etc.
    mime_type: str
    file_size_bytes: int
    total_pages: int = 0
    status: str = "processed"  # 'processing', 'processed', 'failed'
    uploaded_at: datetime
    processing_time_ms: int = 0
    ocr_pages_count: int = 0
    has_tables: bool = False
    preview_text: Optional[str] = None
    error_message: Optional[str] = None
    content_hash: Optional[str] = None


class DocumentDetailResponse(BaseModel):
    metadata: DocumentMetadata
    storage_path: str
    pages_count: int


class DocumentPagesResponse(BaseModel):
    document_id: str
    total_pages: int
    pages: List[DocumentPage]


class DocumentUploadResponse(BaseModel):
    success: bool = True
    message: str = "Document uploaded and parsed successfully"
    document: DocumentMetadata
    pages_preview: List[DocumentPage] = Field(default_factory=list)
    already_exists: bool = False
