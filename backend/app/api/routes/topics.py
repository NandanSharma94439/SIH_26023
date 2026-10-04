"""
Topic Intelligence API Routes
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Endpoints:
- GET /api/topics/summary          — Full topic + keyword analysis (all docs or one)
- GET /api/topics/word-cloud       — Word cloud data points only
- GET /api/topics/documents/{id}   — Per-document topic analysis
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status

from app.schemas.topics import (
    TopicSummaryResponse,
    DocumentTopicResponse,
    WordCloudItem,
)
from app.services.topics.service import topic_intelligence_service

router = APIRouter(prefix="/api/topics", tags=["Topic Intelligence"])


@router.get(
    "/summary",
    response_model=TopicSummaryResponse,
    summary="Get full topic and keyword analysis across all or one document",
)
async def get_topic_summary(
    document_id: Optional[str] = Query(
        None,
        description="Optional document UUID to scope analysis to a single document",
    ),
) -> TopicSummaryResponse:
    """
    Analyzes all processed geological and mining documents and returns:
    - Top keywords with frequency and TF-IDF relevance scores
    - Detected topics with associated keywords and document provenance
    - Word cloud data
    - Summary telemetry (document count, topic count, keyword count)
    """
    try:
        return topic_intelligence_service.get_summary(document_id=document_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Topic analysis failed: {str(e)}",
        )


@router.get(
    "/word-cloud",
    response_model=List[WordCloudItem],
    summary="Get word cloud data for all or one document",
)
async def get_word_cloud(
    document_id: Optional[str] = Query(
        None,
        description="Optional document UUID to scope word cloud to a single document",
    ),
) -> List[WordCloudItem]:
    """
    Returns a ranked list of word cloud data points (text + visual weight 1-100)
    derived from actual document content. Suitable for SVG/canvas word cloud rendering.
    """
    try:
        return topic_intelligence_service.get_word_cloud_data(document_id=document_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Word cloud generation failed: {str(e)}",
        )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentTopicResponse,
    summary="Get topic intelligence for a specific document",
)
async def get_document_topics(document_id: str) -> DocumentTopicResponse:
    """
    Returns document-specific keyword extraction and topic identification.
    IDF weighting still uses the full corpus for correct relative scoring.
    """
    try:
        result = topic_intelligence_service.get_document_topics(document_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found.",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document topic analysis failed: {str(e)}",
        )
