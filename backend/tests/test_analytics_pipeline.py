"""
Phase 6 Automated Test Suite: Analytics, Visualization & Cross-Document Integration
SIH 2026 Problem Statement 26023 (CMPDI / Coal India Limited)

Verifies:
1. Analytics KPI summary (/api/analytics/summary) - All docs & accounts0607.pdf (66 mines, 59 metrics, 125 total)
2. Drilling Analytics (/api/analytics/drilling) - CMPDI, MECL, State Govts, X-Plan, Non-CIL, Promotional blocks
3. Coal Resource Analytics (/api/analytics/resources) - Proved, Indicated, Additional Bt, seam reserves
4. Project / Mine Analytics (/api/analytics/projects) - Filters, subsidiary distribution, search
5. Coal Quality Analytics (/api/analytics/quality) - Laboratory proximate values vs explicit empty state
6. Geological Metrics Explorer (/api/analytics/metrics) - Multi-faceted filtering & pagination
7. Cross-Document Comparison (/api/analytics/comparison) - Multi-document comparison with strict unit integrity
8. Negative & Boundary Testing - Empty scope, missing values, non-existent doc, SQL safety
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_analytics_summary_all_and_accounts0607():
    """Validates /api/analytics/summary for both cumulative and accounts0607.pdf scopes."""
    print("\n--- Test 1: Analytics KPI Summary ---")
    
    # 1. Cumulative Summary
    res_all = client.get("/api/analytics/summary")
    assert res_all.status_code == 200
    s_all = res_all.json()
    assert s_all["total_mines_projects"] >= 66
    assert s_all["total_geological_metrics"] >= 59
    assert s_all["total_entities"] >= 125
    assert s_all["source_scope"] == "all"
    
    # 2. accounts0607.pdf Specific Parity (66 mines, 59 metrics, 125 entities)
    res_acc = client.get("/api/analytics/summary", params={"source_document": "accounts0607.pdf"})
    assert res_acc.status_code == 200
    s_acc = res_acc.json()
    assert s_acc["total_mines_projects"] == 66, f"Expected 66 mines, got {s_acc['total_mines_projects']}"
    assert s_acc["total_geological_metrics"] == 59, f"Expected 59 metrics, got {s_acc['total_geological_metrics']}"
    assert s_acc["total_boreholes"] == 0, f"Expected 0 boreholes, got {s_acc['total_boreholes']}"
    assert s_acc["total_coal_seams"] == 0, f"Expected 0 coal seams, got {s_acc['total_coal_seams']}"
    assert s_acc["total_proximate_analyses"] == 0, f"Expected 0 proximate analyses, got {s_acc['total_proximate_analyses']}"
    assert s_acc["total_entities"] == 125, f"Expected 125 total entities, got {s_acc['total_entities']}"
    
    # Verify exact drilling figures from accounts0607.pdf
    assert s_acc["total_exploratory_drilling_target_m"] == 199000.0
    assert s_acc["total_exploratory_drilling_achieved_m"] == 205746.0
    assert s_acc["drilling_achievement_pct"] == 103.39
    
    # Verify exact coal resource figures
    assert s_acc["additional_coal_resources_bt"] == 1.78
    assert s_acc["proved_resources_bt"] == 1.3
    assert s_acc["indicated_resources_bt"] == 0.47
    
    # Verify reports & logging figures
    assert s_acc["total_reports_prepared"] == 242
    assert s_acc["geological_reports_count"] == 17
    assert s_acc["boreholes_logged_count"] == 60
    assert s_acc["geophysical_logging_depth_m"] == 19081.0
    
    # Verify provenance map is populated
    assert "Total Exploratory Drilling Achieved" in s_acc["provenance_map"]
    p_drilling = s_acc["provenance_map"]["Total Exploratory Drilling Achieved"]
    assert p_drilling["source_document"] == "accounts0607.pdf"
    assert p_drilling["source_page"] == 9
    assert len(p_drilling["evidence_text"]) > 0


def test_drilling_analytics():
    """Validates /api/analytics/drilling targets vs achievements and promotional block drilling."""
    print("\n--- Test 2: Drilling Analytics ---")
    res = client.get("/api/analytics/drilling", params={"source_document": "accounts0607.pdf"})
    assert res.status_code == 200
    data = res.json()
    
    # 1. Agency comparison
    agencies = data["targets_vs_achievements"]
    assert len(agencies) >= 4
    agency_map = {a["agency"]: a for a in agencies}
    
    # CMPDI Departmental
    assert "CMPDI (Departmental)" in agency_map
    cmpdi = agency_map["CMPDI (Departmental)"]
    assert cmpdi["target"] == 192000.0
    assert cmpdi["achieved"] == 198496.0
    assert cmpdi["achievement_pct"] == 103.38
    assert cmpdi["unit"] == "metre"
    assert cmpdi["provenance"]["source_page"] == 9
    
    # MECL Contractual
    assert "MECL (Contractual)" in agency_map
    mecl = agency_map["MECL (Contractual)"]
    assert mecl["achieved"] == 715.0
    assert mecl["provenance"]["source_page"] == 9
    
    # State Govts
    assert "State Governments" in agency_map
    state = agency_map["State Governments"]
    assert state["target"] == 7000.0
    assert state["achieved"] == 6535.0
    assert state["achievement_pct"] == 93.36
    
    # Total Drilling
    assert "Total Exploratory Drilling" in agency_map
    tot = agency_map["Total Exploratory Drilling"]
    assert tot["target"] == 199000.0
    assert tot["achieved"] == 205746.0
    assert tot["achievement_pct"] == 103.39
    
    # X-Plan Drilling
    assert "X-Plan Drilling" in agency_map
    xplan = agency_map["X-Plan Drilling"]
    assert xplan["target"] == 2.83
    assert xplan["achieved"] == 2.84
    assert xplan["unit"] == "lakh metre"
    
    # 2. Promotional drilling by block
    promo_blocks = data["promotional_drilling_by_block"]
    assert len(promo_blocks) == 3
    block_names = {b["block_name"]: b["drilling_metres"] for b in promo_blocks}
    assert block_names["Ashok Karkatta West"] == 3639.0
    assert block_names["Bishnupur"] == 2230.0
    assert block_names["Chimri"] == 1010.0
    assert data["total_promotional_drilling_m"] == 6879.0
    
    # 3. Non-CIL / captive blocks
    non_cil = data["non_cil_captive_blocks"]
    assert non_cil is not None
    assert non_cil["drilling_metres"] == 51774.0
    assert non_cil["blocks_count"] == 11
    assert non_cil["coalfields_count"] == 6
    assert non_cil["reports_count"] == 5
    
    # 4. Geophysical logging
    logging_info = data["geophysical_logging"]
    assert logging_info is not None
    assert logging_info["boreholes_count"] == 60
    assert logging_info["logging_depth_metres"] == 19081.0
    assert logging_info["magnetic_survey_stations"] == 4763.0
    assert logging_info["resistivity_profiling_km"] == 122.0
    assert logging_info["vertical_soundings_count"] == 151.0


def test_resource_analytics():
    """Validates /api/analytics/resources coal resources and seam reserves."""
    print("\n--- Test 3: Resource Analytics ---")
    
    # 1. accounts0607.pdf scope: macro resources present, micro seam reserves = 0
    res_acc = client.get("/api/analytics/resources", params={"source_document": "accounts0607.pdf"})
    assert res_acc.status_code == 200
    r_acc = res_acc.json()
    assert len(r_acc["resource_categories"]) == 3
    cats = {c["category"]: c["value"] for c in r_acc["resource_categories"]}
    assert cats["Proved Resources"] == 1.3
    assert cats["Indicated Resources"] == 0.47
    assert cats["Total Additional Resources"] == 1.78
    assert r_acc["total_additional_resources_bt"] == 1.78
    assert len(r_acc["seam_reserves"]) == 0  # No seam records in accounts0607
    
    # 2. All documents scope: seam reserves present
    res_all = client.get("/api/analytics/resources")
    assert res_all.status_code == 200
    r_all = res_all.json()
    assert len(r_all["seam_reserves"]) >= 3
    seam_names = [s["seam_id"] for s in r_all["seam_reserves"]]
    assert any("Seam VIII" in s or "SEAM-VIII" in s for s in seam_names)

    # 3. Borehole_Logging_Data.xlsx scope: exactly 3 unique seam reserves, no duplicates
    res_xlsx = client.get("/api/analytics/resources", params={"source_document": "Borehole_Logging_Data.xlsx"})
    assert res_xlsx.status_code == 200
    r_xlsx = res_xlsx.json()
    seams_xlsx = r_xlsx["seam_reserves"]
    assert len(seams_xlsx) == 3, f"Expected exactly 3 unique seam reserves for Borehole_Logging_Data.xlsx, got {len(seams_xlsx)}"
    
    # Verify no duplicate seam_id in result
    seam_ids = [s["seam_id"] for s in seams_xlsx]
    assert len(seam_ids) == len(set(seam_ids)), f"Duplicate seam IDs detected: {seam_ids}"
    
    # Verify exact values and recovery % calculations
    s_map = {s["seam_id"]: s for s in seams_xlsx}
    
    # Seam VIII
    assert "Seam VIII" in s_map
    s8 = s_map["Seam VIII"]
    assert s8["category"] == "Proved"
    assert s8["gross_reserves_mt"] == 14.8
    assert s8["extractable_reserves_mt"] == 12.2
    assert s8["recovery_factor_pct"] == 82.43
    assert s8["provenance"]["source_page"] == 2
    assert round((12.2 / 14.8) * 100, 2) == 82.43
    
    # Seam VII
    assert "Seam VII" in s_map
    s7 = s_map["Seam VII"]
    assert s7["category"] == "Proved"
    assert s7["gross_reserves_mt"] == 28.5
    assert s7["extractable_reserves_mt"] == 23.9
    assert s7["recovery_factor_pct"] == 83.86
    assert s7["provenance"]["source_page"] == 2
    assert round((23.9 / 28.5) * 100, 2) == 83.86
    
    # Seam VI
    assert "Seam VI" in s_map
    s6 = s_map["Seam VI"]
    assert s6["category"] == "Indicated"
    assert s6["gross_reserves_mt"] == 42.1
    assert s6["extractable_reserves_mt"] == 33.7
    assert s6["recovery_factor_pct"] == 80.05
    assert s6["provenance"]["source_page"] == 2
    assert round((33.7 / 42.1) * 100, 2) == 80.05


def test_project_analytics():
    """Validates /api/analytics/projects filtering, search, and subsidiary breakdowns."""
    print("\n--- Test 4: Project Analytics ---")
    
    # 1. accounts0607.pdf projects count = 66
    res_acc = client.get("/api/analytics/projects", params={"source_document": "accounts0607.pdf"})
    assert res_acc.status_code == 200
    p_acc = res_acc.json()
    assert p_acc["total_projects"] == 66
    assert len(p_acc["projects"]) == 66
    assert len(p_acc["subsidiary_breakdown"]) >= 5
    
    # Verify subsidiary counts
    sub_map = {s["subsidiary"]: s["count"] for s in p_acc["subsidiary_breakdown"]}
    assert sub_map.get("CCL", 0) == 5
    assert sub_map.get("CMPDI / CIL", 0) == 50
    
    # 2. Filter by subsidiary (CCL)
    res_ccl = client.get(
        "/api/analytics/projects",
        params={"source_document": "accounts0607.pdf", "subsidiary": "CCL"},
    )
    assert res_ccl.status_code == 200
    p_ccl = res_ccl.json()
    assert p_ccl["total_projects"] == 5
    for p in p_ccl["projects"]:
        assert p["subsidiary"] == "CCL"
        assert p["source_document"] == "accounts0607.pdf"
        
    # 3. Keyword search
    res_search = client.get(
        "/api/analytics/projects",
        params={"source_document": "accounts0607.pdf", "search": "Chimri"},
    )
    assert res_search.status_code == 200
    p_search = res_search.json()
    assert p_search["total_projects"] >= 1
    assert any("Chimri" in p["project_name"] for p in p_search["projects"])


def test_coal_quality_analytics():
    """Validates /api/analytics/quality proximate analysis handling and empty state."""
    print("\n--- Test 5: Coal Quality Analytics ---")
    
    # 1. accounts0607.pdf has 0 proximate analyses -> must return clean empty state
    res_acc = client.get("/api/analytics/quality", params={"source_document": "accounts0607.pdf"})
    assert res_acc.status_code == 200
    q_acc = res_acc.json()
    assert q_acc["has_data"] is False
    assert q_acc["total_records"] == 0
    assert q_acc["records"] == []
    assert q_acc["averages"] is None
    assert "No laboratory proximate analysis" in q_acc["empty_state_reason"]
    
    # 2. Cumulative / Borehole_Logging_Data.xlsx scope has records
    res_all = client.get("/api/analytics/quality")
    assert res_all.status_code == 200
    q_all = res_all.json()
    assert q_all["has_data"] is True
    assert q_all["total_records"] >= 3
    assert q_all["averages"] is not None
    assert q_all["averages"]["avg_ash_pct"] is not None
    assert q_all["averages"]["avg_gcv"] is not None


def test_geological_metrics_explorer():
    """Validates /api/analytics/metrics explorer, pagination, and multi-facet filtering."""
    print("\n--- Test 6: Geological Metrics Explorer ---")
    
    # 1. Total count for accounts0607.pdf must be exactly 59
    res_acc = client.get("/api/analytics/metrics", params={"source_document": "accounts0607.pdf"})
    assert res_acc.status_code == 200
    m_acc = res_acc.json()
    assert m_acc["total"] == 59, f"Expected 59 metrics, got {m_acc['total']}"
    assert len(m_acc["categories"]) >= 10
    assert len(m_acc["units"]) >= 5
    
    # 2. Category filtering
    res_cat = client.get(
        "/api/analytics/metrics",
        params={"source_document": "accounts0607.pdf", "category": "REPORTS"},
    )
    assert res_cat.status_code == 200
    m_cat = res_cat.json()
    assert m_cat["total"] >= 5
    for m in m_cat["metrics"]:
        assert m["category"] == "REPORTS"
        assert m["source_document"] == "accounts0607.pdf"
        assert m["source_page"] == 16
        
    # 3. Unit filtering
    res_unit = client.get(
        "/api/analytics/metrics",
        params={"source_document": "accounts0607.pdf", "unit": "metre"},
    )
    assert res_unit.status_code == 200
    m_unit = res_unit.json()
    assert m_unit["total"] >= 4
    for m in m_unit["metrics"]:
        assert m["unit"] == "metre"


def test_cross_document_comparison():
    """Validates /api/analytics/comparison entity breakdown and unit segregation."""
    print("\n--- Test 7: Cross-Document Analytics Comparison ---")
    res = client.get("/api/analytics/comparison")
    assert res.status_code == 200
    comp = res.json()
    
    assert len(comp["compared_documents"]) >= 3
    assert len(comp["entity_breakdown"]) >= 3
    
    # Find accounts0607.pdf breakdown
    acc_bk = next((b for b in comp["entity_breakdown"] if "accounts0607.pdf" in b["document"]), None)
    assert acc_bk is not None
    assert acc_bk["mines_projects"] == 66
    assert acc_bk["geological_metrics"] == 59
    assert acc_bk["total_entities"] == 125
    
    # Verify compatible metrics exist and unit segregation note is present
    assert len(comp["compatible_metrics"]) > 0
    assert "Disparate units" in comp["incompatible_metrics_note"]


def test_negative_and_boundary_cases():
    """Validates robustness against empty scopes, non-existent files, and SQL injection."""
    print("\n--- Test 8: Boundary & Negative Cases ---")
    
    # Non-existent document
    res_non = client.get("/api/analytics/summary", params={"source_document": "non_existent_file.pdf"})
    assert res_non.status_code == 200
    s_non = res_non.json()
    assert s_non["total_entities"] == 0
    assert s_non["total_mines_projects"] == 0
    assert s_non["total_geological_metrics"] == 0
    
    # SQL Injection safety test
    res_inj = client.get(
        "/api/analytics/projects",
        params={"source_document": "accounts0607.pdf", "subsidiary": "' OR 1=1 --"},
    )
    assert res_inj.status_code == 200
    p_inj = res_inj.json()
    assert p_inj["total_projects"] == 0  # Parameterized query searches for literal "' OR 1=1 --"
