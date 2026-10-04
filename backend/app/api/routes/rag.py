"""
RAG API Endpoints: Grounded Querying & Index Management
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGIndexResponse,
    RAGStatusResponse,
)
from app.services.rag.service import rag_service

router = APIRouter(prefix="/api/rag", tags=["RAG & Knowledge Base"])


@router.get(
    "/status",
    response_model=RAGStatusResponse,
    summary="Get RAG knowledge base & vector store telemetry",
)
async def get_rag_status():
    """Returns vector count, embedding model, index existence, and Gemini configuration status."""
    return rag_service.get_status()


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="Query the vector knowledge base with grounded citations",
)
async def query_knowledge_base(request: RAGQueryRequest):
    """
    Executes semantic vector search and synthesizes a grounded answer via Gemini
    with strict page-level source citations.
    """
    try:
        return rag_service.query(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during query processing: {str(e)}",
        )


@router.post(
    "/index/{document_id}",
    response_model=RAGIndexResponse,
    summary="Index a single processed document into FAISS vector store",
)
async def index_document(document_id: str):
    """Chunks and embeds a processed document, inserting vectors into the FAISS index."""
    try:
        return rag_service.index_document(document_id)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {str(e)}",
        )


@router.post(
    "/index-all",
    response_model=RAGIndexResponse,
    summary="Index all unindexed processed documents into FAISS vector store",
)
async def index_all_documents():
    """Indexes all registered processed documents that have not yet been vectorized."""
    try:
        return rag_service.index_all_documents()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed during bulk indexing: {str(e)}",
        )
