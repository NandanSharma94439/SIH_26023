"""
Reports API Routes for Phase 5: Automated Geological Reporting
SIH 2026 Problem Statement 26023 (CMPDI / Coal India Limited)

Provides endpoints to:
- Inspect reporting subsystem status & available templates
- Generate structured CMPDI Geological Summaries & Reserve Reconciliation Memos
- Export reports into PDF, Excel, and Markdown
"""

from typing import List
from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import Response

from app.schemas.report import (
    ReportType,
    ReportScope,
    ExportFormat,
    ReportGenerationRequest,
    ReportExportRequest,
    GeneratedReport,
    ReportStatusResponse,
    ReportTypeInfo,
)
from app.services.reports.service import report_service

router = APIRouter(prefix="/api/reports", tags=["Phase 5 - Geological Reports"])


@router.get(
    "/status",
    response_model=ReportStatusResponse,
    summary="Get reporting subsystem status and available templates",
)
async def get_reports_status() -> ReportStatusResponse:
    """Returns telemetry of available report templates, export formats, and database entity counts."""
    return report_service.get_service_status()


@router.get(
    "/types",
    response_model=List[ReportTypeInfo],
    summary="List supported report template types and recommended scopes",
)
async def get_report_types() -> List[ReportTypeInfo]:
    """Returns metadata for all available report templates."""
    return report_service.get_report_types()


@router.post(
    "/generate",
    response_model=GeneratedReport,
    summary="Generate a structured report from Phase 4 relational database",
)
async def generate_report(request: ReportGenerationRequest) -> GeneratedReport:
    """
    Compiles verified Phase 4 records (mines, boreholes, seams, proximate, metrics)
    into a structured report with metadata, sections, and rendered markdown.
    """
    try:
        return report_service.generate_report(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


@router.post(
    "/geological-summary",
    response_model=GeneratedReport,
    summary="Generate a CMPDI Geological Summary Report",
)
async def generate_geological_summary(request: ReportGenerationRequest) -> GeneratedReport:
    """Shortcut endpoint to generate a CMPDI Geological Summary Report."""
    request.report_type = ReportType.CMPDI_GEOLOGICAL_SUMMARY
    return report_service.generate_report(request)


@router.post(
    "/reserve-reconciliation",
    response_model=GeneratedReport,
    summary="Generate a Seam-by-Seam Reserve Reconciliation Memo",
)
async def generate_reserve_reconciliation(request: ReportGenerationRequest) -> GeneratedReport:
    """Shortcut endpoint to generate a Seam-by-Seam Reserve Reconciliation Memo."""
    request.report_type = ReportType.RESERVE_RECONCILIATION_MEMO
    return report_service.generate_report(request)


@router.post(
    "/export/pdf",
    summary="Export generated report as a high-density professional PDF document",
)
async def export_pdf(request: ReportGenerationRequest):
    """Generates the report and returns binary PDF file stream for download."""
    try:
        export_req = ReportExportRequest(**request.model_dump(), export_format=ExportFormat.PDF)
        file_bytes, media_type, filename = report_service.export_report_file(export_req)
        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF export failed: {str(e)}",
        )


@router.post(
    "/export/excel",
    summary="Export generated report as a multi-worksheet Excel workbook",
)
async def export_excel(request: ReportGenerationRequest):
    """Generates the report and returns binary Excel (.xlsx) file stream for download."""
    try:
        export_req = ReportExportRequest(**request.model_dump(), export_format=ExportFormat.EXCEL)
        file_bytes, media_type, filename = report_service.export_report_file(export_req)
        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel export failed: {str(e)}",
        )


@router.post(
    "/export/markdown",
    summary="Export generated report as a clean Markdown text document",
)
async def export_markdown(request: ReportGenerationRequest):
    """Generates the report and returns text Markdown (.md) file stream for download."""
    try:
        export_req = ReportExportRequest(**request.model_dump(), export_format=ExportFormat.MARKDOWN)
        file_bytes, media_type, filename = report_service.export_report_file(export_req)
        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Markdown export failed: {str(e)}",
        )
