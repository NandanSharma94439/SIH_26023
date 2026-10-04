"""
Benchmark & Validation API Routes
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Endpoints for:
1. Unified SIH outcome measurements
2. Report preparation time reduction & manual baseline submission
3. Ground-truth extraction accuracy validation
4. Workflow automation coverage
5. Multi-format benchmark export (Markdown, JSON, CSV)
"""

from fastapi import APIRouter, Query, Response, status
from fastapi.responses import PlainTextResponse

from app.schemas.benchmarks import (
    ManualTimeInput,
    ReportTimeBenchmarkItem,
    TimeReductionSummary,
    AccuracyBenchmarkResponse,
    AutomationCoverageResponse,
    UnifiedBenchmarkSummary,
)
from app.services.benchmarks.service import benchmark_service

router = APIRouter(prefix="/api/benchmarks", tags=["Validation & Benchmarks"])


@router.get(
    "/summary",
    response_model=UnifiedBenchmarkSummary,
    summary="Get unified SIH-26023 benchmark telemetry",
)
async def get_benchmark_summary():
    """Returns consolidated telemetry covering time reduction, accuracy, and automation coverage."""
    return benchmark_service.get_unified_summary()


@router.get(
    "/time-reduction",
    response_model=TimeReductionSummary,
    summary="Get report-preparation time reduction benchmarks",
)
async def get_time_reduction():
    """Returns time reduction calculations comparing GeoMine latency with evaluator manual baselines."""
    return benchmark_service.get_time_reduction_summary()


@router.post(
    "/time-reduction",
    response_model=ReportTimeBenchmarkItem,
    summary="Submit user-measured manual preparation baseline",
)
async def submit_manual_baseline(input_data: ManualTimeInput):
    """
    Allows a domain evaluator to input a measured manual preparation baseline for a report type,
    calculating exact Time Saved and Time Reduction % against actual GeoMine system latency.
    """
    return benchmark_service.measure_report_time(
        report_type=input_data.report_type,
        scope=input_data.scope,
        source_document=input_data.source_document,
        manual_time_minutes=input_data.manual_time_minutes,
    )


@router.get(
    "/accuracy",
    response_model=AccuracyBenchmarkResponse,
    summary="Get ground-truth extraction and report accuracy benchmark",
)
async def get_accuracy_benchmark():
    """
    Compares extracted entities against verified canonical ground-truth values.
    Calculates field accuracy % and category-level metrics with sample-size safeguards.
    """
    return benchmark_service.get_accuracy_benchmark()


@router.get(
    "/automation",
    response_model=AutomationCoverageResponse,
    summary="Get 12-stage workflow automation coverage analysis",
)
async def get_automation_coverage():
    """
    Evaluates the 12-stage reporting lifecycle for strict and weighted automation coverage.
    """
    return benchmark_service.get_automation_coverage()


@router.get(
    "/export",
    summary="Export benchmark validation report (Markdown, JSON, CSV)",
)
async def export_benchmark_report(
    format: str = Query("markdown", description="Export format: markdown, json, csv")
):
    """
    Exports complete reproducible benchmark methodology and results.
    """
    content = benchmark_service.export_benchmarks(export_format=format)
    media_type = "text/plain"
    ext = "txt"

    if format.lower() == "json":
        media_type = "application/json"
        ext = "json"
    elif format.lower() == "csv":
        media_type = "text/csv"
        ext = "csv"
    elif format.lower() == "markdown":
        media_type = "text/markdown"
        ext = "md"

    headers = {
        "Content-Disposition": f'attachment; filename="geomine_benchmarks_{format.lower()}.{ext}"'
    }

    return Response(content=content, media_type=media_type, headers=headers)
