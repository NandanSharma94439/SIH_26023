"""
Analytics Domain Schemas (Phase 6)
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Pydantic schemas for:
- Summary KPI Telemetry
- Drilling Targets vs. Achievements (CMPDI, MECL, State Govts, X-Plan, Non-CIL)
- Coal Resource Classification & Reserves
- Mine / Project Analytics & Subsidiary Breakdowns
- Coal Quality (Proximate Analysis) Distributions & Averages
- Geological Metrics Explorer with Multi-Param Filtering
- Cross-Document Comparative Analytics
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProvenanceRecord(BaseModel):
    """Document and page-level audit trail for analytical figures."""
    source_document: str = Field(..., description="Filename or ID of the originating document")
    source_page: int = Field(..., description="1-indexed physical or logical page number")
    evidence_text: str = Field(..., description="Verbatim text quote from source document proving the figure")


class AnalyticsKPISummary(BaseModel):
    """High-level geological & exploration KPI summary."""
    total_mines_projects: int = Field(default=0, description="Total verified mines/projects")
    total_geological_metrics: int = Field(default=0, description="Total verified geological metrics")
    total_boreholes: int = Field(default=0, description="Total exploratory borehole logs")
    total_coal_seams: int = Field(default=0, description="Total coal seam records")
    total_proximate_analyses: int = Field(default=0, description="Total laboratory proximate analyses")
    total_entities: int = Field(default=0, description="Sum of all verified structured entities")
    
    # Core Drilling KPIs
    total_exploratory_drilling_achieved_m: Optional[float] = Field(None, description="Total exploratory drilling achieved in metres")
    total_exploratory_drilling_target_m: Optional[float] = Field(None, description="Total exploratory drilling target in metres")
    drilling_achievement_pct: Optional[float] = Field(None, description="Percentage of drilling target achieved")
    
    # Reports & Studies KPIs
    total_reports_prepared: Optional[int] = Field(None, description="Total reports and plans completed")
    geological_reports_count: Optional[int] = Field(None, description="Total geological exploration reports")
    
    # Coal Resources KPIs
    additional_coal_resources_bt: Optional[float] = Field(None, description="Total additional coal resources estimated (Bt)")
    proved_resources_bt: Optional[float] = Field(None, description="Proved category coal resources (Bt)")
    indicated_resources_bt: Optional[float] = Field(None, description="Indicated category coal resources (Bt)")
    
    # Borehole & Geophysical Logging KPIs
    boreholes_logged_count: Optional[int] = Field(None, description="Boreholes studied with multi-parametric geophysical logging")
    geophysical_logging_depth_m: Optional[float] = Field(None, description="Total geophysical logging depth in metres")
    
    source_scope: str = Field(default="all", description="Scope of analytics: 'all' or document name")
    provenance_map: Dict[str, ProvenanceRecord] = Field(default_factory=dict, description="Audit provenance for key KPI figures")


class DrillingAgencyItem(BaseModel):
    """Agency-wise exploratory drilling target vs. achievement."""
    agency: str = Field(..., description="Agency name (e.g. CMPDI Departmental, MECL Contractual, State Govts)")
    target: Optional[float] = Field(None, description="Target drilling value")
    achieved: Optional[float] = Field(None, description="Achieved drilling value")
    unit: str = Field(default="metre", description="Unit of measurement")
    achievement_pct: Optional[float] = Field(None, description="Achievement percentage (achieved / target * 100)")
    fiscal_period: Optional[str] = Field(None, description="Fiscal period or Plan (e.g. 2006-07 BE, X plan)")
    category: Optional[str] = Field(None, description="Drilling category classification")
    provenance: Optional[ProvenanceRecord] = Field(None, description="Audit trail for this figure")


class PromotionalBlockItem(BaseModel):
    """Promotional exploratory drilling broken down by coalfield block."""
    block_name: str = Field(..., description="Coalfield exploration block name")
    drilling_metres: float = Field(..., description="Drilling completed in metres")
    unit: str = Field(default="m", description="Unit of measurement")
    fiscal_period: Optional[str] = Field("2006-07", description="Fiscal year")
    provenance: Optional[ProvenanceRecord] = Field(None, description="Source provenance")


class NonCILCaptiveDrillingInfo(BaseModel):
    """Exploratory drilling in Non-CIL and Captive Mining Blocks."""
    drilling_metres: Optional[float] = Field(None, description="Total drilling in metres")
    blocks_count: Optional[int] = Field(None, description="Number of blocks explored")
    coalfields_count: Optional[int] = Field(None, description="Number of coalfields covered")
    reports_count: Optional[int] = Field(None, description="Detailed exploration reports prepared")
    fiscal_period: Optional[str] = Field(None, description="Fiscal year")
    provenance: Optional[ProvenanceRecord] = Field(None, description="Audit provenance")


class GeophysicalLoggingStats(BaseModel):
    """Geophysical logging and surface survey metrics."""
    boreholes_count: Optional[int] = Field(None, description="Boreholes studied with multi-parametric geophysical logging")
    logging_depth_metres: Optional[float] = Field(None, description="Total geophysical logging depth in metres")
    magnetic_survey_stations: Optional[float] = Field(None, description="Magnetic survey stations")
    resistivity_profiling_km: Optional[float] = Field(None, description="Surface resistivity profiling in line km")
    vertical_soundings_count: Optional[float] = Field(None, description="Vertical electrical soundings count")
    fiscal_period: Optional[str] = Field(None, description="Fiscal period")
    provenance: Optional[ProvenanceRecord] = Field(None, description="Audit provenance")


class DrillingAnalyticsResponse(BaseModel):
    """Comprehensive drilling analytics payload."""
    targets_vs_achievements: List[DrillingAgencyItem] = Field(default_factory=list)
    promotional_drilling_by_block: List[PromotionalBlockItem] = Field(default_factory=list)
    total_promotional_drilling_m: Optional[float] = Field(None, description="Sum of promotional drilling across blocks")
    non_cil_captive_blocks: Optional[NonCILCaptiveDrillingInfo] = None
    geophysical_logging: Optional[GeophysicalLoggingStats] = None
    source_scope: str = Field(default="all")


class ResourceCategoryItem(BaseModel):
    """Coal resource classification breakdown (Proved, Indicated, Inferred)."""
    category: str = Field(..., description="Resource confidence category (Proved, Indicated, Inferred, Additional)")
    value: float = Field(..., description="Estimated coal resource quantity")
    unit: str = Field(..., description="Unit (e.g. Billion Tonnes, Bt, MT)")
    fiscal_period: Optional[str] = Field(None, description="Fiscal assessment period")
    provenance: Optional[ProvenanceRecord] = Field(None, description="Audit provenance")


class SeamReserveItem(BaseModel):
    """Seam-by-seam geological reserve metrics."""
    seam_id: str = Field(..., description="Coal seam identifier")
    borehole_id: Optional[str] = Field(None, description="Borehole identifier if applicable")
    category: Optional[str] = Field(None, description="Reserve confidence category (Proved, Indicated)")
    gross_reserves_mt: Optional[float] = Field(None, description="Gross in-situ reserves in Million Tonnes")
    extractable_reserves_mt: Optional[float] = Field(None, description="Extractable reserves in Million Tonnes")
    recovery_factor_pct: Optional[float] = Field(None, description="Calculated recovery percentage")
    provenance: Optional[ProvenanceRecord] = Field(None, description="Audit provenance")


class ResourceAnalyticsResponse(BaseModel):
    """Coal resource and reserve distribution payload."""
    resource_categories: List[ResourceCategoryItem] = Field(default_factory=list)
    seam_reserves: List[SeamReserveItem] = Field(default_factory=list)
    total_additional_resources_bt: Optional[float] = Field(None, description="Total additional coal resources in Bt")
    source_scope: str = Field(default="all")


class SubsidiaryCountItem(BaseModel):
    """Subsidiary mine project distribution."""
    subsidiary: str = Field(..., description="Subsidiary name (e.g. CMPDI / CIL, CCL, WCL)")
    count: int = Field(..., description="Total mine/project records")


class ProjectAnalyticsItem(BaseModel):
    """Individual mine or project record with full attributes."""
    id: str
    project_name: str
    subsidiary: Optional[str] = None
    location: Optional[str] = None
    block_name: Optional[str] = None
    target_production: Optional[float] = None
    target_production_unit: Optional[str] = None
    stripping_ratio: Optional[float] = None
    life_of_mine_years: Optional[int] = None
    source_document: str
    source_page: int
    evidence_text: str


class ProjectAnalyticsResponse(BaseModel):
    """Project and mine analytics payload with filters and subsidiary breakdowns."""
    total_projects: int = Field(default=0)
    subsidiary_breakdown: List[SubsidiaryCountItem] = Field(default_factory=list)
    available_subsidiaries: List[str] = Field(default_factory=list)
    available_locations: List[str] = Field(default_factory=list)
    projects: List[ProjectAnalyticsItem] = Field(default_factory=list)
    source_scope: str = Field(default="all")


class ProximateQualityItem(BaseModel):
    """Laboratory proximate quality analysis record."""
    id: str
    seam_id: Optional[str] = None
    borehole_id: Optional[str] = None
    moisture_percent: Optional[float] = None
    ash_percent: Optional[float] = None
    volatile_matter_percent: Optional[float] = None
    fixed_carbon_percent: Optional[float] = None
    gross_calorific_value: Optional[float] = None
    units: Optional[str] = None
    source_document: str
    source_page: int
    evidence_text: str


class CoalQualityAverages(BaseModel):
    """Mean proximate analysis values across active scope."""
    avg_moisture_pct: Optional[float] = None
    avg_ash_pct: Optional[float] = None
    avg_volatile_matter_pct: Optional[float] = None
    avg_fixed_carbon_pct: Optional[float] = None
    avg_gcv: Optional[float] = None


class CoalQualityResponse(BaseModel):
    """Coal quality and proximate analysis payload."""
    has_data: bool = Field(..., description="True if records exist in scope; false if none")
    total_records: int = Field(default=0)
    records: List[ProximateQualityItem] = Field(default_factory=list)
    averages: Optional[CoalQualityAverages] = None
    source_scope: str = Field(default="all")
    empty_state_reason: Optional[str] = None


class GeologicalMetricItem(BaseModel):
    """Geological metric explorer item."""
    id: str
    metric_name: str
    metric_value: Optional[float] = None
    unit: Optional[str] = None
    year_period: Optional[str] = None
    category: Optional[str] = None
    source_document: str
    source_page: int
    evidence_text: str


class GeologicalMetricsResponse(BaseModel):
    """Paginated and searchable geological metrics explorer response."""
    total: int = Field(default=0)
    categories: List[str] = Field(default_factory=list)
    units: List[str] = Field(default_factory=list)
    metrics: List[GeologicalMetricItem] = Field(default_factory=list)
    source_scope: str = Field(default="all")


class DocumentEntityBreakdown(BaseModel):
    """Structured entity breakdown per document."""
    document: str
    mines_projects: int
    boreholes: int
    coal_seams: int
    proximate_analyses: int
    geological_metrics: int
    total_entities: int


class CompatibleMetricComparison(BaseModel):
    """Cross-document comparison for a compatible metric with strict unit alignment."""
    metric_name: str
    unit: str
    category: Optional[str] = None
    values_by_document: Dict[str, Optional[float]] = Field(default_factory=dict)
    provenance_by_document: Dict[str, Optional[ProvenanceRecord]] = Field(default_factory=dict)


class CrossDocumentComparisonResponse(BaseModel):
    """Cross-document analytics comparison payload."""
    compared_documents: List[str] = Field(default_factory=list)
    entity_breakdown: List[DocumentEntityBreakdown] = Field(default_factory=list)
    compatible_metrics: List[CompatibleMetricComparison] = Field(default_factory=list)
    incompatible_metrics_note: Optional[str] = None
