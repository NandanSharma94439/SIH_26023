"""
Phase 4 Domain Schemas: Structured Mining Data Extraction
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Defines validated Pydantic schemas with complete provenance:
- Coal Seam
- Borehole
- Proximate Analysis
- Mine/Project
- Geological Report Metrics
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class BaseExtractionEntity(BaseModel):
    """Base schema enforcing document and page-level provenance on every extracted entity."""
    id: Optional[str] = Field(default=None, description="Unique record identifier (UUID)")
    document_id: str = Field(..., description="ID of source processed document")
    source_document: str = Field(..., description="Filename of source document")
    source_page: int = Field(..., description="1-indexed source page number")
    evidence_text: str = Field(..., description="Verbatim source sentence or table row supporting extraction")
    extraction_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when extraction occurred"
    )


class CoalSeam(BaseExtractionEntity):
    """Relational model for coal seams and stratigraphy."""
    seam_id: str = Field(..., description="Identifier or code of the coal seam (e.g., 'Seam VIII', 'Seam VII (Top)')")
    borehole_id: Optional[str] = Field(default=None, description="Associated borehole identifier if drilled")
    depth_from: Optional[float] = Field(default=None, description="Top depth of seam in meters")
    depth_to: Optional[float] = Field(default=None, description="Bottom depth of seam in meters")
    thickness: Optional[float] = Field(default=None, description="True or clean thickness in meters")
    coal_grade: Optional[str] = Field(default=None, description="CIL coal grade classification (e.g., 'G-8', 'G-9')")
    category: Optional[str] = Field(default=None, description="Reserve categorization (e.g., 'Proved', 'Indicated')")
    gross_reserves_mt: Optional[float] = Field(default=None, description="Gross reserves in Million Tonnes (MT)")
    extractable_reserves_mt: Optional[float] = Field(default=None, description="Extractable reserves in Million Tonnes (MT)")


class ProximateAnalysis(BaseExtractionEntity):
    """Relational model for coal quality and proximate analysis parameters."""
    seam_id: Optional[str] = Field(default=None, description="Associated coal seam code or name")
    borehole_id: Optional[str] = Field(default=None, description="Associated borehole identifier")
    moisture_percent: Optional[float] = Field(default=None, description="Inherent moisture percentage (%)")
    ash_percent: Optional[float] = Field(default=None, description="Ash percentage (%)")
    volatile_matter_percent: Optional[float] = Field(default=None, description="Volatile matter percentage (%)")
    fixed_carbon_percent: Optional[float] = Field(default=None, description="Fixed carbon percentage (%)")
    gross_calorific_value: Optional[float] = Field(default=None, description="Gross Calorific Value (GCV)")
    units: Optional[str] = Field(default="kcal/kg", description="Measurement units for GCV and proximate parameters")


class Borehole(BaseExtractionEntity):
    """Relational model for borehole collar logs and drilling lithology."""
    borehole_id: str = Field(..., description="Official borehole identifier (e.g., 'BH-204', 'CM-101')")
    mine_project: Optional[str] = Field(default=None, description="Associated mine, project, or coalfield name")
    latitude: Optional[float] = Field(default=None, description="Collar latitude coordinates (WGS84)")
    longitude: Optional[float] = Field(default=None, description="Collar longitude coordinates (WGS84)")
    collar_elevation: Optional[float] = Field(default=None, description="Collar elevation in meters Relative Level (RL)")
    total_depth: Optional[float] = Field(default=None, description="Total depth drilled in meters")
    lithology: Optional[str] = Field(default=None, description="Summary or sequence lithology description")


class MineProject(BaseExtractionEntity):
    """Relational model for coal mining projects, feasibility blocks, and operations."""
    project_name: str = Field(..., description="Name of the mine, block, or feasibility project")
    subsidiary: Optional[str] = Field(default="CMPDI / CIL", description="Operating subsidiary or organization")
    location: Optional[str] = Field(default=None, description="Geographical or basin location")
    block_name: Optional[str] = Field(default=None, description="Exploratory block identifier")
    target_production: Optional[float] = Field(default=None, description="Target annual coal production")
    target_production_unit: Optional[str] = Field(default="MTPA", description="Unit of annual production")
    stripping_ratio: Optional[float] = Field(default=None, description="Overburden to coal stripping ratio (m3/t)")
    life_of_mine_years: Optional[int] = Field(default=None, description="Anticipated life of mine in years")


class GeologicalMetric(BaseExtractionEntity):
    """Relational model for reported exploration statistics, targets, and departmental metrics."""
    metric_name: str = Field(..., description="Name of the operational or exploration metric")
    metric_value: Optional[float] = Field(default=None, description="Numerical metric value")
    unit: Optional[str] = Field(default=None, description="Measurement unit (e.g., 'm', 'reports', '%')")
    year_period: Optional[str] = Field(default=None, description="Fiscal or reporting year period (e.g., '2006-07')")
    category: Optional[str] = Field(default=None, description="Categorization of metric (e.g., 'Exploration', 'Reports')")


# Aggregated extraction result models
class DocumentExtractionResult(BaseModel):
    """Response returned when extracting structured data from a single document."""
    document_id: str
    filename: str
    success: bool
    message: str
    extracted_counts: Dict[str, int]
    boreholes: List[Borehole] = Field(default_factory=list)
    coal_seams: List[CoalSeam] = Field(default_factory=list)
    proximate_analyses: List[ProximateAnalysis] = Field(default_factory=list)
    mine_projects: List[MineProject] = Field(default_factory=list)
    geological_metrics: List[GeologicalMetric] = Field(default_factory=list)


class ExtractionStatusResponse(BaseModel):
    """System-wide telemetry of extracted structured mining records."""
    status: str
    gemini_configured: bool
    total_entities_count: int
    counts_by_type: Dict[str, int]
    total_documents_extracted: int
    indexed_documents_count: int
