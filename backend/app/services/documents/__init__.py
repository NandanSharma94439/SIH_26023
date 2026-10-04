from app.services.documents.service import DocumentIngestionService
from app.services.documents.table_normalization import (
    normalize_table_text,
    is_table_doubled,
    is_token_doubled,
    collapse_token,
)

__all__ = [
    "DocumentIngestionService",
    "normalize_table_text",
    "is_table_doubled",
    "is_token_doubled",
    "collapse_token",
]
