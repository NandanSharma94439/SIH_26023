"""
Document Ingestion & Management API Routes
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)
"""

import hashlib
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Response
from app.schemas.document import (
    DocumentMetadata,
    DocumentDetailResponse,
    DocumentPagesResponse,
    DocumentUploadResponse,
)
from app.services.documents.service import document_service
from app.services.documents.db import doc_db

router = APIRouter(prefix="/api/documents", tags=["Document Ingestion & Multi-Modal Parser"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    response: Response,
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """
    Ingests, validates, stores, and parses a geological or mining document.
    Supported formats: PDF, DOCX, XLSX, PNG, TIFF, JPG.
    Extracts text, bounding blocks, structured tables, and applies OCR fallback.
    Performs SHA-256 content deduplication to prevent duplicate records and processing.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing in upload request.",
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}",
        )

    # 1. Validate file format and size before deduplication check
    safe_filename = document_service.sanitize_filename(file.filename)
    is_valid, error_msg, file_type = document_service.validate_file(
        safe_filename, file.content_type or "", len(content)
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        )

    # 2. SHA-256 Content Deduplication Check
    content_hash = hashlib.sha256(content).hexdigest()
    existing_doc = doc_db.get_document_by_hash(content_hash)

    if existing_doc:
        # Document with identical content already exists.
        # Do not create a new document record.
        # Do not duplicate processing/OCR/RAG/extraction.
        # Return/reuse the existing document with a clear already_exists response.
        response.status_code = status.HTTP_200_OK
        existing_meta = existing_doc["metadata"]
        existing_pages = document_service.get_document_pages(existing_meta.id) or []

        return DocumentUploadResponse(
            success=True,
            already_exists=True,
            message=f"Document already exists: '{existing_meta.filename}' (ID: {existing_meta.id}). Reusing existing record.",
            document=existing_meta,
            pages_preview=existing_pages[:3],
        )

    # 3. Process new unique document
    try:
        metadata, pages = document_service.process_document(
            file_bytes=content,
            original_filename=file.filename,
            content_type=file.content_type or "",
            content_hash=content_hash,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}",
        )

    return DocumentUploadResponse(
        success=True,
        already_exists=False,
        message=f"Document '{metadata.filename}' parsed successfully into {metadata.total_pages} page(s).",
        document=metadata,
        pages_preview=pages[:3],  # First 3 pages for instant preview
    )


@router.get("", response_model=List[DocumentMetadata])
async def list_documents() -> List[DocumentMetadata]:
    """Retrieves all ingested documents sorted by upload date descending."""
    return doc_db.list_documents()


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_details(document_id: str) -> DocumentDetailResponse:
    """Retrieves detailed metadata and storage information for a specific document."""
    record = doc_db.get_document(document_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )

    return DocumentDetailResponse(
        metadata=record["metadata"],
        storage_path=record["stored_path"],
        pages_count=record["metadata"].total_pages,
    )


@router.get("/{document_id}/pages", response_model=DocumentPagesResponse)
async def get_document_pages(document_id: str) -> DocumentPagesResponse:
    """Retrieves all parsed pages, text blocks, and structured tables for a specific document."""
    record = doc_db.get_document(document_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )

    pages = document_service.get_document_pages(document_id)
    if pages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parsed page contents for document '{document_id}' not found.",
        )

    return DocumentPagesResponse(
        document_id=document_id,
        total_pages=len(pages),
        pages=pages,
    )
