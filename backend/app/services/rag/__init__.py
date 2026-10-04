"""
RAG Service Package for Mining Document Intelligence
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)
"""

from app.services.rag.chunking import DomainAwareChunker
from app.services.rag.embeddings import GeminiEmbeddingService
from app.services.rag.vector_store import FAISSVectorStore
from app.services.rag.service import GroundedRAGService, rag_service, RAGKnowledgeBaseService

__all__ = [
    "DomainAwareChunker",
    "GeminiEmbeddingService",
    "FAISSVectorStore",
    "GroundedRAGService",
    "RAGKnowledgeBaseService",
    "rag_service",
]
