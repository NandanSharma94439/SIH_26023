"""
Phase 4 Extraction REST API Endpoints
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Exposes structured extraction operations and entity retrieval:
- POST /api/extraction/document/{document_id}
- POST /api/extraction/all
- GET  /api/extraction/status
- GET  /api/extraction/boreholes
- GET  /api/extraction/seams
- GET  /api/extraction/proximate-analysis
- GET  /api/extraction/mines
- GET  /api/extraction/metrics
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.extraction import (
    Borehole,
    CoalSeam,
    ProximateAnalysis,
    MineProject,
    GeologicalMetric,
    DocumentExtractionResult,
    ExtractionStatusResponse,
)
from app.services.extraction.service import extraction_service

router = APIRouter(prefix="/api/extraction", tags=["Structured Mining Extraction"])


@router.get(
    "/status",
    response_model=ExtractionStatusResponse,
    summary="Get structured extraction telemetry & record counts",
)
async def get_extraction_status():
    """Returns database record counts for all 5 mining entity types and configuration status."""
    return extraction_service.get_service_status()


@router.post(
    "/document/{document_id}",
    response_model=DocumentExtractionResult,
    summary="Extract structured mining entities from a single document",
)
async def extract_document(document_id: str):
    """
    Parses processed tables and text for a document, prompts Gemini for structured extraction,
    validates with Pydantic, and saves relational records with provenance.
    """
    try:
        return extraction_service.extract_document(document_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}",
        )


@router.post(
    "/all",
    summary="Batch extract structured mining entities across all processed documents",
)
async def extract_all_documents():
    """Triggers structured extraction across all registered processed documents."""
    try:
        return extraction_service.extract_all_documents()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk extraction failed: {str(e)}",
        )


@router.get(
    "/boreholes",
    response_model=List[Borehole],
    summary="List extracted borehole logs with provenance",
)
async def get_boreholes(
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    source_document: Optional[str] = Query(None, description="Filter by source document filename"),
    borehole_id: Optional[str] = Query(None, description="Filter by borehole identifier"),
    search: Optional[str] = Query(None, description="Search across borehole ID, project, lithology"),
):
    """Returns relational borehole records including collar elevation, total depth, and lithology."""
    return extraction_service.get_boreholes(
        document_id=document_id,
        borehole_id=borehole_id,
        search=search,
        source_document=source_document,
    )


@router.get(
    "/seams",
    response_model=List[CoalSeam],
    summary="List extracted coal seams with stratigraphy & reserves",
)
async def get_seams(
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    source_document: Optional[str] = Query(None, description="Filter by source document filename"),
    seam_id: Optional[str] = Query(None, description="Filter by seam code"),
    borehole_id: Optional[str] = Query(None, description="Filter by borehole identifier"),
    search: Optional[str] = Query(None, description="Search seam code, grade, or category"),
):
    """Returns relational coal seam records with depth from/to, thickness, grade, and reserves."""
    return extraction_service.get_seams(
        document_id=document_id,
        seam_id=seam_id,
        borehole_id=borehole_id,
        search=search,
        source_document=source_document,
    )


@router.get(
    "/proximate-analysis",
    response_model=List[ProximateAnalysis],
    summary="List extracted proximate analyses & coal quality metrics",
)
async def get_proximate_analysis(
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    source_document: Optional[str] = Query(None, description="Filter by source document filename"),
    seam_id: Optional[str] = Query(None, description="Filter by seam code"),
    borehole_id: Optional[str] = Query(None, description="Filter by borehole identifier"),
):
    """Returns proximate analysis parameters: moisture %, ash %, volatile matter %, and GCV."""
    return extraction_service.get_proximate_analyses(
        document_id=document_id,
        seam_id=seam_id,
        borehole_id=borehole_id,
        source_document=source_document,
    )


@router.get(
    "/mines",
    response_model=List[MineProject],
    summary="List extracted mining projects, feasibility blocks & production targets",
)
async def get_mines(
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    source_document: Optional[str] = Query(None, description="Filter by source document filename"),
    search: Optional[str] = Query(None, description="Search project name, location, or block"),
):
    """Returns mining project records including target production, stripping ratio, and life of mine."""
    return extraction_service.get_mines(
        document_id=document_id,
        search=search,
        source_document=source_document,
    )


@router.get(
    "/metrics",
    response_model=List[GeologicalMetric],
    summary="List extracted exploration metrics & operational statistics",
)
async def get_metrics(
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    source_document: Optional[str] = Query(None, description="Filter by source document filename"),
    category: Optional[str] = Query(None, description="Filter by metric category"),
):
    """Returns reported exploration metrics (e.g. drilling target achievement, reports submitted)."""
    return extraction_service.get_metrics(
        document_id=document_id,
        category=category,
        source_document=source_document,
    )
