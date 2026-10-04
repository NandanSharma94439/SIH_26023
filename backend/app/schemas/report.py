"""
Pydantic Schemas for Phase 5: Automated Geological Reporting
SIH 2026 Problem Statement 26023 (CMPDI / Coal India Limited)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """Supported report generation types."""
    CMPDI_GEOLOGICAL_SUMMARY = "cmpdi_geological_summary"
    RESERVE_RECONCILIATION_MEMO = "reserve_reconciliation_memo"


class ReportScope(str, Enum):
    """Data scoping options for report compilation."""
    DOCUMENT = "document"
    PROJECT = "project"
    ALL = "all"


class ExportFormat(str, Enum):
    """Supported export binary / text formats."""
    PDF = "pdf"
    EXCEL = "excel"
    MARKDOWN = "markdown"


class ReportProvenanceItem(BaseModel):
    """Source provenance tracking for a factual entity used in a report."""
    document_id: str = Field(..., description="Source document identifier")
    source_document: str = Field(..., description="Source document filename")
    source_page: int = Field(..., description="1-indexed source page number")
    evidence_text: str = Field(..., description="Verbatim source sentence or tabular cell")
    entity_type: str = Field(..., description="Entity category: borehole, coal_seam, etc.")
    entity_id: str = Field(..., description="Record primary key or identifier")


class SeamReconciliationRow(BaseModel):
    """Detailed seam reconciliation record."""
    seam_id: str
    borehole_id: Optional[str] = None
    depth_from: Optional[float] = None
    depth_to: Optional[float] = None
    thickness: Optional[float] = None
    coal_grade: Optional[str] = None
    category: Optional[str] = None
    gross_reserves_mt: Optional[float] = None
    extractable_reserves_mt: Optional[float] = None
    recovery_percentage: Optional[float] = None
    mining_loss_mt: Optional[float] = None
    source_document: str
    source_page: int
    evidence_text: str


class ReportSection(BaseModel):
    """Structured report section containing tabular or key-value data."""
    section_id: str
    title: str
    summary_text: Optional[str] = None
    headers: Optional[List[str]] = None
    rows: Optional[List[List[Any]]] = None
    key_value_pairs: Optional[Dict[str, Any]] = None


class ReportMetadata(BaseModel):
    """Metadata block for generated reports."""
    report_id: str = Field(..., description="Unique generated report UUID")
    title: str = Field(..., description="Report title")
    report_type: ReportType = Field(..., description="Type of report generated")
    organization: str = Field("Central Mine Planning & Design Institute Limited (CMPDI)", description="Issuing authority")
    subsidiary: Optional[str] = Field(None, description="Operating CIL subsidiary")
    scope: ReportScope = Field(..., description="Data scoping used")
    scope_target: str = Field(..., description="Identifier or filename of target scope")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Generation timestamp")
    total_records_used: int = Field(0, description="Total Phase 4 relational entities consumed")


class ReportGenerationRequest(BaseModel):
    """Request payload to generate a report."""
    report_type: ReportType = Field(ReportType.CMPDI_GEOLOGICAL_SUMMARY, description="Template report type")
    scope: ReportScope = Field(ReportScope.ALL, description="Scope of data: document, project, or all")
    document_id: Optional[str] = Field(None, description="Filter by document ID if scope=document")
    source_document: Optional[str] = Field(None, description="Filter by source document filename if scope=document")
    project_name: Optional[str] = Field(None, description="Filter by mine/project name if scope=project")
    custom_title: Optional[str] = Field(None, description="Optional override title")


class ReportExportRequest(ReportGenerationRequest):
    """Request payload for exporting a report directly to a file format."""
    export_format: ExportFormat = Field(ExportFormat.PDF, description="Target export format")


class GeneratedReport(BaseModel):
    """Complete generated report with structured sections and rendered markdown."""
    metadata: ReportMetadata
    summary_statistics: Dict[str, Any] = Field(default_factory=dict)
    sections: List[ReportSection] = Field(default_factory=list)
    markdown_content: str = Field("", description="Pre-rendered markdown representation")
    provenance_sources: List[ReportProvenanceItem] = Field(default_factory=list)


class ReportTypeInfo(BaseModel):
    """Information regarding a supported report template."""
    id: str
    name: str
    description: str
    recommended_scopes: List[str]
    features: List[str]


class ReportStatusResponse(BaseModel):
    """Status telemetry for reporting subsystem."""
    status: str
    phase: str
    report_templates: List[ReportTypeInfo]
    export_formats: List[str]
    total_structured_entities_available: int
    is_ready: bool
