"""
Pydantic Schemas for Grounded RAG Assistant & Vector Knowledge Base
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RAGChunkMetadata(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    file_type: str
    page_number: int
    section: Optional[str] = "General"
    source_type: Optional[str] = "text"  # "text", "table", "ocr"
    char_count: int = 0
    word_count: int = 0
    dimensions: Optional[Dict[str, float]] = None
    bbox: Optional[List[float]] = None


class RAGChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: RAGChunkMetadata


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="User question about mining/geological documents")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of relevant chunks to retrieve")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional document filter")


class RAGSource(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    file_type: str
    page_number: int
    section: Optional[str] = None
    source_type: Optional[str] = "text"
    text: str
    score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    dimensions: Optional[Dict[str, float]] = None
    bbox: Optional[List[float]] = None


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    evidence_found: bool
    model_used: str
    sources_count: int
    sources: List[RAGSource]
    latency_ms: int


class RAGIndexResponse(BaseModel):
    success: bool = True
    message: str
    indexed_documents: int
    new_chunks_indexed: int
    total_vectors_in_index: int
    index_path: str


class RAGStatusResponse(BaseModel):
    status: str
    vector_count: int
    dimensions: int
    embedding_model: str
    llm_model: str
    gemini_configured: bool
    index_exists: bool
    indexed_documents_count: int
