"""
Grounded RAG Assistant & Knowledge Base Service
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Coordinates:
- Ingestion of processed documents into domain-aware chunks.
- Vector generation via Gemini text-embedding-004.
- Persistence and semantic search via FAISS.
- Grounded answer synthesis via Gemini 1.5 with page-level citations.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from google.genai import types

from app.core.config import settings
from app.schemas.document import DocumentMetadata, DocumentPage
from app.schemas.rag import (
    RAGChunk,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGSource,
    RAGIndexResponse,
    RAGStatusResponse,
)
from app.services.documents.db import doc_db
from app.services.rag.chunking import DomainAwareChunker
from app.services.rag.embeddings import GeminiEmbeddingService
from app.services.rag.vector_store import FAISSVectorStore


class GroundedRAGService:
    """Enterprise RAG Service for geological documents and mining reports."""

    def __init__(
        self,
        embedding_service: Optional[GeminiEmbeddingService] = None,
        vector_store: Optional[FAISSVectorStore] = None,
        chunker: Optional[DomainAwareChunker] = None,
    ):
        self.embedding_service = embedding_service or GeminiEmbeddingService()
        self.vector_store = vector_store or FAISSVectorStore()
        self.chunker = chunker or DomainAwareChunker()
        self.llm_model = settings.GEMINI_MODEL

    def get_status(self) -> RAGStatusResponse:
        """Returns the current vector index and Gemini API configuration telemetry."""
        is_configured = self.embedding_service.is_configured
        v_count = self.vector_store.vector_count

        if not is_configured:
            status = "unconfigured"
        elif v_count == 0:
            status = "empty"
        else:
            status = "ready"

        return RAGStatusResponse(
            status=status,
            vector_count=v_count,
            dimensions=FAISSVectorStore.DIMENSION,
            embedding_model=self.embedding_service.model,
            llm_model=self.llm_model,
            gemini_configured=is_configured,
            index_exists=v_count > 0,
            indexed_documents_count=self.vector_store.indexed_documents_count,
        )

    def index_document(self, document_id: str) -> RAGIndexResponse:
        """
        Indexes a single processed document by ID into FAISS:
        1. Reads processed JSON data (with normalized tables).
        2. Generates domain-aware chunks.
        3. Generates real Gemini embeddings.
        4. Adds to FAISS vector store and persists to disk.
        """
        if not self.embedding_service.is_configured:
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env "
                "to generate real embeddings and index documents."
            )

        doc_record = doc_db.get_document(document_id)
        if not doc_record:
            raise FileNotFoundError(f"Document with ID '{document_id}' not found in registry.")

        processed_path = Path(doc_record["processed_path"])
        if not processed_path.exists():
            raise FileNotFoundError(f"Processed document file missing at {processed_path}")

        with open(processed_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = DocumentMetadata(**data["metadata"])
        pages = [DocumentPage(**p) for p in data["pages"]]

        # Generate semantic domain-aware chunks
        chunks = self.chunker.chunk_document(metadata, pages)
        if not chunks:
            return RAGIndexResponse(
                success=True,
                message=f"Document '{metadata.filename}' produced no indexable text.",
                indexed_documents=0,
                new_chunks_indexed=0,
                total_vectors_in_index=self.vector_store.vector_count,
                index_path=str(self.vector_store.index_path),
            )

        # If document already indexed, remove old version before re-indexing
        if self.vector_store.is_document_indexed(document_id):
            self.vector_store.remove_document(document_id)

        # Generate embeddings via Gemini API
        chunk_texts = [c.text for c in chunks]
        embeddings = self.embedding_service.embed_texts(chunk_texts)

        # Add to vector store and persist
        added = self.vector_store.add_chunks(chunks, embeddings)

        return RAGIndexResponse(
            success=True,
            message=f"Successfully indexed {added} chunks from '{metadata.filename}'.",
            indexed_documents=1,
            new_chunks_indexed=added,
            total_vectors_in_index=self.vector_store.vector_count,
            index_path=str(self.vector_store.index_path),
        )

    def index_all_documents(self) -> RAGIndexResponse:
        """
        Indexes all processed documents currently registered in the database.
        Skips documents that are already indexed unless modified.
        """
        if not self.embedding_service.is_configured:
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env "
                "to generate real embeddings and index documents."
            )

        docs = doc_db.list_documents()
        if not docs:
            return RAGIndexResponse(
                success=True,
                message="No processed documents found in registry to index.",
                indexed_documents=0,
                new_chunks_indexed=0,
                total_vectors_in_index=self.vector_store.vector_count,
                index_path=str(self.vector_store.index_path),
            )

        indexed_count = 0
        total_new_chunks = 0

        for doc in docs:
            # Check if processed JSON exists
            doc_record = doc_db.get_document(doc.id)
            if not doc_record:
                continue
            proc_path = Path(doc_record["processed_path"])
            if not proc_path.exists():
                continue

            # Check if already indexed
            if self.vector_store.is_document_indexed(doc.id):
                continue

            try:
                res = self.index_document(doc.id)
                indexed_count += res.indexed_documents
                total_new_chunks += res.new_chunks_indexed
                time.sleep(1.0)
            except Exception as e:
                print(f"Warning: Failed indexing doc {doc.id} ({doc.filename}): {e}")

        return RAGIndexResponse(
            success=True,
            message=f"Indexing completed: {indexed_count} new documents, {total_new_chunks} chunks indexed.",
            indexed_documents=indexed_count,
            new_chunks_indexed=total_new_chunks,
            total_vectors_in_index=self.vector_store.vector_count,
            index_path=str(self.vector_store.index_path),
        )

    def query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        """
        Executes grounded semantic retrieval and synthesis:
        1. Embeds the user question using text-embedding-004.
        2. Retrieves top-k matching chunks from FAISS vector store.
        3. Formulates a grounded prompt with strictly cited evidence chunks.
        4. Synthesizes response via Gemini LLM with strict grounding instructions.
        """
        start_time = time.perf_counter()

        if not self.embedding_service.is_configured:
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env "
                "to query the knowledge base and generate grounded answers."
            )

        if self.vector_store.vector_count == 0:
            return RAGQueryResponse(
                query=request.query,
                answer=(
                    "The knowledge base is currently empty. Please index your processed documents "
                    "using the 'Index Documents' control before asking questions."
                ),
                evidence_found=False,
                model_used=self.llm_model,
                sources_count=0,
                sources=[],
                latency_ms=int((time.perf_counter() - start_time) * 1000),
            )

        # 1. Embed query
        query_embedding = self.embedding_service.embed_query(request.query)

        # 2. Semantic retrieval from FAISS
        raw_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            document_ids=request.document_ids,
        )

        if not raw_results:
            return RAGQueryResponse(
                query=request.query,
                answer="The requested information was not found in the indexed documents.",
                evidence_found=False,
                model_used=self.llm_model,
                sources_count=0,
                sources=[],
                latency_ms=int((time.perf_counter() - start_time) * 1000),
            )

        # 3. Format sources
        sources: List[RAGSource] = []
        for chunk, score in raw_results:
            sources.append(
                RAGSource(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.metadata.document_id,
                    filename=chunk.metadata.filename,
                    file_type=chunk.metadata.file_type,
                    page_number=chunk.metadata.page_number,
                    section=chunk.metadata.section,
                    source_type=chunk.metadata.source_type,
                    text=chunk.text,
                    score=round(score, 4),
                    dimensions=chunk.metadata.dimensions,
                    bbox=chunk.metadata.bbox,
                )
            )

        # 4. Formulate grounded synthesis prompt
        evidence_blocks = []
        for i, s in enumerate(sources, start=1):
            evidence_blocks.append(
                f"[Source {i} | Document: {s.filename} | Page: {s.page_number} | Type: {s.source_type} | Section: {s.section}]\n"
                f"{s.text}\n"
            )

        combined_evidence = "\n---\n".join(evidence_blocks)

        system_instruction = (
            "You are the Grounded Mining Intelligence Assistant for Central Mine Planning & Design Institute (CMPDI) "
            "and Coal India Limited (CIL).\n\n"
            "STRICT GROUNDING RULES:\n"
            "1. Answer ONLY using the facts, figures, dates, numbers, and measurements directly present in the provided Document Evidence.\n"
            "2. Never extrapolate, hallucinate, assume, or invent facts, borehole IDs, mine names, seam codes, or metrics.\n"
            "3. Cite your sources in brackets like [Filename, Page X] directly after each factual statement or sentence.\n"
            "4. Preserve numerical values, percentages, depths, thicknesses, and units exactly as stated in the evidence.\n"
            "5. If the provided evidence does NOT contain the answer, explicitly state: "
            "'The requested information was not found in the indexed documents.' Do not attempt to guess or answer from outside knowledge."
        )

        user_content = (
            f"DOCUMENT EVIDENCE:\n"
            f"{combined_evidence}\n\n"
            f"QUESTION:\n{request.query}\n\n"
            f"Please provide a factual, grounded answer with page-level citations based exclusively on the evidence above."
        )

        # 5. Synthesize answer with Gemini
        client = self.embedding_service.get_client()
        answer_text = "The requested information was not found in the indexed documents."
        max_retries = 3
        for attempt in range(max_retries):
            try:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,  # Low temperature for deterministic, factual grounding
                )
                response = client.models.generate_content(
                    model=self.llm_model,
                    contents=user_content,
                    config=config,
                )
                if response and response.text:
                    answer_text = response.text.strip()
                break
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < max_retries - 1:
                    time.sleep(3.0 * (attempt + 1))
                    continue
                raise RuntimeError(f"Gemini grounded generation failed: {str(e)}")

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        evidence_found = "not found in the indexed documents" not in answer_text.lower()

        return RAGQueryResponse(
            query=request.query,
            answer=answer_text,
            evidence_found=evidence_found,
            model_used=self.llm_model,
            sources_count=len(sources),
            sources=sources,
            latency_ms=latency_ms,
        )


rag_service = GroundedRAGService()
RAGKnowledgeBaseService = GroundedRAGService
