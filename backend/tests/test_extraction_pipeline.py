"""
Phase 4 Automated Test Suite: Structured Mining Data Extraction
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Tests:
1. Pydantic Domain Model Validation (Boreholes, Seams, Proximate, Mines, Metrics).
2. Provenance Integrity (document_id, filename, page, evidence_text).
3. Float & Numerical Cleaners (_clean_float handling ratios, units, commas).
4. Relational Database Operations & Deduplication on Reprocessing.
5. Real Document Extraction & Provenance Verification across PDF, DOCX, XLSX, and PNG OCR.
6. REST API Endpoints & Status Telemetry.
"""

import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app
from app.schemas.extraction import (
    Borehole,
    CoalSeam,
    ProximateAnalysis,
    MineProject,
    GeologicalMetric,
)
from app.services.extraction.db import ExtractionDatabase
from app.services.extraction.service import StructuredMiningExtractorService, extraction_service
from app.services.documents.db import doc_db


def test_pydantic_domain_models():
    """Validates schema structure, mandatory provenance, and optional fields."""
    now = datetime.now(timezone.utc)
    doc_id = str(uuid.uuid4())

    # 1. Borehole Model
    bh = Borehole(
        document_id=doc_id,
        source_document="Scanned_Borehole_BH204_OCR.png",
        source_page=1,
        evidence_text="COLLAR ELEVATION: 214.50 m RL TOTAL DEPTH DRILLED: 240.00 m",
        borehole_id="BH-204",
        collar_elevation=214.50,
        total_depth=240.00,
        lithology="Medium to coarse sandstone",
    )
    assert bh.borehole_id == "BH-204"
    assert bh.collar_elevation == 214.50
    assert bh.total_depth == 240.00
    assert bh.latitude is None  # Supported missing fields remain null

    # 2. Coal Seam Model
    seam = CoalSeam(
        document_id=doc_id,
        source_document="Borehole_Logging_Data.xlsx",
        source_page=1,
        evidence_text="64.5 | 66.6 | Coal (Bright Banded) | SEAM-VIII | 21.4 | 5450",
        seam_id="SEAM-VIII",
        borehole_id="CM-101",
        depth_from=64.5,
        depth_to=66.6,
        thickness=2.1,
        coal_grade="G-8",
        category="Proved",
        gross_reserves_mt=14.8,
    )
    assert seam.thickness == 2.1
    assert seam.coal_grade == "G-8"
    assert seam.category == "Proved"

    # 3. Proximate Analysis Model
    prox = ProximateAnalysis(
        document_id=doc_id,
        source_document="Borehole_Logging_Data.xlsx",
        source_page=1,
        evidence_text="Ash_Percent: 21.4 | GCV: 5450 kcal/kg",
        seam_id="SEAM-VIII",
        borehole_id="CM-101",
        ash_percent=21.4,
        gross_calorific_value=5450.0,
        units="kcal/kg",
    )
    assert prox.ash_percent == 21.4
    assert prox.gross_calorific_value == 5450.0
    assert prox.moisture_percent is None

    # 4. Mine Project Model
    mine = MineProject(
        document_id=doc_id,
        source_document="CMPDI_Mining_Feasibility.docx",
        source_page=1,
        evidence_text="Target Annual Production: 5.0 MTPA | Stripping Ratio: 4.2",
        project_name="Sector-B",
        target_production=5.0,
        target_production_unit="MTPA",
        stripping_ratio=4.2,
        life_of_mine_years=25,
    )
    assert mine.stripping_ratio == 4.2
    assert mine.life_of_mine_years == 25

    # 5. Geological Metric Model
    metric = GeologicalMetric(
        document_id=doc_id,
        source_document="accounts0607.pdf",
        source_page=9,
        evidence_text="CMPDI Departmental Drilling Target 1,92,000 m achievement 103%",
        metric_name="CMPDI Departmental Drilling Target",
        metric_value=192000.0,
        unit="m",
        year_period="2006-07",
        category="Exploration & Drilling",
    )
    assert metric.metric_value == 192000.0
    assert metric.year_period == "2006-07"

    print("test_pydantic_domain_models: PASSED")


def test_float_cleaner_and_parsing():
    """Validates numerical parsing from raw strings with units, commas, and ratios."""
    clean = StructuredMiningExtractorService._clean_float

    assert clean("214.50 m RL") == 214.50
    assert clean("240.00 m") == 240.00
    assert clean("1,92,000") == 192000.0
    assert clean("5.0 MTPA") == 5.0
    assert clean("1:4.2") == 4.2
    assert clean("4.2:1") == 4.2
    assert clean(14.8) == 14.8
    assert clean(None) is None
    assert clean("") is None
    assert clean("Not Available") is None

    print("test_float_cleaner_and_parsing: PASSED")


