"""
Automated Verification Test for Phase 4 Document-Scoped Filtering
SIH 2026 PS 26023 (CMPDI / Coal India Limited)

Tests:
1. accounts0607.pdf:
   - boreholes: 0
   - coal_seams: 0
   - proximate_analyses: 0
   - mine_projects: 66
   - geological_metrics: 59
2. Scanned_Borehole_BH204_OCR.png:
   - BH-204 appears with collar elevation and depth
3. Borehole_Logging_Data.xlsx:
   - CM101 borehole appears
   - Coal seams appear (Seam VIII, Seam VII)
   - Proximate analysis appears (Ash %, GCV)
4. Dynamic switching & scope verification (Current Document vs All Documents)
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.services.extraction.service import extraction_service

client = TestClient(app)


def test_accounts0607_pdf_filtering():
    """Requirement 10A: accounts0607.pdf -> 0 boreholes, 0 seams, 0 proximate, 66 mines, 59 metrics."""
    print("\n--- Test A: accounts0607.pdf Filtering ---")
    doc_name = "accounts0607.pdf"

    # Query boreholes
    res_b = client.get("/api/extraction/boreholes", params={"source_document": doc_name})
    assert res_b.status_code == 200
    boreholes = res_b.json()
    print(f"accounts0607.pdf boreholes count: {len(boreholes)}")
    assert len(boreholes) == 0, f"Expected 0 boreholes, got {len(boreholes)}"

    # Query seams
    res_s = client.get("/api/extraction/seams", params={"source_document": doc_name})
    assert res_s.status_code == 200
    seams = res_s.json()
    print(f"accounts0607.pdf seams count: {len(seams)}")
    assert len(seams) == 0, f"Expected 0 seams, got {len(seams)}"

    # Query proximate
    res_p = client.get("/api/extraction/proximate-analysis", params={"source_document": doc_name})
    assert res_p.status_code == 200
    proximate = res_p.json()
    print(f"accounts0607.pdf proximate count: {len(proximate)}")
    assert len(proximate) == 0, f"Expected 0 proximate records, got {len(proximate)}"

    # Query mines
    res_m = client.get("/api/extraction/mines", params={"source_document": doc_name})
    assert res_m.status_code == 200
    mines = res_m.json()
    print(f"accounts0607.pdf mines count: {len(mines)}")
    assert len(mines) == 66, f"Expected 66 mines, got {len(mines)}"

    # Query metrics
    res_g = client.get("/api/extraction/metrics", params={"source_document": doc_name})
    assert res_g.status_code == 200
    metrics = res_g.json()
    print(f"accounts0607.pdf metrics count: {len(metrics)}")
    assert len(metrics) == 59, f"Expected 59 metrics, got {len(metrics)}"

    print("accounts0607.pdf Scoped Filtering: PASSED (0, 0, 0, 66, 59)")


def test_bh204_ocr_filtering():
    """Requirement 10B: Scanned_Borehole_BH204_OCR.png -> BH-204 should appear."""
    print("\n--- Test B: Scanned_Borehole_BH204_OCR.png Filtering ---")
    doc_name = "Scanned_Borehole_BH204_OCR.png"

    res_b = client.get("/api/extraction/boreholes", params={"source_document": doc_name})
    assert res_b.status_code == 200
    boreholes = res_b.json()
    print(f"BH204 boreholes count: {len(boreholes)}")
    assert len(boreholes) >= 1, "Expected BH-204 to appear"

    bh204 = next((b for b in boreholes if b["borehole_id"] == "BH-204"), None)
    assert bh204 is not None, "BH-204 not found in extracted records!"
    assert bh204["collar_elevation"] == 214.50
    assert bh204["total_depth"] == 240.00
    assert bh204["source_document"] == doc_name
    print(f"Found {bh204['borehole_id']}: Elevation {bh204['collar_elevation']} m RL, Depth {bh204['total_depth']} m")

    # Verify seams and proximate are 0 for BH204
    res_s = client.get("/api/extraction/seams", params={"source_document": doc_name})
    assert len(res_s.json()) == 0

    res_p = client.get("/api/extraction/proximate-analysis", params={"source_document": doc_name})
    assert len(res_p.json()) == 0

    print("BH-204 Scoped Filtering: PASSED")


def test_borehole_logging_xlsx_filtering():
    """Requirement 10C: Borehole_Logging_Data.xlsx -> CM101/seam/proximate records should appear."""
    print("\n--- Test C: Borehole_Logging_Data.xlsx Filtering ---")
    doc_name = "Borehole_Logging_Data.xlsx"

    # Borehole CM101
    res_b = client.get("/api/extraction/boreholes", params={"source_document": doc_name})
    assert res_b.status_code == 200
    boreholes = res_b.json()
    print(f"XLSX boreholes count: {len(boreholes)}")
    assert len(boreholes) >= 1
    cm101 = next((b for b in boreholes if "CM101" in b["borehole_id"] or "CM-101" in b["borehole_id"]), None)
    assert cm101 is not None, "CM101 borehole not found!"
    print(f"Found borehole: {cm101['borehole_id']}")

    # Seams (Seam VIII, Seam VII)
    res_s = client.get("/api/extraction/seams", params={"source_document": doc_name})
    assert res_s.status_code == 200
    seams = res_s.json()
    print(f"XLSX seams count: {len(seams)}")
    assert len(seams) >= 2, "Expected seams to appear for XLSX"
    seam_ids = [s["seam_id"] for s in seams]
    print(f"Extracted seams: {seam_ids}")
    assert any("VIII" in sid for sid in seam_ids), "Seam VIII not found!"

    # Proximate (Ash %, GCV)
    res_p = client.get("/api/extraction/proximate-analysis", params={"source_document": doc_name})
    assert res_p.status_code == 200
    prox = res_p.json()
    print(f"XLSX proximate count: {len(prox)}")
    assert len(prox) >= 1
    ash_rec = next((p for p in prox if p["ash_percent"] == 21.4), None)
    assert ash_rec is not None, "Ash 21.4% record not found!"
    assert ash_rec["gross_calorific_value"] == 5450.0
    print(f"Found proximate record: Ash {ash_rec['ash_percent']}%, GCV {ash_rec['gross_calorific_value']} kcal/kg")

    print("Borehole_Logging_Data.xlsx Scoped Filtering: PASSED")


def test_cumulative_all_documents_scope():
    """Verifies that All Documents mode displays all cumulative records without filtering."""
    print("\n--- Test D: All Documents Cumulative Scope ---")
    res_b = client.get("/api/extraction/boreholes")
    boreholes = res_b.json()
    print(f"Global boreholes count: {len(boreholes)}")
    assert len(boreholes) >= 3, "Expected at least 3 boreholes across all documents"

    res_s = client.get("/api/extraction/seams")
    seams = res_s.json()
    print(f"Global seams count: {len(seams)}")
    assert len(seams) >= 12, "Expected at least 12 seams across all documents"

    print("Cumulative All Documents Scope: PASSED")


if __name__ == "__main__":
    print("=================================================================")
    print("RUNNING DOCUMENT-SCOPED FILTERING VERIFICATION SUITE")
    print("=================================================================")
    test_accounts0607_pdf_filtering()
    test_bh204_ocr_filtering()
    test_borehole_logging_xlsx_filtering()
    test_cumulative_all_documents_scope()
    print("\n=================================================================")
    print("ALL DOCUMENT-SCOPED FILTERING TESTS PASSED SUCCESSFULLY!")
    print("=================================================================")
