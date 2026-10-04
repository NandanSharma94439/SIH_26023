"""
Benchmark & Validation Schemas
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Pydantic models for:
1. Report-preparation time reduction & user baseline measurement
2. Extraction accuracy & ground-truth validation
3. Workflow automation coverage calculation
4. Multi-format benchmark export
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Report Preparation Time Reduction
# ---------------------------------------------------------------------------
class ManualTimeInput(BaseModel):
    """User-entered manual baseline time for a specific report."""
    report_type: str = Field(default="cmpdi_geological_summary", description="Report template ID")
    scope: str = Field(default="all", description="Report scope: all, document, project")
    source_document: Optional[str] = Field(None, description="Optional document filename")
    manual_time_minutes: float = Field(..., description="Measured manual preparation time in minutes")


class ReportTimeBenchmarkItem(BaseModel):
    """Detailed time comparison record for report preparation."""
    report_type: str = Field(..., description="Report template name")
    scope: str = Field(..., description="Scope of the report")
    source_document: Optional[str] = Field(None, description="Document filename if scoped")
    source_documents_count: int = Field(..., description="Number of source documents aggregated")
    manual_time_minutes: Optional[float] = Field(None, description="User-entered manual baseline (minutes)")
    geomine_time_seconds: float = Field(..., description="System-measured automated preparation time (seconds)")
    geomine_time_minutes: float = Field(..., description="System-measured automated preparation time (minutes)")
    time_saved_minutes: Optional[float] = Field(None, description="Manual Time - GeoMine Time (minutes)")
    time_reduction_percent: Optional[float] = Field(None, description="((Manual - GeoMine) / Manual) * 100")
    measurement_date: str = Field(..., description="ISO timestamp of system measurement")
    status: Literal["measured_with_user_baseline", "awaiting_user_baseline"] = Field(
        ..., description="Whether manual baseline has been supplied by evaluator"
    )


class TimeReductionSummary(BaseModel):
    """Summary of time reduction benchmarks across tested report types."""
    benchmarks: List[ReportTimeBenchmarkItem] = Field(default_factory=list)
    average_reduction_percent: Optional[float] = Field(None, description="Mean reduction across baselined reports")
    total_time_saved_minutes: Optional[float] = Field(None, description="Sum of time saved across baselined reports")
    methodology: str = Field(..., description="Explanation of measurement approach")


# ---------------------------------------------------------------------------
# 2. Extraction & Report Accuracy
# ---------------------------------------------------------------------------
class GroundTruthField(BaseModel):
    """Single verified ground-truth data point compared against system output."""
    field_name: str = Field(..., description="Human-readable field identifier")
    category: str = Field(..., description="Entity category (Borehole, Coal Seam, Proximate, etc.)")
    source_document: str = Field(..., description="Canonical source filename")
    source_page: Optional[int] = Field(None, description="Page number in canonical source")
    ground_truth_value: str = Field(..., description="Verified canonical ground-truth value")
    system_output_value: Optional[str] = Field(None, description="Value extracted by GeoMine system")
    is_correct: bool = Field(..., description="Whether system output matches ground truth")
    evidence_snippet: Optional[str] = Field(None, description="Verbatim text supporting ground truth")


class CategoryAccuracy(BaseModel):
    """Accuracy metrics for a specific domain entity category."""
    category: str = Field(..., description="Category name")
    tested_fields_count: int = Field(..., description="Number of tested ground truth fields")
    correct_fields_count: int = Field(..., description="Number of accurately extracted fields")
    accuracy_percent: Optional[float] = Field(None, description="Percentage of correct fields (0-100)")
    has_sufficient_samples: bool = Field(..., description="True if sample size >= 3")
    sample_status: str = Field(..., description="OK or 'Not enough validated samples'")


class AccuracyBenchmarkResponse(BaseModel):
    """Overall ground-truth extraction and report correctness validation."""
    total_fields_tested: int = Field(..., description="Total ground-truth fields evaluated")
    total_correct_fields: int = Field(..., description="Total fields matching ground truth")
    overall_extraction_accuracy_percent: float = Field(..., description="Overall field accuracy %")
    category_breakdown: List[CategoryAccuracy] = Field(default_factory=list)
    ground_truth_dataset: List[GroundTruthField] = Field(default_factory=list)
    report_generation_correctness: Dict[str, Any] = Field(
        ..., description="Verification of compiled report sections and provenance citations"
    )
    methodology: str = Field(..., description="Explanation of ground-truth validation methodology")


# ---------------------------------------------------------------------------
# 3. Automation Percentage
# ---------------------------------------------------------------------------
class WorkflowStep(BaseModel):
    """Single workflow stage with automation classification and justification."""
    step_number: int = Field(..., description="Workflow sequence index (1-12)")
    step_name: str = Field(..., description="Title of the workflow stage")
    lifecycle_phase: str = Field(..., description="Ingestion, Extraction, Synthesis, or Export")
    classification: Literal["Automated", "Partially Automated", "Human Required"] = Field(
        ..., description="Degree of automation"
    )
    description: str = Field(..., description="What the system executes at this stage")
    automation_rationale: str = Field(..., description="Technical justification for classification")
    system_capability: str = Field(..., description="Underlying GeoMine module or engine")


class AutomationCoverageResponse(BaseModel):
    """Comprehensive automation coverage analysis across the 12-step reporting workflow."""
    total_workflow_steps: int = Field(default=12, description="Total steps in end-to-end workflow")
    automated_steps_count: int = Field(..., description="Number of fully automated stages")
    partially_automated_steps_count: int = Field(..., description="Number of partially automated stages")
    human_required_steps_count: int = Field(..., description="Number of human-required stages")
    strict_automation_coverage_percent: float = Field(
        ..., description="Automated steps / Total steps * 100"
    )
    weighted_automation_coverage_percent: float = Field(
        ..., description="(Automated * 1.0 + Partial * 0.5) / Total steps * 100"
    )
    formula_definitions: Dict[str, str] = Field(..., description="Mathematical definitions of both formulas")
    workflow_steps: List[WorkflowStep] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Unified Benchmark Summary
# ---------------------------------------------------------------------------
class UnifiedBenchmarkSummary(BaseModel):
    """Complete SIH-26023 benchmark telemetry response."""
    time_reduction: TimeReductionSummary
    extraction_accuracy: AccuracyBenchmarkResponse
    automation_coverage: AutomationCoverageResponse
    generated_at: str
