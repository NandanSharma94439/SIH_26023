"""
Geological & Mining Report Generator Service (Phase 5 Delivery)
SIH 2026 Problem Statement 26023 (CMPDI / Coal India Limited)

Coordinates:
1. Data assembly from Phase 4 relational database (ReportDataAssembler)
2. Report generation for Geological Summary & Reserve Reconciliation (GeologicalReportGenerator)
3. Multi-format export into PDF, Excel, and Markdown (ReportExporter)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

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
from app.services.extraction.db import extraction_db
from app.services.reports.assembler import ReportDataAssembler
from app.services.reports.generator import GeologicalReportGenerator, report_generator
from app.services.reports.exporters import ReportExporter, report_exporter


class GeologicalReportGeneratorService:
    """Enterprise report generator for standardized CMPDI & CIL mining reports."""

    REPORT_TEMPLATES = [
        ReportTypeInfo(
            id=ReportType.CMPDI_GEOLOGICAL_SUMMARY.value,
            name="CMPDI Geological Summary Report",
            description="Standardized CMPDI geological report covering project feasibility, exploratory borehole stratigraphy, coal seam reserves, and proximate laboratory quality parameters.",
            recommended_scopes=["all", "document", "project"],
            features=[
                "Mine Planning & Stripping Ratios",
                "Exploratory Borehole Logs & Lithology Strata",
                "Coal Seam Thickness & Reserve Classifications",
                "Proximate Quality Matrix (Ash, VM, Moisture, GCV)",
                "Departmental Exploration & Drilling Targets",
                "Complete Document & Page Provenance",
            ],
        ),
        ReportTypeInfo(
            id=ReportType.RESERVE_RECONCILIATION_MEMO.value,
            name="Seam-by-Seam Reserve Reconciliation Memo",
            description="Technical reconciliation memo correlating coal seams, true thickness, gross vs. extractable reserves, mining loss calculations, and borehole stratigraphy.",
            recommended_scopes=["document", "project", "all"],
            features=[
                "Seam Correlation Across Exploratory Boreholes",
                "Gross In-Situ vs. Extractable Reserve Reconciliation",
                "Calculated Extraction Recovery Factor & Mining Loss",
                "Stratigraphic Strata & Collar Control Context",
                "Proximate Analysis Grade Verification",
                "Auditable Source Evidence Quotes",
            ],
        ),
    ]

    EXPORT_FORMATS = [
        ExportFormat.PDF.value,
        ExportFormat.EXCEL.value,
        ExportFormat.MARKDOWN.value,
    ]

    def __init__(
        self,
        assembler: Optional[ReportDataAssembler] = None,
        generator: Optional[GeologicalReportGenerator] = None,
        exporter: Optional[ReportExporter] = None,
    ):
        self.assembler = assembler or ReportDataAssembler(extraction_db)
        self.generator = generator or report_generator
        self.exporter = exporter or report_exporter

    def get_service_status(self) -> ReportStatusResponse:
        """Returns runtime status and telemetry for the reporting subsystem."""
        db_status = extraction_db.get_extraction_status()
        total_entities = db_status.get("total_entities_count", 0)

        return ReportStatusResponse(
            status="operational",
            phase="Phase 5 - Automated Geological Reporting Operational",
            report_templates=self.REPORT_TEMPLATES,
            export_formats=self.EXPORT_FORMATS,
            total_structured_entities_available=total_entities,
            is_ready=True,
        )

    def get_report_types(self) -> List[ReportTypeInfo]:
        """Returns list of supported report templates."""
        return self.REPORT_TEMPLATES

    def generate_report(self, request: ReportGenerationRequest) -> GeneratedReport:
        """
        Compiles structured Phase 4 records and produces a deterministic report.
        """
        # Determine human-friendly scope target string
        if request.scope == ReportScope.DOCUMENT:
            scope_target = request.source_document or request.document_id or "Selected Document"
        elif request.scope == ReportScope.PROJECT:
            scope_target = request.project_name or "Selected Project"
        else:
            scope_target = "Cumulative Ingested Dataset"

        # 1. Assemble Data
        data = self.assembler.assemble_data(
            scope=request.scope,
            document_id=request.document_id,
            source_document=request.source_document,
            project_name=request.project_name,
        )

        # 2. Generate Structured Report
        report = self.generator.generate(
            report_type=request.report_type,
            scope=request.scope,
            scope_target=scope_target,
            data=data,
            custom_title=request.custom_title,
        )

        return report

    def export_report_file(self, request: ReportExportRequest) -> tuple[bytes, str, str]:
        """
        Generates and exports the report into binary/text format.
        Returns: (file_bytes, media_type, filename)
        """
        report = self.generate_report(request)
        scope_slug = (report.metadata.scope_target or "report").replace(" ", "_").replace(".", "_")[:20]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")

        if request.export_format == ExportFormat.PDF:
            pdf_bytes = self.exporter.export_pdf(report)
            filename = f"CMPDI_{report.metadata.report_type.value}_{scope_slug}_{timestamp}.pdf"
            return pdf_bytes, "application/pdf", filename

        elif request.export_format == ExportFormat.EXCEL:
            excel_bytes = self.exporter.export_excel(report)
            filename = f"CMPDI_{report.metadata.report_type.value}_{scope_slug}_{timestamp}.xlsx"
            return excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename

        elif request.export_format == ExportFormat.MARKDOWN:
            md_text = self.exporter.export_markdown(report)
            filename = f"CMPDI_{report.metadata.report_type.value}_{scope_slug}_{timestamp}.md"
            return md_text.encode("utf-8"), "text/markdown; charset=utf-8", filename

        else:
            raise ValueError(f"Unsupported export format: {request.export_format}")


report_service = GeologicalReportGeneratorService()
