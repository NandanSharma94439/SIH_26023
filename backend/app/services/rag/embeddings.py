"""
Gemini Embedding Service for Vector Knowledge Base
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Responsibilities:
1. Connects to Google Gemini API using google.genai Client.
2. Generates real high-density embeddings using text-embedding-004.
3. Keeps all credentials backend-side and avoids mock/fake embeddings.
4. Provides clear configuration error if GEMINI_API_KEY is not configured.
"""

import time
from typing import List, Optional
from google import genai
from google.genai import types
from app.core.config import settings


class GeminiEmbeddingService:
    """Manages text embedding generation via Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_EMBEDDING_MODEL
        self._client: Optional[genai.Client] = None
        if self.is_configured:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception:
                self._client = None

    @property
    def is_configured(self) -> bool:
        """Returns True if a non-empty API key is present."""
        return bool(self.api_key and self.api_key.strip())

    def get_client(self) -> genai.Client:
        """Returns initialized genai.Client or raises a clear configuration error."""
        if not self.is_configured:
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env "
                "to generate real embeddings and query the vector knowledge base."
            )
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def embed_texts(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        Generates 768-dimensional embeddings for a list of document chunk texts.
        Never generates mock embeddings.
        Batches by both item count and character volume to respect Gemini API limits.
        """
        if not texts:
            return []

        client = self.get_client()
        all_embeddings: List[List[float]] = []
        config = types.EmbedContentConfig(output_dimensionality=768)

        # Batch by item count and char limit to adhere to Gemini API token limits
        batches: List[List[str]] = []
        current_batch: List[str] = []
        current_chars = 0

        for t in texts:
            text_item = t[:8000] if len(t) > 8000 else t
            if current_batch and (len(current_batch) >= batch_size or current_chars + len(text_item) > 12000):
                batches.append(current_batch)
                current_batch = [text_item]
                current_chars = len(text_item)
            else:
                current_batch.append(text_item)
                current_chars += len(text_item)
        if current_batch:
            batches.append(current_batch)

        for i, batch in enumerate(batches):
            response = None
            max_retries = 4
            for attempt in range(max_retries):
                try:
                    response = client.models.embed_content(
                        model=self.model,
                        contents=batch,
                        config=config,
                    )
                    break
                except Exception as e:
                    err_str = str(e)
                    if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "UNAVAILABLE" in err_str) and attempt < max_retries - 1:
                        backoff = 15.0 * (attempt + 1)
                        time.sleep(backoff)
                        continue
                    raise

            if response and response.embeddings:
                for emb in response.embeddings:
                    if emb.values:
                        all_embeddings.append(emb.values)
                    else:
                        raise RuntimeError(f"Embedding values missing from Gemini response in batch {i}.")
            else:
                raise RuntimeError(f"Gemini embedding API returned no embeddings for batch {i}.")

            # Gentle pause between batches to respect rate limits
            if i + 1 < len(batches):
                time.sleep(1.5)

        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """Generates embedding vector for a single user search query."""
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty.")

        client = self.get_client()
        config = types.EmbedContentConfig(output_dimensionality=768)
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                response = client.models.embed_content(
                    model=self.model,
                    contents=query.strip(),
                    config=config,
                )
                break
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < max_retries - 1:
                    time.sleep(2.0 * (attempt + 1))
                    continue
                raise

        if response and response.embeddings and response.embeddings[0].values:
            return response.embeddings[0].values
        raise RuntimeError("Gemini embedding API returned empty response for query.")