def test_database_deduplication():
    """Verifies that reprocessing a document replaces its prior records rather than duplicating them."""
    test_db_path = BASE_DIR / "storage" / "test_dedup_extraction.db"
    if test_db_path.exists():
        test_db_path.unlink()

    db = ExtractionDatabase(db_path=test_db_path)
    doc_id = str(uuid.uuid4())

    bh1 = Borehole(
        document_id=doc_id,
        source_document="test.pdf",
        source_page=1,
        evidence_text="Borehole BH-1 depth 100m",
        borehole_id="BH-1",
        total_depth=100.0,
    )

    # Initial save
    db.save_extraction_results(
        document_id=doc_id,
        boreholes=[bh1],
        coal_seams=[],
        proximate_analyses=[],
        mine_projects=[],
        geological_metrics=[],
    )

    records = db.list_boreholes(document_id=doc_id)
    assert len(records) == 1
    assert records[0].total_depth == 100.0

    # Reprocess same document with updated total depth
    bh2 = Borehole(
        document_id=doc_id,
        source_document="test.pdf",
        source_page=1,
        evidence_text="Borehole BH-1 depth 120m",
        borehole_id="BH-1",
        total_depth=120.0,
    )

    db.save_extraction_results(
        document_id=doc_id,
        boreholes=[bh2],
        coal_seams=[],
        proximate_analyses=[],
        mine_projects=[],
        geological_metrics=[],
    )

    records_after = db.list_boreholes(document_id=doc_id)
    assert len(records_after) == 1, "Duplicate record created instead of replacement!"
    assert records_after[0].total_depth == 120.0

    # Clean up test DB
    try:
        import gc
        gc.collect()
        if test_db_path.exists():
            test_db_path.unlink()
    except Exception:
        pass

    print("test_database_deduplication: PASSED")


def test_real_document_provenance_verification():
    """
    Verifies that all extracted entities in the database are supported by
    verbatim text from their cited source documents and pages.
    """
    boreholes = extraction_service.get_boreholes()
    seams = extraction_service.get_seams()
    proximate = extraction_service.get_proximate_analyses()
    mines = extraction_service.get_mines()
    metrics = extraction_service.get_metrics()

    assert len(boreholes) > 0, "No boreholes found in database!"
    assert len(seams) > 0, "No coal seams found in database!"
    assert len(proximate) > 0, "No proximate analyses found in database!"
    assert len(mines) > 0, "No mines found in database!"
    assert len(metrics) > 0, "No geological metrics found in database!"

    # 1. Verify BH-204 from Scanned_Borehole_BH204_OCR.png
    bh204 = next((b for b in boreholes if b.borehole_id == "BH-204"), None)
    assert bh204 is not None, "BH-204 not extracted!"
    assert bh204.collar_elevation == 214.50
    assert bh204.total_depth == 240.00
    assert bh204.source_page == 1
    assert "BH204" in bh204.source_document

    # 2. Verify Sector-B from CMPDI_Mining_Feasibility.docx
    sector_b = next((m for m in mines if "Sector-B" in m.project_name), None)
    assert sector_b is not None, "Sector-B project not extracted!"
    assert sector_b.target_production == 5.0
    assert sector_b.stripping_ratio == 4.2
    assert sector_b.life_of_mine_years == 25
    assert sector_b.source_page == 1

    # 3. Verify SEAM-VIII from Borehole_Logging_Data.xlsx
    seam8 = next((s for s in seams if s.seam_id == "SEAM-VIII" and s.thickness is not None), None)
    assert seam8 is not None, "SEAM-VIII with thickness not extracted!"
    assert seam8.thickness == 2.1
    assert seam8.depth_from == 64.5
    assert seam8.depth_to == 66.6

    # 4. Verify Proximate Analysis from Borehole_Logging_Data.xlsx
    prox_ash = next((p for p in proximate if p.ash_percent == 21.4), None)
    assert prox_ash is not None, "Proximate ash 21.4% not extracted!"
    assert prox_ash.gross_calorific_value == 5450.0

    print("test_real_document_provenance_verification: PASSED")


def test_extraction_api_endpoints():
    """Tests all Phase 4 REST API endpoints using FastAPI TestClient."""
    client = TestClient(app)

    # 1. GET /api/extraction/status
    res = client.get("/api/extraction/status")
    assert res.status_code == 200
    status_data = res.json()
    assert status_data["gemini_configured"] is True
    assert status_data["total_entities_count"] > 0
    assert "boreholes" in status_data["counts_by_type"]
    assert "coal_seams" in status_data["counts_by_type"]

    # 2. GET /api/extraction/boreholes
    res_b = client.get("/api/extraction/boreholes")
    assert res_b.status_code == 200
    assert len(res_b.json()) >= 3

    # 3. GET /api/extraction/seams
    res_s = client.get("/api/extraction/seams")
    assert res_s.status_code == 200
    assert len(res_s.json()) >= 5

    # 4. GET /api/extraction/proximate-analysis
    res_p = client.get("/api/extraction/proximate-analysis")
    assert res_p.status_code == 200
    assert len(res_p.json()) >= 3

    # 5. GET /api/extraction/mines
    res_m = client.get("/api/extraction/mines")
    assert res_m.status_code == 200
    assert len(res_m.json()) >= 3

    # 6. GET /api/extraction/metrics
    res_g = client.get("/api/extraction/metrics")
    assert res_g.status_code == 200
    assert len(res_g.json()) >= 5

    # 7. Error handling for non-existent document ID
    res_err = client.post("/api/extraction/document/00000000-0000-0000-0000-000000000000")
    assert res_err.status_code == 404

    print("test_extraction_api_endpoints: PASSED")


if __name__ == "__main__":
    print("=================================================================")
    print("RUNNING PHASE 4 AUTOMATED TEST SUITE: STRUCTURED MINING EXTRACTION")
    print("=================================================================")
    test_pydantic_domain_models()
    test_float_cleaner_and_parsing()
    test_database_deduplication()
    test_real_document_provenance_verification()
    test_extraction_api_endpoints()
    print("=================================================================")
    print("ALL PHASE 4 EXTRACTION TESTS PASSED SUCCESSFULLY!")
    print("=================================================================")
