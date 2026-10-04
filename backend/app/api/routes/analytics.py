"""
Analytics & Visualization API Routes (Phase 6)
SIH 2026 Problem Statement 26023 (CMPDI / Coal India Limited)

Endpoints:
- GET /api/analytics/summary: Consolidated KPI counts, drilling targets, coal resources, reports
- GET /api/analytics/drilling: Target vs achievement, agency comparison, promotional drilling by block
- GET /api/analytics/resources: Additional, proved, indicated coal resources & seam reserves
- GET /api/analytics/projects: Filterable project database, subsidiary distribution
- GET /api/analytics/quality: Proximate analysis charts, means & empty-state fallback
- GET /api/analytics/metrics: Searchable, paginated geological metrics explorer
- GET /api/analytics/comparison: Cross-document multi-entity comparison with unit integrity
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status

from app.schemas.analytics import (
    AnalyticsKPISummary,
    DrillingAnalyticsResponse,
    ResourceAnalyticsResponse,
    ProjectAnalyticsResponse,
    CoalQualityResponse,
    GeologicalMetricsResponse,
    CrossDocumentComparisonResponse,
)
from app.services.analytics.service import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["Phase 6 - Mining Analytics & Visualizations"])


@router.get(
    "/summary",
    response_model=AnalyticsKPISummary,
    summary="Get consolidated geological and operational KPI summary",
)
async def get_analytics_summary(
    document_id: Optional[str] = Query(None, description="Document ID to scope telemetry"),
    source_document: Optional[str] = Query(None, description="Document filename to scope telemetry"),
) -> AnalyticsKPISummary:
    """Returns high-level KPI cards with provenance mapping from extraction.db."""
    try:
        return analytics_service.get_summary(
            document_id=document_id, source_document=source_document
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate analytics summary: {str(e)}",
        )


@router.get(
    "/drilling",
    response_model=DrillingAnalyticsResponse,
    summary="Get exploratory drilling targets, achievements, and block metrics",
)
async def get_drilling_analytics(
    document_id: Optional[str] = Query(None, description="Document ID to scope drilling metrics"),
    source_document: Optional[str] = Query(None, description="Document filename to scope drilling metrics"),
) -> DrillingAnalyticsResponse:
    """Returns agency-wise drilling comparison, promotional drilling by block, and logging metrics."""
    try:
        return analytics_service.get_drilling_analytics(
            document_id=document_id, source_document=source_document
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve drilling analytics: {str(e)}",
        )


@router.get(
    "/resources",
    response_model=ResourceAnalyticsResponse,
    summary="Get coal resource figures, categories, and seam reserves",
)
async def get_resource_analytics(
    document_id: Optional[str] = Query(None, description="Document ID to scope resource data"),
    source_document: Optional[str] = Query(None, description="Document filename to scope resource data"),
) -> ResourceAnalyticsResponse:
    """Returns proved, indicated, additional resource estimates and seam-by-seam reserves."""
    try:
        return analytics_service.get_resource_analytics(
            document_id=document_id, source_document=source_document
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resource analytics: {str(e)}",
        )


@router.get(
    "/projects",
    response_model=ProjectAnalyticsResponse,
    summary="Get filterable mine and project analytics with subsidiary breakdowns",
)
async def get_project_analytics(
    document_id: Optional[str] = Query(None, description="Document ID filter"),
    source_document: Optional[str] = Query(None, description="Source document filename filter"),
    subsidiary: Optional[str] = Query(None, description="Coal subsidiary filter (e.g. CCL, WCL, MCL)"),
    location: Optional[str] = Query(None, description="Coalfield / basin location filter"),
    search: Optional[str] = Query(None, description="Keyword search across name and block"),
) -> ProjectAnalyticsResponse:
    """Returns mine/project records and subsidiary distribution statistics."""
    try:
        return analytics_service.get_project_analytics(
            document_id=document_id,
            source_document=source_document,
            subsidiary=subsidiary,
            location=location,
            search=search,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project analytics: {str(e)}",
        )


@router.get(
    "/quality",
    response_model=CoalQualityResponse,
    summary="Get proximate analysis quality parameters and averages",
)
async def get_coal_quality(
    document_id: Optional[str] = Query(None, description="Document ID filter"),
    source_document: Optional[str] = Query(None, description="Source document filename filter"),
) -> CoalQualityResponse:
    """Returns moisture, ash, VM, FC, and GCV laboratory records or an explicit empty state."""
    try:
        return analytics_service.get_coal_quality_analytics(
            document_id=document_id, source_document=source_document
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve coal quality analytics: {str(e)}",
        )


@router.get(
    "/metrics",
    response_model=GeologicalMetricsResponse,
    summary="Searchable, filterable geological metrics explorer",
)
async def get_geological_metrics_explorer(
    document_id: Optional[str] = Query(None, description="Document ID filter"),
    source_document: Optional[str] = Query(None, description="Source document filename filter"),
    category: Optional[str] = Query(None, description="Metric category filter"),
    unit: Optional[str] = Query(None, description="Metric measurement unit filter"),
    search: Optional[str] = Query(None, description="Keyword search across metric name and evidence"),
    limit: int = Query(100, ge=1, le=500, description="Page size limit"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> GeologicalMetricsResponse:
    """Returns paginated geological metrics records with filter facets."""
    try:
        return analytics_service.get_metrics_explorer(
            document_id=document_id,
            source_document=source_document,
            category=category,
            unit=unit,
            search=search,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query geological metrics explorer: {str(e)}",
        )


@router.get(
    "/comparison",
    response_model=CrossDocumentComparisonResponse,
    summary="Cross-document comparative analytics with unit preservation",
)
async def get_cross_document_comparison(
    documents: Optional[str] = Query(
        None, description="Comma-separated list of document filenames to compare"
    ),
) -> CrossDocumentComparisonResponse:
    """Compares entity volume and compatible structured metrics across multiple indexed documents."""
    try:
        return analytics_service.get_cross_document_comparison(documents=documents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute cross-document comparison: {str(e)}",
        )
