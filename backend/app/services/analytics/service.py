"""
Analytics & Visualization Service Layer (Phase 6)
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Directly queries the verified SQLite relational database (extraction.db).
Zero synthetic data, strict provenance preservation, and safe parameterized SQL.
"""

from typing import List, Optional, Dict, Any, Tuple
import sqlite3

from app.services.extraction.db import extraction_db
from app.schemas.analytics import (
    ProvenanceRecord,
    AnalyticsKPISummary,
    DrillingAgencyItem,
    PromotionalBlockItem,
    NonCILCaptiveDrillingInfo,
    GeophysicalLoggingStats,
    DrillingAnalyticsResponse,
    ResourceCategoryItem,
    SeamReserveItem,
    ResourceAnalyticsResponse,
    SubsidiaryCountItem,
    ProjectAnalyticsItem,
    ProjectAnalyticsResponse,
    ProximateQualityItem,
    CoalQualityAverages,
    CoalQualityResponse,
    GeologicalMetricItem,
    GeologicalMetricsResponse,
    DocumentEntityBreakdown,
    CompatibleMetricComparison,
    CrossDocumentComparisonResponse,
)


class AnalyticsService:
    """Core analytical calculations and visualizations engine for CMPDI data."""

    def __init__(self, db=None):
        self.db = db or extraction_db

    def _get_connection(self) -> sqlite3.Connection:
        return self.db._get_connection()

    def _build_doc_filter(
        self, document_id: Optional[str] = None, source_document: Optional[str] = None
    ) -> Tuple[str, List[Any], str]:
        """Builds safe, parameterized SQL snippet for document filtering."""
        params: List[Any] = []
        clause = ""
        scope_label = "all"

        # Check if caller passed 'all' or empty
        target = source_document or document_id
        if target and target.strip().lower() not in ("all", "*", ""):
            clean_target = target.strip()
            # Match either exact document_id, exact source_document, or filename substring
            clause = " AND (document_id = ? OR source_document = ? OR source_document LIKE ?)"
            params.extend([clean_target, clean_target, f"%{clean_target}%"])
            scope_label = clean_target

        return clause, params, scope_label

    def get_summary(
        self, document_id: Optional[str] = None, source_document: Optional[str] = None
    ) -> AnalyticsKPISummary:
        """Returns consolidated KPI summary from extraction.db with complete provenance."""
        filter_sql, params, scope_label = self._build_doc_filter(document_id, source_document)

        with self._get_connection() as conn:
            # 1. Total entities counts
            m_count = conn.execute(
                f"SELECT count(1) FROM mines_projects WHERE 1=1 {filter_sql}", params
            ).fetchone()[0]
            g_count = conn.execute(
                f"SELECT count(1) FROM geological_metrics WHERE 1=1 {filter_sql}", params
            ).fetchone()[0]
            b_count = conn.execute(
                f"SELECT count(1) FROM boreholes WHERE 1=1 {filter_sql}", params
            ).fetchone()[0]
            s_count = conn.execute(
                f"SELECT count(1) FROM coal_seams WHERE 1=1 {filter_sql}", params
            ).fetchone()[0]
            p_count = conn.execute(
                f"SELECT count(1) FROM proximate_analyses WHERE 1=1 {filter_sql}", params
            ).fetchone()[0]
            total_entities = m_count + g_count + b_count + s_count + p_count

            # 2. Extract key metrics from geological_metrics table
            metrics_rows = conn.execute(
                f"SELECT metric_name, metric_value, unit, year_period, category, source_document, source_page, evidence_text "
                f"FROM geological_metrics WHERE 1=1 {filter_sql}",
                params,
            ).fetchall()

            metrics_map: Dict[str, Any] = {}
            prov_map: Dict[str, ProvenanceRecord] = {}

            for r in metrics_rows:
                name = r["metric_name"].strip()
                val = r["metric_value"]
                metrics_map[name] = val
                prov_map[name] = ProvenanceRecord(
                    source_document=r["source_document"],
                    source_page=r["source_page"],
                    evidence_text=r["evidence_text"] or "",
                )

            # Drilling KPIs
            drilling_achieved = metrics_map.get("Total Exploratory Drilling Achieved")
            drilling_target = metrics_map.get("Total Exploratory Drilling Target")
            drilling_pct = None
            if drilling_achieved is not None and drilling_target and drilling_target > 0:
                drilling_pct = round((drilling_achieved / drilling_target) * 100, 2)

            # Reports KPIs
            total_reports = metrics_map.get("TOTAL")
            if total_reports is not None:
                total_reports = int(total_reports)
            
            geo_reports = (
                metrics_map.get("GEOLOGICAL REPORTS")
                or metrics_map.get("Geological Reports on coal exploration")
            )
            if geo_reports is not None:
                geo_reports = int(geo_reports)

            # Resources KPIs
            add_resources = metrics_map.get("Additional coal resources estimated")
            proved_res = metrics_map.get("Proved category coal resources")
            ind_res = metrics_map.get("Indicated category coal resources")

            # Logging KPIs
            boreholes_logged = metrics_map.get("Boreholes studied with multi-parametric geophysical logging")
            if boreholes_logged is not None:
                boreholes_logged = int(boreholes_logged)
            logging_depth = metrics_map.get("Geophysical logging depth metre")

            return AnalyticsKPISummary(
                total_mines_projects=m_count,
                total_geological_metrics=g_count,
                total_boreholes=b_count,
                total_coal_seams=s_count,
                total_proximate_analyses=p_count,
                total_entities=total_entities,
                total_exploratory_drilling_achieved_m=drilling_achieved,
                total_exploratory_drilling_target_m=drilling_target,
                drilling_achievement_pct=drilling_pct,
                total_reports_prepared=total_reports,
                geological_reports_count=geo_reports,
                additional_coal_resources_bt=add_resources,
                proved_resources_bt=proved_res,
                indicated_resources_bt=ind_res,
                boreholes_logged_count=boreholes_logged,
                geophysical_logging_depth_m=logging_depth,
                source_scope=scope_label,
                provenance_map=prov_map,
            )

    def get_drilling_analytics(
        self, document_id: Optional[str] = None, source_document: Optional[str] = None
    ) -> DrillingAnalyticsResponse:
        """Returns structured drilling targets vs achievements, promotional blocks, and logging stats."""
        filter_sql, params, scope_label = self._build_doc_filter(document_id, source_document)

        with self._get_connection() as conn:
            rows = conn.execute(
                f"SELECT metric_name, metric_value, unit, year_period, category, source_document, source_page, evidence_text "
                f"FROM geological_metrics WHERE 1=1 {filter_sql}",
                params,
            ).fetchall()

            metrics_by_name: Dict[str, Any] = {r["metric_name"].strip(): r for r in rows}

            def make_prov(r):
                if not r:
                    return None
                return ProvenanceRecord(
                    source_document=r["source_document"],
                    source_page=r["source_page"],
                    evidence_text=r["evidence_text"] or "",
                )

            # 1. Agency drilling items
            agency_items: List[DrillingAgencyItem] = []

            # CMPDI Departmental Drilling
            cmpdi_tgt = metrics_by_name.get("CMPDI Exploratory Drilling Target")
            cmpdi_ach = metrics_by_name.get("CMPDI Exploratory Drilling Achieved")
            if cmpdi_tgt or cmpdi_ach:
                t_val = cmpdi_tgt["metric_value"] if cmpdi_tgt else None
                a_val = cmpdi_ach["metric_value"] if cmpdi_ach else None
                pct = round((a_val / t_val) * 100, 2) if (a_val is not None and t_val) else None
                agency_items.append(
                    DrillingAgencyItem(
                        agency="CMPDI (Departmental)",
                        target=t_val,
                        achieved=a_val,
                        unit=cmpdi_ach["unit"] if cmpdi_ach else (cmpdi_tgt["unit"] if cmpdi_tgt else "metre"),
                        achievement_pct=pct,
                        fiscal_period="2006-07 BE / 2006-07",
                        category="Departmental Drilling",
                        provenance=make_prov(cmpdi_ach or cmpdi_tgt),
                    )
                )

            # MECL Contractual Drilling
            mecl_ach = metrics_by_name.get("MECL Exploratory Drilling Achieved")
            if mecl_ach:
                a_val = mecl_ach["metric_value"]
                agency_items.append(
                    DrillingAgencyItem(
                        agency="MECL (Contractual)",
                        target=None,
                        achieved=a_val,
                        unit=mecl_ach["unit"] or "metre",
                        achievement_pct=None,
                        fiscal_period=mecl_ach["year_period"] or "2006-07",
                        category="Contractual Drilling",
                        provenance=make_prov(mecl_ach),
                    )
                )

            # State Govts Drilling
            state_tgt = metrics_by_name.get("State Govts Exploratory Drilling Target")
            state_ach = metrics_by_name.get("State Govts Exploratory Drilling Achieved")
            if state_tgt or state_ach:
                t_val = state_tgt["metric_value"] if state_tgt else None
                a_val = state_ach["metric_value"] if state_ach else None
                pct = round((a_val / t_val) * 100, 2) if (a_val is not None and t_val) else None
                agency_items.append(
                    DrillingAgencyItem(
                        agency="State Governments",
                        target=t_val,
                        achieved=a_val,
                        unit=state_ach["unit"] if state_ach else (state_tgt["unit"] if state_tgt else "metre"),
                        achievement_pct=pct,
                        fiscal_period="2006-07 BE / 2006-07",
                        category="State Drilling",
                        provenance=make_prov(state_ach or state_tgt),
                    )
                )

            # Total Exploratory Drilling
            tot_tgt = metrics_by_name.get("Total Exploratory Drilling Target")
            tot_ach = metrics_by_name.get("Total Exploratory Drilling Achieved")
            if tot_tgt or tot_ach:
                t_val = tot_tgt["metric_value"] if tot_tgt else None
                a_val = tot_ach["metric_value"] if tot_ach else None
                pct = round((a_val / t_val) * 100, 2) if (a_val is not None and t_val) else None
                agency_items.append(
                    DrillingAgencyItem(
                        agency="Total Exploratory Drilling",
                        target=t_val,
                        achieved=a_val,
                        unit=tot_ach["unit"] if tot_ach else (tot_tgt["unit"] if tot_tgt else "metre"),
                        achievement_pct=pct,
                        fiscal_period="2006-07 BE / 2006-07",
                        category="Total Drilling",
                        provenance=make_prov(tot_ach or tot_tgt),
                    )
                )

            # X-Plan Drilling
            xplan_tgt = metrics_by_name.get("Drilling Target")
            xplan_ach = metrics_by_name.get("Drilling Achievement")
            if xplan_tgt or xplan_ach:
                t_val = xplan_tgt["metric_value"] if xplan_tgt else None
                a_val = xplan_ach["metric_value"] if xplan_ach else None
                pct = round((a_val / t_val) * 100, 2) if (a_val is not None and t_val) else None
                agency_items.append(
                    DrillingAgencyItem(
                        agency="X-Plan Drilling",
                        target=t_val,
                        achieved=a_val,
                        unit=xplan_ach["unit"] if xplan_ach else "lakh metre",
                        achievement_pct=pct,
                        fiscal_period="X plan",
                        category="Five-Year Plan Target",
                        provenance=make_prov(xplan_ach or xplan_tgt),
                    )
                )

            # 2. Promotional drilling by block
            promo_blocks: List[PromotionalBlockItem] = []
            block_candidates = [
                ("Ashok Karkatta West", "Drilling in Ashok Karkatta West"),
                ("Bishnupur", "Drilling in Bishnupur"),
                ("Chimri", "Drilling in Chimri"),
            ]
            total_promo = 0.0
            for b_name, m_key in block_candidates:
                r = metrics_by_name.get(m_key)
                if r and r["metric_value"] is not None:
                    promo_blocks.append(
                        PromotionalBlockItem(
                            block_name=b_name,
                            drilling_metres=r["metric_value"],
                            unit=r["unit"] or "m",
                            fiscal_period=r["year_period"] or "2006-07",
                            provenance=make_prov(r),
                        )
                    )
                    total_promo += r["metric_value"]

            # If total promotional drilling record exists, verify or use its value
            tot_promo_rec = metrics_by_name.get("Promotional drilling")
            if tot_promo_rec and tot_promo_rec["metric_value"] is not None:
                total_promo_val = tot_promo_rec["metric_value"]
            else:
                total_promo_val = total_promo if promo_blocks else None

            # 3. Non-CIL / Captive Blocks info
            non_cil_rec = metrics_by_name.get("Exploratory Drilling in Non-CIL/Captive Mining Blocks")
            non_cil_blocks_rec = metrics_by_name.get("Non-CIL/Captive Mining Blocks")
            non_cil_cf_rec = metrics_by_name.get("Non-CIL/Captive Mining Coalfields")
            non_cil_rep_rec = metrics_by_name.get("Detailed Exploration Reports of Non-CIL/Captive Mining blocks")

            non_cil_info = None
            if non_cil_rec or non_cil_blocks_rec or non_cil_cf_rec or non_cil_rep_rec:
                non_cil_info = NonCILCaptiveDrillingInfo(
                    drilling_metres=non_cil_rec["metric_value"] if non_cil_rec else None,
                    blocks_count=int(non_cil_blocks_rec["metric_value"]) if non_cil_blocks_rec else None,
                    coalfields_count=int(non_cil_cf_rec["metric_value"]) if non_cil_cf_rec else None,
                    reports_count=int(non_cil_rep_rec["metric_value"]) if non_cil_rep_rec else None,
                    fiscal_period=non_cil_rec["year_period"] if non_cil_rec else "2006-07",
                    provenance=make_prov(non_cil_rec or non_cil_blocks_rec),
                )

            # 4. Geophysical logging & surveys
            geo_bh = metrics_by_name.get("Boreholes studied with multi-parametric geophysical logging")
            geo_depth = metrics_by_name.get("Geophysical logging depth metre")
            mag_surv = metrics_by_name.get("Magnetic Survey")
            res_prof = metrics_by_name.get("Resistivity profiling")
            ves = metrics_by_name.get("Vertical Electrical Soundings")

            geo_stats = None
            if geo_bh or geo_depth or mag_surv or res_prof or ves:
                geo_stats = GeophysicalLoggingStats(
                    boreholes_count=int(geo_bh["metric_value"]) if geo_bh else None,
                    logging_depth_metres=geo_depth["metric_value"] if geo_depth else None,
                    magnetic_survey_stations=mag_surv["metric_value"] if mag_surv else None,
                    resistivity_profiling_km=res_prof["metric_value"] if res_prof else None,
                    vertical_soundings_count=ves["metric_value"] if ves else None,
                    fiscal_period="2006-07",
                    provenance=make_prov(geo_depth or geo_bh),
                )

            return DrillingAnalyticsResponse(
                targets_vs_achievements=agency_items,
                promotional_drilling_by_block=promo_blocks,
                total_promotional_drilling_m=total_promo_val,
                non_cil_captive_blocks=non_cil_info,
                geophysical_logging=geo_stats,
                source_scope=scope_label,
            )

    def get_resource_analytics(
        self, document_id: Optional[str] = None, source_document: Optional[str] = None
    ) -> ResourceAnalyticsResponse:
        """Returns coal resource classifications and seam reserve reconciliations."""
        filter_sql, params, scope_label = self._build_doc_filter(document_id, source_document)

        with self._get_connection() as conn:
            # 1. Macro resource classifications from geological_metrics
            rows = conn.execute(
                f"SELECT metric_name, metric_value, unit, year_period, category, source_document, source_page, evidence_text "
                f"FROM geological_metrics WHERE 1=1 {filter_sql}",
                params,
            ).fetchall()

            metrics_by_name = {r["metric_name"].strip(): r for r in rows}

            categories: List[ResourceCategoryItem] = []
            add_res = metrics_by_name.get("Additional coal resources estimated")
            proved_res = metrics_by_name.get("Proved category coal resources")
            ind_res = metrics_by_name.get("Indicated category coal resources")

            def make_prov(r):
                if not r:
                    return None
                return ProvenanceRecord(
                    source_document=r["source_document"],
                    source_page=r["source_page"],
                    evidence_text=r["evidence_text"] or "",
                )

            if proved_res and proved_res["metric_value"] is not None:
                categories.append(
                    ResourceCategoryItem(
                        category="Proved Resources",
                        value=proved_res["metric_value"],
                        unit=proved_res["unit"] or "Bt",
                        fiscal_period=proved_res["year_period"] or "2006-07",
                        provenance=make_prov(proved_res),
                    )
                )

            if ind_res and ind_res["metric_value"] is not None:
                categories.append(
                    ResourceCategoryItem(
                        category="Indicated Resources",
                        value=ind_res["metric_value"],
                        unit=ind_res["unit"] or "Bt",
                        fiscal_period=ind_res["year_period"] or "2006-07",
                        provenance=make_prov(ind_res),
                    )
                )

            total_add_val = add_res["metric_value"] if add_res else None
            if add_res and add_res["metric_value"] is not None:
                categories.append(
                    ResourceCategoryItem(
                        category="Total Additional Resources",
                        value=add_res["metric_value"],
                        unit=add_res["unit"] or "Billion Tonnes",
                        fiscal_period=add_res["year_period"] or "2006-07",
                        provenance=make_prov(add_res),
                    )
                )

            # 2. Micro seam reserves from coal_seams table
            seam_rows = conn.execute(
                f"SELECT seam_id, borehole_id, category, gross_reserves_mt, extractable_reserves_mt, "
                f"source_document, source_page, evidence_text FROM coal_seams "
                f"WHERE (gross_reserves_mt IS NOT NULL OR extractable_reserves_mt IS NOT NULL) {filter_sql} "
                f"GROUP BY seam_id, borehole_id, category, gross_reserves_mt, extractable_reserves_mt, source_document, source_page "
                f"ORDER BY source_document ASC, source_page ASC, seam_id ASC",
                params,
            ).fetchall()

            seam_reserves: List[SeamReserveItem] = []
            for s in seam_rows:
                g_mt = s["gross_reserves_mt"]
                e_mt = s["extractable_reserves_mt"]
                rec_pct = None
                if g_mt and e_mt and g_mt > 0:
                    rec_pct = round((e_mt / g_mt) * 100, 2)

                seam_reserves.append(
                    SeamReserveItem(
                        seam_id=s["seam_id"],
                        borehole_id=s["borehole_id"],
                        category=s["category"],
                        gross_reserves_mt=g_mt,
                        extractable_reserves_mt=e_mt,
                        recovery_factor_pct=rec_pct,
                        provenance=ProvenanceRecord(
                            source_document=s["source_document"],
                            source_page=s["source_page"],
                            evidence_text=s["evidence_text"] or "",
                        ),
                    )
                )

            return ResourceAnalyticsResponse(
                resource_categories=categories,
                seam_reserves=seam_reserves,
                total_additional_resources_bt=total_add_val,
                source_scope=scope_label,
            )

    def get_project_analytics(
        self,
        document_id: Optional[str] = None,
        source_document: Optional[str] = None,
        subsidiary: Optional[str] = None,
        location: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ProjectAnalyticsResponse:
        """Returns filtered mine/project analytics with subsidiary breakdown."""
        doc_filter, params, scope_label = self._build_doc_filter(document_id, source_document)

        with self._get_connection() as conn:
            # 1. Available subsidiaries and locations in this document scope
            sub_rows = conn.execute(
                f"SELECT DISTINCT subsidiary FROM mines_projects WHERE subsidiary IS NOT NULL {doc_filter} ORDER BY subsidiary ASC",
                params,
            ).fetchall()
            available_subs = [r[0] for r in sub_rows if r[0]]

            loc_rows = conn.execute(
                f"SELECT DISTINCT location FROM mines_projects WHERE location IS NOT NULL {doc_filter} ORDER BY location ASC",
                params,
            ).fetchall()
            available_locs = [r[0] for r in loc_rows if r[0]]

            # 2. Subsidiary breakdown in scope
            breakdown_rows = conn.execute(
                f"SELECT subsidiary, count(1) as cnt FROM mines_projects WHERE 1=1 {doc_filter} GROUP BY subsidiary ORDER BY cnt DESC",
                params,
            ).fetchall()
            subsidiary_breakdown = [
                SubsidiaryCountItem(subsidiary=r["subsidiary"] or "Unspecified", count=r["cnt"])
                for r in breakdown_rows
            ]

            # 3. Filtered project list
            query_conds = [f"1=1 {doc_filter}"]
            query_params = list(params)

            if subsidiary and subsidiary.strip() and subsidiary.lower() != "all":
                query_conds.append("subsidiary = ?")
                query_params.append(subsidiary.strip())

            if location and location.strip() and location.lower() != "all":
                query_conds.append("location = ?")
                query_params.append(location.strip())

            if search and search.strip():
                term = f"%{search.strip()}%"
                query_conds.append("(project_name LIKE ? OR location LIKE ? OR block_name LIKE ?)")
                query_params.extend([term, term, term])

            final_query = f"SELECT * FROM mines_projects WHERE {' AND '.join(query_conds)} ORDER BY project_name ASC"
            p_rows = conn.execute(final_query, query_params).fetchall()

            projects = [
                ProjectAnalyticsItem(
                    id=r["id"],
                    project_name=r["project_name"],
                    subsidiary=r["subsidiary"],
                    location=r["location"],
                    block_name=r["block_name"],
                    target_production=r["target_production"],
                    target_production_unit=r["target_production_unit"],
                    stripping_ratio=r["stripping_ratio"],
                    life_of_mine_years=r["life_of_mine_years"],
                    source_document=r["source_document"],
                    source_page=r["source_page"],
                    evidence_text=r["evidence_text"] or "",
                )
                for r in p_rows
            ]

            return ProjectAnalyticsResponse(
                total_projects=len(projects),
                subsidiary_breakdown=subsidiary_breakdown,
                available_subsidiaries=available_subs,
                available_locations=available_locs,
                projects=projects,
                source_scope=scope_label,
            )

    def get_coal_quality_analytics(
        self, document_id: Optional[str] = None, source_document: Optional[str] = None
    ) -> CoalQualityResponse:
        """Returns laboratory proximate analysis records and calculated averages, or an empty state."""
        filter_sql, params, scope_label = self._build_doc_filter(document_id, source_document)

        with self._get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM proximate_analyses WHERE 1=1 {filter_sql} ORDER BY source_document ASC, source_page ASC",
                params,
            ).fetchall()

            if not rows:
                return CoalQualityResponse(
                    has_data=False,
                    total_records=0,
                    records=[],
                    averages=None,
                    source_scope=scope_label,
                    empty_state_reason=f"No laboratory proximate analysis records exist in document scope '{scope_label}'.",
                )

            records: List[ProximateQualityItem] = []
            moisture_vals = []
            ash_vals = []
            vm_vals = []
            fc_vals = []
            gcv_vals = []

            for r in rows:
                item = ProximateQualityItem(
                    id=r["id"],
                    seam_id=r["seam_id"],
                    borehole_id=r["borehole_id"],
                    moisture_percent=r["moisture_percent"],
                    ash_percent=r["ash_percent"],
                    volatile_matter_percent=r["volatile_matter_percent"],
                    fixed_carbon_percent=r["fixed_carbon_percent"],
                    gross_calorific_value=r["gross_calorific_value"],
                    units=r["units"] or "%",
                    source_document=r["source_document"],
                    source_page=r["source_page"],
                    evidence_text=r["evidence_text"] or "",
                )
                records.append(item)
                if r["moisture_percent"] is not None:
                    moisture_vals.append(r["moisture_percent"])
                if r["ash_percent"] is not None:
                    ash_vals.append(r["ash_percent"])
                if r["volatile_matter_percent"] is not None:
                    vm_vals.append(r["volatile_matter_percent"])
                if r["fixed_carbon_percent"] is not None:
                    fc_vals.append(r["fixed_carbon_percent"])
                if r["gross_calorific_value"] is not None:
                    gcv_vals.append(r["gross_calorific_value"])

            avg_m = round(sum(moisture_vals) / len(moisture_vals), 2) if moisture_vals else None
            avg_a = round(sum(ash_vals) / len(ash_vals), 2) if ash_vals else None
            avg_v = round(sum(vm_vals) / len(vm_vals), 2) if vm_vals else None
            avg_f = round(sum(fc_vals) / len(fc_vals), 2) if fc_vals else None
            avg_g = round(sum(gcv_vals) / len(gcv_vals), 2) if gcv_vals else None

            averages = CoalQualityAverages(
                avg_moisture_pct=avg_m,
                avg_ash_pct=avg_a,
                avg_volatile_matter_pct=avg_v,
                avg_fixed_carbon_pct=avg_f,
                avg_gcv=avg_g,
            )

            return CoalQualityResponse(
                has_data=True,
                total_records=len(records),
                records=records,
                averages=averages,
                source_scope=scope_label,
            )

    def get_metrics_explorer(
        self,
        document_id: Optional[str] = None,
        source_document: Optional[str] = None,
        category: Optional[str] = None,
        unit: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> GeologicalMetricsResponse:
        """Returns paginated and searchable table of geological report metrics."""
        doc_filter, doc_params, scope_label = self._build_doc_filter(document_id, source_document)

        with self._get_connection() as conn:
            # Distinct categories and units in scope
            cat_rows = conn.execute(
                f"SELECT DISTINCT category FROM geological_metrics WHERE category IS NOT NULL {doc_filter} ORDER BY category ASC",
                doc_params,
            ).fetchall()
            categories = [r[0] for r in cat_rows if r[0]]

            unit_rows = conn.execute(
                f"SELECT DISTINCT unit FROM geological_metrics WHERE unit IS NOT NULL {doc_filter} ORDER BY unit ASC",
                doc_params,
            ).fetchall()
            units = [r[0] for r in unit_rows if r[0]]

            # Filter conditions
            conds = [f"1=1 {doc_filter}"]
            params = list(doc_params)

            if category and category.strip() and category.lower() != "all":
                conds.append("category = ?")
                params.append(category.strip())

            if unit and unit.strip() and unit.lower() != "all":
                conds.append("unit = ?")
                params.append(unit.strip())

            if search and search.strip():
                term = f"%{search.strip()}%"
                conds.append("(metric_name LIKE ? OR category LIKE ? OR evidence_text LIKE ?)")
                params.extend([term, term, term])

            where_clause = " AND ".join(conds)

            # Total matching count
            total_count = conn.execute(
                f"SELECT count(1) FROM geological_metrics WHERE {where_clause}", params
            ).fetchone()[0]

            # Paginated rows
            paginated_params = list(params) + [limit, offset]
            rows = conn.execute(
                f"SELECT * FROM geological_metrics WHERE {where_clause} ORDER BY source_document ASC, source_page ASC, metric_name ASC LIMIT ? OFFSET ?",
                paginated_params,
            ).fetchall()

            metrics = [
                GeologicalMetricItem(
                    id=r["id"],
                    metric_name=r["metric_name"],
                    metric_value=r["metric_value"],
                    unit=r["unit"],
                    year_period=r["year_period"],
                    category=r["category"],
                    source_document=r["source_document"],
                    source_page=r["source_page"],
                    evidence_text=r["evidence_text"] or "",
                )
                for r in rows
            ]

            return GeologicalMetricsResponse(
                total=total_count,
                categories=categories,
                units=units,
                metrics=metrics,
                source_scope=scope_label,
            )

    def get_cross_document_comparison(
        self, documents: Optional[str] = None
    ) -> CrossDocumentComparisonResponse:
        """Compares compatible metrics and entity distributions across indexed documents without unit corruption."""
        with self._get_connection() as conn:
            # 1. Resolve candidate documents
            if documents and documents.strip():
                doc_list = [d.strip() for d in documents.split(",") if d.strip()]
            else:
                # Get all distinct source documents present in database
                d_rows = conn.execute(
                    "SELECT DISTINCT source_document FROM mines_projects "
                    "UNION SELECT DISTINCT source_document FROM boreholes "
                    "UNION SELECT DISTINCT source_document FROM coal_seams "
                    "UNION SELECT DISTINCT source_document FROM proximate_analyses "
                    "UNION SELECT DISTINCT source_document FROM geological_metrics"
                ).fetchall()
                doc_list = [r[0] for r in d_rows if r[0]]

            # 2. Entity breakdown per document
            entity_breakdowns: List[DocumentEntityBreakdown] = []
            for doc in doc_list:
                p = [doc, doc, f"%{doc}%"]
                filter_s = "WHERE (document_id = ? OR source_document = ? OR source_document LIKE ?)"
                m = conn.execute(f"SELECT count(1) FROM mines_projects {filter_s}", p).fetchone()[0]
                b = conn.execute(f"SELECT count(1) FROM boreholes {filter_s}", p).fetchone()[0]
                s = conn.execute(f"SELECT count(1) FROM coal_seams {filter_s}", p).fetchone()[0]
                pr = conn.execute(f"SELECT count(1) FROM proximate_analyses {filter_s}", p).fetchone()[0]
                g = conn.execute(f"SELECT count(1) FROM geological_metrics {filter_s}", p).fetchone()[0]
                total = m + b + s + pr + g
                entity_breakdowns.append(
                    DocumentEntityBreakdown(
                        document=doc,
                        mines_projects=m,
                        boreholes=b,
                        coal_seams=s,
                        proximate_analyses=pr,
                        geological_metrics=g,
                        total_entities=total,
                    )
                )

            # 3. Compatible metrics comparison
            # Group geological metrics by (metric_name, unit) across the selected documents
            compatible_comparisons: List[CompatibleMetricComparison] = []

            # Find all (metric_name, unit, category) present in selected docs
            if doc_list:
                placeholders = ",".join(["?"] * len(doc_list))
                m_rows = conn.execute(
                    f"SELECT metric_name, unit, category, metric_value, source_document, source_page, evidence_text "
                    f"FROM geological_metrics WHERE source_document IN ({placeholders})",
                    doc_list,
                ).fetchall()

                # Group by normalized (metric_name, unit)
                groups: Dict[Tuple[str, str], Dict[str, Any]] = {}
                for row in m_rows:
                    m_name = row["metric_name"].strip()
                    m_unit = (row["unit"] or "unitless").strip()
                    key = (m_name, m_unit)
                    if key not in groups:
                        groups[key] = {
                            "metric_name": m_name,
                            "unit": m_unit,
                            "category": row["category"],
                            "values": {},
                            "provenances": {},
                        }
                    d_name = row["source_document"]
                    groups[key]["values"][d_name] = row["metric_value"]
                    groups[key]["provenances"][d_name] = ProvenanceRecord(
                        source_document=d_name,
                        source_page=row["source_page"],
                        evidence_text=row["evidence_text"] or "",
                    )

                for g_data in groups.values():
                    compatible_comparisons.append(
                        CompatibleMetricComparison(
                            metric_name=g_data["metric_name"],
                            unit=g_data["unit"],
                            category=g_data["category"],
                            values_by_document=g_data["values"],
                            provenance_by_document=g_data["provenances"],
                        )
                    )

            note = (
                "Metric comparison strictly groups metrics with identical names and physical units. "
                "Disparate units (e.g. 'metre' vs 'lakh metre' vs 'Billion Tonnes') are preserved in their native units "
                "to prevent erroneous mathematical conflation."
            )

            return CrossDocumentComparisonResponse(
                compared_documents=doc_list,
                entity_breakdown=entity_breakdowns,
                compatible_metrics=compatible_comparisons,
                incompatible_metrics_note=note,
            )


# Global singleton instance
analytics_service = AnalyticsService()
