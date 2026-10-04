"""
Topic Intelligence Schemas
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Pydantic schemas for:
- Keyword extraction results with frequency and relevance scoring
- Topic identification with associated keywords and document provenance
- Word cloud data for frontend visualization
- Topic Intelligence summary response
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class KeywordItem(BaseModel):
    """A single extracted keyword with frequency and relevance score."""
    word: str = Field(..., description="The extracted keyword or term")
    count: int = Field(..., description="Raw occurrence count across analyzed text")
    relevance: float = Field(..., description="Normalized TF-IDF-inspired relevance score (0.0–1.0)")
    documents: List[str] = Field(default_factory=list, description="List of source document filenames containing this keyword")


class TopicItem(BaseModel):
    """A detected thematic topic from document corpus analysis."""
    name: str = Field(..., description="Human-readable topic label")
    score: float = Field(..., description="Topic relevance/confidence score (0.0–1.0)")
    keywords: List[str] = Field(..., description="Top keywords defining this topic")
    document_count: int = Field(default=0, description="Number of documents contributing to this topic")
    document_names: List[str] = Field(default_factory=list, description="Names of contributing source documents")


class WordCloudItem(BaseModel):
    """A single word cloud data point with display weight."""
    text: str = Field(..., description="The word or term to display")
    value: float = Field(..., description="Display weight/size (normalized 1–100)")
    count: int = Field(..., description="Raw occurrence count")


class TopicSummaryResponse(BaseModel):
    """Complete Topic Intelligence summary for all or one document."""
    total_documents_analyzed: int = Field(..., description="Total number of documents analyzed")
    total_topics_detected: int = Field(..., description="Total number of topics identified")
    total_keywords_extracted: int = Field(..., description="Total distinct keywords extracted")
    top_topic: Optional[str] = Field(None, description="Name of the highest-scoring topic")
    top_keyword: Optional[str] = Field(None, description="Most frequent keyword across the corpus")
    topics: List[TopicItem] = Field(default_factory=list, description="List of identified topics")
    top_keywords: List[KeywordItem] = Field(default_factory=list, description="Top 50 keywords by relevance")
    word_cloud: List[WordCloudItem] = Field(default_factory=list, description="Word cloud data points")
    scope: str = Field(default="all", description="Analysis scope: 'all' or a document filename/ID")


class DocumentTopicResponse(BaseModel):
    """Topic Intelligence result for a single specific document."""
    document_id: str = Field(..., description="Document UUID")
    document_filename: str = Field(..., description="Document filename")
    topics: List[TopicItem] = Field(default_factory=list)
    top_keywords: List[KeywordItem] = Field(default_factory=list)
    word_cloud: List[WordCloudItem] = Field(default_factory=list)
    total_topics_detected: int = Field(default=0)
    total_keywords_extracted: int = Field(default=0)
