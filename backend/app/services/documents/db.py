"""
SQLite Document Metadata Store
Provides persistent, acid-compliant storage for ingested document metadata.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.schemas.document import DocumentMetadata


class DocumentDatabase:
    """Manages SQLite storage for document metadata records."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.BASE_DIR / "storage" / "documents.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    total_pages INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'processed',
                    uploaded_at TEXT NOT NULL,
                    processing_time_ms INTEGER DEFAULT 0,
                    ocr_pages_count INTEGER DEFAULT 0,
                    has_tables INTEGER DEFAULT 0,
                    preview_text TEXT,
                    error_message TEXT,
                    stored_path TEXT NOT NULL,
                    processed_path TEXT NOT NULL,
                    content_hash TEXT
                )
                """
            )
            # Add column if table was created previously without content_hash
            cursor = conn.execute("PRAGMA table_info(documents)")
            cols = [r["name"] for r in cursor.fetchall()]
            if "content_hash" not in cols:
                conn.execute("ALTER TABLE documents ADD COLUMN content_hash TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash)"
            )
            conn.commit()
            self._backfill_hashes(conn)

    def _backfill_hashes(self, conn: sqlite3.Connection) -> None:
        """Backfills SHA-256 content hashes for existing records where content_hash is NULL."""
        import hashlib
        rows = conn.execute(
            "SELECT id, stored_path FROM documents WHERE content_hash IS NULL"
        ).fetchall()
        for r in rows:
            p = Path(r["stored_path"])
            if p.exists() and p.is_file():
                try:
                    chash = hashlib.sha256(p.read_bytes()).hexdigest()
                    conn.execute(
                        "UPDATE documents SET content_hash = ? WHERE id = ?",
                        (chash, r["id"]),
                    )
                except Exception:
                    pass
        conn.commit()

    def _row_to_metadata(self, r: sqlite3.Row) -> DocumentMetadata:
        keys = r.keys()
        return DocumentMetadata(
            id=r["id"],
            filename=r["filename"],
            file_type=r["file_type"],
            mime_type=r["mime_type"],
            file_size_bytes=r["file_size_bytes"],
            total_pages=r["total_pages"],
            status=r["status"],
            uploaded_at=datetime.fromisoformat(r["uploaded_at"]),
            processing_time_ms=r["processing_time_ms"],
            ocr_pages_count=r["ocr_pages_count"],
            has_tables=bool(r["has_tables"]),
            preview_text=r["preview_text"],
            error_message=r["error_message"],
            content_hash=r["content_hash"] if "content_hash" in keys else None,
        )

    def save_document(
        self,
        metadata: DocumentMetadata,
        stored_path: str,
        processed_path: str,
    ) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents (
                    id, filename, file_type, mime_type, file_size_bytes,
                    total_pages, status, uploaded_at, processing_time_ms,
                    ocr_pages_count, has_tables, preview_text, error_message,
                    stored_path, processed_path, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata.id,
                    metadata.filename,
                    metadata.file_type,
                    metadata.mime_type,
                    metadata.file_size_bytes,
                    metadata.total_pages,
                    metadata.status,
                    metadata.uploaded_at.isoformat(),
                    metadata.processing_time_ms,
                    metadata.ocr_pages_count,
                    1 if metadata.has_tables else 0,
                    metadata.preview_text,
                    metadata.error_message,
                    str(stored_path),
                    str(processed_path),
                    metadata.content_hash,
                ),
            )
            conn.commit()

    def list_documents(self) -> List[DocumentMetadata]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY uploaded_at DESC"
            ).fetchall()

            return [self._row_to_metadata(r) for r in rows]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
            if not row:
                return None

            return {
                "metadata": self._row_to_metadata(row),
                "stored_path": row["stored_path"],
                "processed_path": row["processed_path"],
            }

    def get_document_by_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Finds an existing canonical document with an identical SHA-256 content hash."""
        if not content_hash:
            return None
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE content_hash = ? ORDER BY uploaded_at ASC LIMIT 1",
                (content_hash,),
            ).fetchone()
            if not row:
                return None

            return {
                "metadata": self._row_to_metadata(row),
                "stored_path": row["stored_path"],
                "processed_path": row["processed_path"],
            }

    def delete_document(self, doc_id: str) -> bool:
        """Deletes a document record from SQLite by ID."""
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            return cur.rowcount > 0


doc_db = DocumentDatabase()
