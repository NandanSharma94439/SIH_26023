"""
FAISS Vector Store & Metadata Persistence
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Responsibilities:
1. Manages a high-performance FAISS IndexFlatIP (cosine similarity via L2 normalization).
2. Persists index and chunk metadata to storage/faiss_index/ on disk.
3. Automatically recovers index and metadata on backend restart.
4. Provides semantic retrieval with score ranking and optional document filtering.
5. Tracks indexed documents to prevent redundant re-indexing.
"""

import pickle
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

import faiss
import numpy as np

from app.core.config import settings
from app.schemas.rag import RAGChunk


class FAISSVectorStore:
    """Manages persistent FAISS vector index and document chunk metadata."""

    DIMENSION = 768  # Gemini text-embedding-004 dimension

    def __init__(
        self,
        index_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
    ):
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.metadata_path = metadata_path or settings.FAISS_METADATA_PATH
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(self.DIMENSION)
        # Mapping vector_idx (int) -> RAGChunk
        self.chunks: List[RAGChunk] = []
        # Set of indexed document_ids
        self.indexed_doc_ids: Set[str] = set()

        # Load existing index from disk if present
        self.load()

    @property
    def vector_count(self) -> int:
        return self.index.ntotal if self.index else 0

    @property
    def indexed_documents_count(self) -> int:
        return len(self.indexed_doc_ids)

    def is_document_indexed(self, doc_id: str) -> bool:
        return doc_id in self.indexed_doc_ids

    def add_chunks(self, chunks: List[RAGChunk], embeddings: List[List[float]]) -> int:
        """Adds chunks and their embedding vectors to the FAISS index and persists to disk."""
        if not chunks or not embeddings:
            return 0
        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch between chunks count ({len(chunks)}) and embeddings count ({len(embeddings)})")

        with self._lock:
            vectors = np.array(embeddings, dtype=np.float32)
            if vectors.shape[1] != self.DIMENSION:
                raise ValueError(f"Expected embedding dimension {self.DIMENSION}, got {vectors.shape[1]}")

            # Normalize vectors for exact Cosine Similarity with Inner Product
            faiss.normalize_L2(vectors)

            self.index.add(vectors)
            for c in chunks:
                self.chunks.append(c)
                self.indexed_doc_ids.add(c.metadata.document_id)

            self.save()
            return len(chunks)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
    ) -> List[Tuple[RAGChunk, float]]:
        """
        Retrieves top_k most similar chunks for a query embedding.
        Returns list of (RAGChunk, similarity_score) tuples sorted by score desc.
        """
        if self.vector_count == 0:
            return []

        q_vec = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(q_vec)

        # Retrieve more candidates if document filtering is active
        k_search = min(top_k * 4 if document_ids else top_k, self.vector_count)

        with self._lock:
            distances, indices = self.index.search(q_vec, k_search)

        results: List[Tuple[RAGChunk, float]] = []
        doc_filter = set(document_ids) if document_ids else None

        for idx, dist in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue

            chunk = self.chunks[idx]
            if doc_filter and chunk.metadata.document_id not in doc_filter:
                continue

            # Convert inner product to cosine similarity score in [0.0, 1.0]
            score = float(np.clip((dist + 1.0) / 2.0 if dist < 0 else dist, 0.0, 1.0))
            results.append((chunk, score))

            if len(results) >= top_k:
                break

        return results

    def remove_document(self, doc_id: str) -> bool:
        """Removes a document from the index and rebuilds or removes vector IDs."""
        with self._lock:
            if doc_id not in self.indexed_doc_ids:
                return False

            indices_to_remove = [
                i for i, c in enumerate(self.chunks) if c.metadata.document_id == doc_id
            ]
            if not indices_to_remove:
                return False

            if len(indices_to_remove) == len(self.chunks):
                self.index = faiss.IndexFlatIP(self.DIMENSION)
                self.chunks = []
                self.indexed_doc_ids.clear()
            else:
                sel = faiss.IDSelectorBatch(indices_to_remove)
                self.index.remove_ids(sel)
                remove_set = set(indices_to_remove)
                self.chunks = [c for i, c in enumerate(self.chunks) if i not in remove_set]
                self.indexed_doc_ids.discard(doc_id)

            self.save()
            return True

    def save(self) -> None:
        """Persists the FAISS index binary and metadata mapping to disk."""
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(self.index_path))

            meta_payload = {
                "chunks": [c.model_dump() for c in self.chunks],
                "indexed_doc_ids": list(self.indexed_doc_ids),
                "dimension": self.DIMENSION,
            }
            with open(self.metadata_path, "wb") as f:
                pickle.dump(meta_payload, f)
        except Exception as e:
            print(f"Warning: Failed to persist FAISS index to disk: {e}")

    def load(self) -> bool:
        """Loads FAISS index binary and metadata mapping from disk."""
        if not self.index_path.exists() or not self.metadata_path.exists():
            return False

        try:
            with self._lock:
                loaded_index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, "rb") as f:
                    meta_payload = pickle.load(f)

                self.index = loaded_index
                self.chunks = [RAGChunk(**item) for item in meta_payload.get("chunks", [])]
                self.indexed_doc_ids = set(meta_payload.get("indexed_doc_ids", []))
                return True
        except Exception as e:
            print(f"Warning: Failed to load FAISS index from disk: {e}")
            self.index = faiss.IndexFlatIP(self.DIMENSION)
            self.chunks = []
            self.indexed_doc_ids.clear()
            return False
