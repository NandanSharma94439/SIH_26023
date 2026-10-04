"""
Report Generator Engine for Phase 5: Automated Geological Reporting
SIH 2026 Problem Statement 26023 (CMPDI / Coal India Limited)

Builds CMPDI Geological Summary Reports and Seam-by-Seam Reserve Reconciliation Memos
using validated Phase 4 records, preserving exact provenance and missing-value fidelity.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.schemas.report import (
    ReportType,
    ReportScope,
    ReportMetadata,
    ReportSection,
    GeneratedReport,
    ReportProvenanceItem,
    SeamReconciliationRow,
)
from app.schemas.extraction import (
    MineProject,
    Borehole,
    CoalSeam,
    ProximateAnalysis,
    GeologicalMetric,
)


class GeologicalReportGenerator:
    """Deterministic geological report generator for CMPDI and CIL planning departments."""

    def generate(
        self,
        report_type: ReportType,
        scope: ReportScope,
        scope_target: str,
        data: Dict[str, Any],
        custom_title: Optional[str] = None,
    ) -> GeneratedReport:
        """Generates a complete structured report with metadata, sections, and markdown representation."""
        report_id = str(uuid.uuid4())
        mines: List[MineProject] = data["mines"]
        boreholes: List[Borehole] = data["boreholes"]
        seams: List[CoalSeam] = data["seams"]
        proximate: List[ProximateAnalysis] = data["proximate"]
        metrics: List[GeologicalMetric] = data["metrics"]
        reconciliation_rows: List[SeamReconciliationRow] = data["reconciliation_rows"]
        provenance_sources: List[ReportProvenanceItem] = data["provenance_sources"]

        # Compute summary statistics
        stats = self._compute_summary_statistics(mines, boreholes, seams, proximate, metrics, reconciliation_rows)

        # Determine subsidiary
        subsidiary = None
        for m in mines:
            if m.subsidiary:
                subsidiary = m.subsidiary
                break
        if not subsidiary:
            subsidiary = "Central Mine Planning & Design Institute / CIL"

        # Determine default title
        if custom_title and custom_title.strip():
            title = custom_title.strip()
        elif report_type == ReportType.CMPDI_GEOLOGICAL_SUMMARY:
            title = f"CMPDI Geological Summary Report: {scope_target}"
        else:
            title = f"Seam-by-Seam Reserve Reconciliation Memo: {scope_target}"

        metadata = ReportMetadata(
            report_id=report_id,
            title=title,
            report_type=report_type,
            organization="Central Mine Planning & Design Institute Limited (CMPDI)",
            subsidiary=subsidiary,
            scope=scope,
            scope_target=scope_target,
            generated_at=datetime.now(timezone.utc),
            total_records_used=data["total_records"],
        )

        if report_type == ReportType.CMPDI_GEOLOGICAL_SUMMARY:
            sections = self._build_geological_summary_sections(mines, boreholes, seams, proximate, metrics, stats)
        else:
            sections = self._build_reserve_reconciliation_sections(seams, reconciliation_rows, boreholes, proximate, stats)

        # Render Markdown
        markdown_content = self._render_markdown(metadata, stats, sections, provenance_sources)

        return GeneratedReport(
            metadata=metadata,
            summary_statistics=stats,
            sections=sections,
            markdown_content=markdown_content,
            provenance_sources=provenance_sources,
        )

    def _compute_summary_statistics(
        self,
        mines: List[MineProject],
        boreholes: List[Borehole],
        seams: List[CoalSeam],
        proximate: List[ProximateAnalysis],
        metrics: List[GeologicalMetric],
        reconciliation_rows: List[SeamReconciliationRow],
    ) -> Dict[str, Any]:
        """Calculates factual aggregate statistics without fabricating missing values."""
        gross_reserves = [s.gross_reserves_mt for s in seams if s.gross_reserves_mt is not None]
        extractable_reserves = [s.extractable_reserves_mt for s in seams if s.extractable_reserves_mt is not None]
        thicknesses = [s.thickness for s in seams if s.thickness is not None]
        depths = [b.total_depth for b in boreholes if b.total_depth is not None]
        ash_vals = [p.ash_percent for p in proximate if p.ash_percent is not None]
        gcv_vals = [p.gross_calorific_value for p in proximate if p.gross_calorific_value is not None]

        total_gross = round(sum(gross_reserves), 2) if gross_reserves else None
        total_extractable = round(sum(extractable_reserves), 2) if extractable_reserves else None
        overall_recovery = None
        if total_gross and total_extractable and total_gross > 0:
            overall_recovery = round((total_extractable / total_gross) * 100.0, 2)

        return {
            "total_mines_projects": len(mines),
            "total_boreholes_logged": len(boreholes),
            "total_seams_analyzed": len(seams),
            "total_proximate_records": len(proximate),
            "total_geological_metrics": len(metrics),
            "total_gross_reserves_mt": total_gross,
            "total_extractable_reserves_mt": total_extractable,
            "overall_recovery_percentage": overall_recovery,
            "mean_seam_thickness_m": round(sum(thicknesses) / len(thicknesses), 2) if thicknesses else None,
            "max_borehole_depth_m": max(depths) if depths else None,
            "average_ash_percentage": round(sum(ash_vals) / len(ash_vals), 2) if ash_vals else None,
            "average_gcv_kcal_kg": round(sum(gcv_vals) / len(gcv_vals), 1) if gcv_vals else None,
        }

    def _build_geological_summary_sections(
        self,
        mines: List[MineProject],
        boreholes: List[Borehole],
        seams: List[CoalSeam],
        proximate: List[ProximateAnalysis],
        metrics: List[GeologicalMetric],
        stats: Dict[str, Any],
    ) -> List[ReportSection]:
        """Constructs sections for CMPDI Geological Summary Report."""
        sections: List[ReportSection] = []

        # 1. Executive Summary & Mine Overview
        mine_rows = []
        for m in mines:
            mine_rows.append([
                m.project_name or "N/A",
                m.subsidiary or "N/A",
                m.location or m.block_name or "N/A",
                f"{m.target_production} {m.target_production_unit or 'MTPA'}" if m.target_production is not None else "N/A",
                f"{m.stripping_ratio}:1" if m.stripping_ratio is not None else "N/A",
                f"{m.life_of_mine_years} Yrs" if m.life_of_mine_years is not None else "N/A",
                f"{m.source_document} (p. {m.source_page})",
            ])

        sections.append(
            ReportSection(
                section_id="mine_planning_overview",
                title="1. Mine Planning & Project Feasibility Parameters",
                summary_text=(
                    f"Operational parameters extracted from verified exploration reports. "
                    f"Identified {len(mines)} project/mine blocks with stripping ratios and production capacities."
                    if mines else "No mine or project feasibility records available in the selected data scope."
                ),
                headers=["Project Name", "Subsidiary", "Location / Block", "Target Production", "Stripping Ratio", "Life of Mine", "Provenance"],
                rows=mine_rows,
            )
        )

        # 2. Stratigraphic & Borehole Exploratory Data
        borehole_rows = []
        for b in boreholes:
            borehole_rows.append([
                b.borehole_id,
                b.mine_project or "N/A",
                f"{b.collar_elevation} m RL" if b.collar_elevation is not None else "N/A",
                f"{b.total_depth} m" if b.total_depth is not None else "N/A",
                b.lithology or "N/A",
                f"{b.source_document} (p. {b.source_page})",
            ])

        sections.append(
            ReportSection(
                section_id="stratigraphic_borehole_data",
                title="2. Exploratory Borehole Collar & Lithology Logs",
                summary_text=(
                    f"Logged {len(boreholes)} exploration boreholes with collar coordinates and lithological strata descriptions. "
                    f"Maximum drilled depth reached: {stats['max_borehole_depth_m']} m."
                    if boreholes else "No exploratory borehole records found in the selected data scope."
                ),
                headers=["Borehole ID", "Mine / Area", "Collar Elevation", "Total Depth", "Lithology Strata", "Provenance"],
                rows=borehole_rows,
            )
        )

        # 3. Coal Seam Stratigraphy & Reserves
        seam_rows = []
        for s in seams:
            seam_rows.append([
                s.seam_id,
                s.borehole_id or "N/A",
                f"{s.depth_from} m" if s.depth_from is not None else "N/A",
                f"{s.depth_to} m" if s.depth_to is not None else "N/A",
                f"{s.thickness} m" if s.thickness is not None else "N/A",
                s.coal_grade or "N/A",
                s.category or "N/A",
                f"{s.gross_reserves_mt} MT" if s.gross_reserves_mt is not None else "N/A",
                f"{s.extractable_reserves_mt} MT" if s.extractable_reserves_mt is not None else "N/A",
                f"{s.source_document} (p. {s.source_page})",
            ])

        sections.append(
            ReportSection(
                section_id="coal_seam_stratigraphy",
                title="3. Coal Seam Stratigraphy & Reserve Classification",
                summary_text=(
                    f"Identified {len(seams)} coal seams. "
                    f"Total Gross Reserves: {stats['total_gross_reserves_mt'] or 'N/A'} MT, "
                    f"Total Extractable Reserves: {stats['total_extractable_reserves_mt'] or 'N/A'} MT. "
                    f"Mean Seam Thickness: {stats['mean_seam_thickness_m'] or 'N/A'} m."
                    if seams else "No coal seam stratigraphy records found in the selected data scope."
                ),
                headers=["Seam Code", "Borehole ID", "Depth From", "Depth To", "Thickness", "Grade", "Category", "Gross (MT)", "Extractable (MT)", "Provenance"],
                rows=seam_rows,
            )
        )

        # 4. Coal Quality & Proximate Analysis
        prox_rows = []
        for p in proximate:
            prox_rows.append([
                p.seam_id or "N/A",
                p.borehole_id or "N/A",
                f"{p.moisture_percent}%" if p.moisture_percent is not None else "N/A",
                f"{p.ash_percent}%" if p.ash_percent is not None else "N/A",
                f"{p.volatile_matter_percent}%" if p.volatile_matter_percent is not None else "N/A",
                f"{p.fixed_carbon_percent}%" if p.fixed_carbon_percent is not None else "N/A",
                f"{p.gross_calorific_value} {p.units or 'kcal/kg'}" if p.gross_calorific_value is not None else "N/A",
                f"{p.source_document} (p. {p.source_page})",
            ])

        sections.append(
            ReportSection(
                section_id="proximate_analysis_summary",
                title="4. Coal Quality & Proximate Analysis Parameters",
                summary_text=(
                    f"Proximate analysis evaluations for {len(proximate)} samples. "
                    f"Average Ash Content: {stats['average_ash_percentage'] or 'N/A'}%, "
                    f"Average Gross Calorific Value: {stats['average_gcv_kcal_kg'] or 'N/A'} kcal/kg."
                    if proximate else "No proximate quality analysis records found in the selected data scope."
                ),
                headers=["Seam Code", "Borehole ID", "Moisture %", "Ash %", "Volatile Matter %", "Fixed Carbon %", "GCV", "Provenance"],
                rows=prox_rows,
            )
        )

        # 5. Exploration & Departmental Metrics
        metric_rows = []
        for g in metrics:
            metric_rows.append([
                g.metric_name,
                f"{g.metric_value:,.2f}" if isinstance(g.metric_value, float) and not g.metric_value.is_integer() else f"{int(g.metric_value):,}" if g.metric_value is not None else "N/A",
                g.unit or "N/A",
                g.year_period or "N/A",
                g.category or "N/A",
                f"{g.source_document} (p. {g.source_page})",
            ])

        sections.append(
            ReportSection(
                section_id="geological_metrics_summary",
                title="5. Exploration Achievements & Geological Metrics",
                summary_text=(
                    f"Departmental targets, drilling statistics, and statutory reports submitted. Total metrics: {len(metrics)}."
                    if metrics else "No exploration metrics found in the selected data scope."
                ),
                headers=["Metric Description", "Reported Value", "Unit", "Fiscal Period", "Category", "Provenance"],
                rows=metric_rows,
            )
        )

        return sections

    def _build_reserve_reconciliation_sections(
        self,
        seams: List[CoalSeam],
        reconciliation_rows: List[SeamReconciliationRow],
        boreholes: List[Borehole],
        proximate: List[ProximateAnalysis],
        stats: Dict[str, Any],
    ) -> List[ReportSection]:
        """Constructs sections for Seam-by-Seam Reserve Reconciliation Memo."""
        sections: List[ReportSection] = []

        # 1. Seam-by-Seam Detailed Reconciliation
        recon_rows = []
        for r in reconciliation_rows:
            recon_rows.append([
                r.seam_id,
                r.borehole_id or "N/A",
                f"{r.depth_from} m" if r.depth_from is not None else "N/A",
                f"{r.depth_to} m" if r.depth_to is not None else "N/A",
                f"{r.thickness} m" if r.thickness is not None else "N/A",
                r.coal_grade or "N/A",
                r.category or "N/A",
                f"{r.gross_reserves_mt} MT" if r.gross_reserves_mt is not None else "N/A",
                f"{r.extractable_reserves_mt} MT" if r.extractable_reserves_mt is not None else "N/A",
                f"{r.recovery_percentage}%" if r.recovery_percentage is not None else "N/A",
                f"{r.mining_loss_mt} MT" if r.mining_loss_mt is not None else "N/A",
                f"{r.source_document} (p. {r.source_page})",
            ])

        sections.append(
            ReportSection(
                section_id="seam_reserve_reconciliation_table",
                title="1. Seam-by-Seam Reserve Reconciliation & Extraction Factors",
                summary_text=(
                    f"Comprehensive seam correlation across exploratory boreholes. "
                    f"Reconciled {len(reconciliation_rows)} seam occurrences. "
                    f"Total Gross: {stats['total_gross_reserves_mt'] or 'N/A'} MT | "
                    f"Total Extractable: {stats['total_extractable_reserves_mt'] or 'N/A'} MT | "
                    f"Overall Recovery Factor: {stats['overall_recovery_percentage'] or 'N/A'}%."
                    if reconciliation_rows else "No seam records available to calculate reserve reconciliation."
                ),
                headers=["Seam ID", "Borehole", "From", "To", "Thickness", "Grade", "Category", "Gross (MT)", "Extractable (MT)", "Recovery %", "Mining Loss", "Provenance"],
                rows=recon_rows,
            )
        )

        # 2. Correlated Stratigraphic Strata
        bh_map = {}
        for b in boreholes:
            bh_map[b.borehole_id] = b

        seam_strat_rows = []
        for s in seams:
            bh = bh_map.get(s.borehole_id)
            seam_strat_rows.append([
                s.seam_id,
                s.borehole_id or "Regional",
                f"{bh.collar_elevation} m RL" if bh and bh.collar_elevation is not None else "N/A",
                f"{s.depth_from} m" if s.depth_from is not None else "N/A",
                f"{s.depth_to} m" if s.depth_to is not None else "N/A",
                f"{s.thickness} m" if s.thickness is not None else "N/A",
                s.coal_grade or "N/A",
                bh.lithology or "N/A" if bh else "Strata not logged",
            ])

        sections.append(
            ReportSection(
                section_id="correlated_stratigraphy",
                title="2. Correlated Stratigraphic Control & Strata Context",
                summary_text="Lithological strata context directly linked to coal seam depths and borehole collars.",
                headers=["Seam ID", "Borehole ID", "Collar RL", "Depth From", "Depth To", "Thickness", "Grade", "Lithology Context"],
                rows=seam_strat_rows,
            )
        )

        # 3. Quality & Proximate Matrix
        prox_rows = []
        for p in proximate:
            prox_rows.append([
                p.seam_id or "N/A",
                p.borehole_id or "N/A",
                f"{p.ash_percent}%" if p.ash_percent is not None else "N/A",
                f"{p.moisture_percent}%" if p.moisture_percent is not None else "N/A",
                f"{p.volatile_matter_percent}%" if p.volatile_matter_percent is not None else "N/A",
                f"{p.gross_calorific_value} {p.units or 'kcal/kg'}" if p.gross_calorific_value is not None else "N/A",
                f"{p.source_document} (p. {p.source_page})",
            ])

        sections.append(
            ReportSection(
                section_id="reconciliation_quality_matrix",
                title="3. Coal Quality Verification & Proximate Matrix",
                summary_text="Laboratory proximate quality parameters supporting reserve grade classification.",
                headers=["Seam Code", "Borehole", "Ash %", "Moisture %", "Volatile Matter %", "GCV", "Provenance"],
                rows=prox_rows,
            )
        )

        return sections

    def _render_markdown(
        self,
        metadata: ReportMetadata,
        stats: Dict[str, Any],
        sections: List[ReportSection],
        provenance_sources: List[ReportProvenanceItem],
    ) -> str:
        """Renders GitHub-flavored markdown representation with tables and citations."""
        lines = []

        # Header Block
        lines.append(f"# {metadata.title}")
        lines.append(f"**Issuing Authority**: {metadata.organization}  ")
        lines.append(f"**Operating Subsidiary**: {metadata.subsidiary or 'Coal India Limited'}  ")
        lines.append(f"**Report Type**: {metadata.report_type.value.replace('_', ' ').title()}  ")
        lines.append(f"**Data Scope**: {metadata.scope.value.upper()} (`{metadata.scope_target}`)  ")
        lines.append(f"**Date Generated**: {metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
        lines.append(f"**Report Identifier**: `{metadata.report_id}`  ")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Executive Highlights
        lines.append("## Executive Highlights")
        lines.append("")
        lines.append(f"- **Total Extracted Records Consumed**: {metadata.total_records_used}")
        lines.append(f"- **Mines & Projects Evaluated**: {stats['total_mines_projects']}")
        lines.append(f"- **Exploratory Boreholes Cited**: {stats['total_boreholes_logged']}")
        lines.append(f"- **Coal Seams Correlated**: {stats['total_seams_analyzed']}")
        if stats["total_gross_reserves_mt"] is not None:
            lines.append(f"- **Gross In-Situ Reserves**: {stats['total_gross_reserves_mt']:,} MT")
        if stats["total_extractable_reserves_mt"] is not None:
            lines.append(f"- **Extractable Coal Reserves**: {stats['total_extractable_reserves_mt']:,} MT")
        if stats["overall_recovery_percentage"] is not None:
            lines.append(f"- **Estimated Mining Recovery Factor**: {stats['overall_recovery_percentage']}%")
        if stats["mean_seam_thickness_m"] is not None:
            lines.append(f"- **Mean Seam True Thickness**: {stats['mean_seam_thickness_m']} m")
        if stats["average_ash_percentage"] is not None:
            lines.append(f"- **Average Ash Content**: {stats['average_ash_percentage']}%")
        if stats["average_gcv_kcal_kg"] is not None:
            lines.append(f"- **Average Gross Calorific Value (GCV)**: {stats['average_gcv_kcal_kg']:,} kcal/kg")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Render Each Section
        for sec in sections:
            lines.append(f"## {sec.title}")
            lines.append("")
            if sec.summary_text:
                lines.append(f"> {sec.summary_text}")
                lines.append("")

            if sec.headers and sec.rows:
                # Markdown Table
                lines.append("| " + " | ".join(sec.headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(sec.headers)) + " |")
                for row in sec.rows:
                    cleaned_row = [str(val).replace("|", "/") if val is not None else "N/A" for val in row]
                    lines.append("| " + " | ".join(cleaned_row) + " |")
                lines.append("")
            elif not sec.rows:
                lines.append("*No records available for this section in the specified data scope.*")
                lines.append("")

        # Section: Provenance & Statutory Audit Trail
        lines.append("## Provenance & Statutory Audit Trail")
        lines.append("")
        lines.append("Every factual metric presented in this report is directly grounded in verified primary documents:")
        lines.append("")

        if provenance_sources:
            lines.append("| Source Document | Page | Entity Category | Verifiable Evidence Quote |")
            lines.append("| --- | ---: | --- | --- |")
            for p in provenance_sources:
                evidence_clean = p.evidence_text.replace("\n", " ").replace("|", "/")
                if len(evidence_clean) > 90:
                    evidence_clean = evidence_clean[:87] + "..."
                lines.append(f"| `{p.source_document}` | {p.source_page} | {p.entity_type} | *\"{evidence_clean}\"* |")
            lines.append("")
        else:
            lines.append("*No primary document provenance citations registered for this scope.*")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("**Confidentiality & Compliance**: Prepared under CMPDI / CIL Exploration Standards. "
                     "Automated compilation via GeoMine Intelligence Platform.")

        return "\n".join(lines)


report_generator = GeologicalReportGenerator()
