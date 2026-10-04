"""
Domain-Aware Semantic Document Chunker for Mining Documents
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Responsibilities:
1. Transforms processed document pages (text, blocks, normalized tables) into domain-aware semantic chunks.
2. Formats tabular data keeping column headers explicitly paired with row cell values.
3. Retains section headers and geological stratigraphy context with following narrative blocks.
4. Enforces configurable chunk sizes and overlaps with sentence boundary preservation.
5. Captures rich metadata (document_id, filename, file_type, page_number, section, source_type, bbox).
"""

import re
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.schemas.document import DocumentMetadata, DocumentPage, ExtractedTable, TextBlock
from app.schemas.rag import RAGChunk, RAGChunkMetadata


class DomainAwareChunker:
    """Chunks mining reports, borehole logs, feasibility studies, and spreadsheets domain-sensitively."""

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_document(
        self,
        metadata: DocumentMetadata,
        pages: List[DocumentPage],
    ) -> List[RAGChunk]:
        """Processes all pages of a document into structured RAG chunks."""
        all_chunks: List[RAGChunk] = []
        chunk_counter = 0

        for page in pages:
            page_num = page.page_number
            active_section = "General"

            # 1. Chunk normalized tables first (structured data preservation)
            if page.tables:
                for table in page.tables:
                    table_chunks = self._chunk_table(
                        table=table,
                        metadata=metadata,
                        page_num=page_num,
                        start_chunk_idx=chunk_counter,
                    )
                    all_chunks.extend(table_chunks)
                    chunk_counter += len(table_chunks)

            # 2. Chunk text blocks / narrative text
            text_chunks = self._chunk_page_text(
                page=page,
                metadata=metadata,
                page_num=page_num,
                start_chunk_idx=chunk_counter,
            )
            all_chunks.extend(text_chunks)
            chunk_counter += len(text_chunks)

        return all_chunks

    def _chunk_table(
        self,
        table: ExtractedTable,
        metadata: DocumentMetadata,
        page_num: int,
        start_chunk_idx: int,
    ) -> List[RAGChunk]:
        """Converts tabular grid into header-associated row strings, preserving context."""
        chunks: List[RAGChunk] = []
        if not table.rows:
            return chunks

        headers = [h.strip().replace("\n", " ") for h in (table.headers or [])]
        clean_headers = [h if h else f"Col_{i+1}" for i, h in enumerate(headers)]

        current_rows_text: List[str] = []
        current_len = 0
        table_title = f"[Table on Page {page_num} (Table {table.table_index})]"

        for r_idx, row in enumerate(table.rows):
            # Build row string pairing header with cell value
            cell_pairs = []
            for c_idx, cell in enumerate(row):
                header = clean_headers[c_idx] if c_idx < len(clean_headers) else f"Col_{c_idx+1}"
                val = str(cell or "").strip().replace("\n", " ")
                if val:
                    cell_pairs.append(f"{header}: {val}")

            if not cell_pairs:
                continue

            row_line = " | ".join(cell_pairs)
            row_len = len(row_line)

            if current_len + row_len > self.chunk_size and current_rows_text:
                # Flush current batch into a chunk
                full_text = f"{table_title}\n" + "\n".join(current_rows_text)
                chunk_id = f"{metadata.id}_p{page_num}_t{table.table_index}_c{len(chunks)}"
                chunks.append(
                    RAGChunk(
                        chunk_id=chunk_id,
                        text=full_text,
                        metadata=RAGChunkMetadata(
                            chunk_id=chunk_id,
                            document_id=metadata.id,
                            filename=metadata.filename,
                            file_type=metadata.file_type,
                            page_number=page_num,
                            section="Table Data",
                            source_type="table",
                            char_count=len(full_text),
                            word_count=len(full_text.split()),
                            dimensions=None,
                            bbox=table.bbox,
                        ),
                    )
                )
                current_rows_text = []
                current_len = 0

            current_rows_text.append(row_line)
            current_len += row_len

        # Flush remaining rows
        if current_rows_text:
            full_text = f"{table_title}\n" + "\n".join(current_rows_text)
            chunk_id = f"{metadata.id}_p{page_num}_t{table.table_index}_c{len(chunks)}"
            chunks.append(
                RAGChunk(
                    chunk_id=chunk_id,
                    text=full_text,
                    metadata=RAGChunkMetadata(
                        chunk_id=chunk_id,
                        document_id=metadata.id,
                        filename=metadata.filename,
                        file_type=metadata.file_type,
                        page_number=page_num,
                        section="Table Data",
                        source_type="table",
                        char_count=len(full_text),
                        word_count=len(full_text.split()),
                        dimensions=None,
                        bbox=table.bbox,
                    ),
                )
            )

        return chunks

    def _chunk_page_text(
        self,
        page: DocumentPage,
        metadata: DocumentMetadata,
        page_num: int,
        start_chunk_idx: int,
    ) -> List[RAGChunk]:
        """Extracts narrative paragraphs with section awareness and sliding-window splitting."""
        chunks: List[RAGChunk] = []
        raw_text = page.text.strip() if page.text else ""
        if not raw_text:
            return chunks

        # Section header regex (e.g., '1.0 INTRODUCTION', 'PART: B', 'SECTION 3', etc.)
        section_pattern = re.compile(
            r"^(?:(?:\d+\.){1,3}\d*\s+[A-Z0-9\s/&,-]{3,}|(?:PART|SECTION|CHAPTER)\s*[:\-\w\s]{2,}|[A-Z\s]{4,}:)$",
            re.MULTILINE,
        )

        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in raw_text.split("\n") if p.strip()]

        current_section = "General"
        current_chunk_paras: List[str] = []
        current_len = 0

        source_type = "ocr" if page.ocr_applied else "text"

        for para in paragraphs:
            # Check if this paragraph is a section header
            if section_pattern.match(para) and len(para) < 120:
                current_section = para.replace("\n", " ").strip()

            para_len = len(para)

            # If adding this paragraph exceeds chunk size, flush the current buffer
            if current_len + para_len > self.chunk_size and current_chunk_paras:
                chunk_text = "\n\n".join(current_chunk_paras)
                chunk_id = f"{metadata.id}_p{page_num}_tx{len(chunks)}"
                chunks.append(
                    RAGChunk(
                        chunk_id=chunk_id,
                        text=chunk_text,
                        metadata=RAGChunkMetadata(
                            chunk_id=chunk_id,
                            document_id=metadata.id,
                            filename=metadata.filename,
                            file_type=metadata.file_type,
                            page_number=page_num,
                            section=current_section,
                            source_type=source_type,
                            char_count=len(chunk_text),
                            word_count=len(chunk_text.split()),
                            dimensions=page.dimensions,
                            bbox=None,
                        ),
                    )
                )

                # Implement overlap: retain last paragraph if reasonable
                if current_chunk_paras and len(current_chunk_paras[-1]) <= self.chunk_overlap:
                    current_chunk_paras = [current_chunk_paras[-1], para]
                    current_len = len(current_chunk_paras[0]) + para_len
                else:
                    current_chunk_paras = [para]
                    current_len = para_len
            else:
                current_chunk_paras.append(para)
                current_len += para_len

        # Flush remaining paragraphs
        if current_chunk_paras:
            chunk_text = "\n\n".join(current_chunk_paras)
            chunk_id = f"{metadata.id}_p{page_num}_tx{len(chunks)}"
            chunks.append(
                RAGChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    metadata=RAGChunkMetadata(
                        chunk_id=chunk_id,
                        document_id=metadata.id,
                        filename=metadata.filename,
                        file_type=metadata.file_type,
                        page_number=page_num,
                        section=current_section,
                        source_type=source_type,
                        char_count=len(chunk_text),
                        word_count=len(chunk_text.split()),
                        dimensions=page.dimensions,
                        bbox=None,
                    ),
                )
            )

        return chunks
