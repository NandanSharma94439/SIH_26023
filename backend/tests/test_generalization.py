"""
GeoMine Extraction Generalization Test Suite
SIH 2026 — Problem Statement 26023

Proves that GeoMine extraction is genuinely document-driven and generalizes to
novel, unseen mining documents without any canonical-specific hardcoding.

Test Documents (all novel - no overlap with 24/24 canonical benchmark):
  1. GeoMine_Test_Mine_Report_02.pdf          - Dhanpuri East OC Mine, SECL, Sohagpur CF
  2. GeoMine_Test_Mine_Report_03_Kalyanpur.pdf  - Kalyanpur Block, MCL, Talcher CF
  3. GeoMine_Test_Korba_Exploration.xlsx      - Korba-North Block, SECL, Korba CF

Acceptance Criteria:
  + Canonical benchmark: 24/24 = 100% (no regression)
  + Each novel document extracts its own entities from its own content
  + Novel borehole IDs, seam names, project names appear in extracted records
  + Novel fields preserved with provenance
  + NULL/missing fields remain null (no hallucination)
  + RAG answers with citations from retrieved evidence
  + Reports compile from selected document only
"""

import sys
import os
import time
import json
from pathlib import Path
from fastapi.testclient import TestClient

# Path Setup
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app
from app.services.extraction.service import extraction_service
from app.services.extraction.db import extraction_db
from app.services.documents.db import doc_db
from app.services.benchmarks.service import benchmark_service
from app.services.rag.service import GroundedRAGService
from app.schemas.rag import RAGQueryRequest

client = TestClient(app)

# Test Document Paths (repository root)
DOCS_DIR = BASE_DIR.parent
DOC_DHANPURI  = DOCS_DIR / "GeoMine_Test_Mine_Report_02.pdf"
DOC_KALYANPUR = DOCS_DIR / "GeoMine_Test_Mine_Report_03_Kalyanpur.pdf"
DOC_KORBA     = DOCS_DIR / "GeoMine_Test_Korba_Exploration.xlsx"

_uploaded_doc_ids = {}


def _upload_and_process(file_path):
    fname = file_path.name
    # Check if doc_db already has it
    for doc in doc_db.list_documents():
        if doc.filename == fname:
            _uploaded_doc_ids[fname] = doc.id
            return doc.id

    mime_map = {
        ".pdf":  "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".png":  "image/png",
    }
    mime = mime_map.get(file_path.suffix.lower(), "application/octet-stream")
    assert file_path.exists(), f"Test document missing: {file_path}"
    with open(file_path, "rb") as f:
        res = client.post("/api/documents/upload", files={"file": (fname, f, mime)})
    assert res.status_code in (200, 201), f"Upload failed for {fname}: {res.text}"
    data = res.json()
    doc_id = (
        data.get("id")
        or data.get("document_id")
        or (data.get("document") or {}).get("id")
    )
    assert doc_id, f"No document_id returned for {fname}: {data}"
    _uploaded_doc_ids[fname] = doc_id
    return doc_id


# PHASE 0: Pre-test canonical benchmark guard
def test_canonical_benchmark_pre():
    result = benchmark_service.get_accuracy_benchmark()
    assert result.total_fields_tested == 24
    assert result.total_correct_fields == 24
    assert result.overall_extraction_accuracy_percent == 100.0
    print("CANONICAL BENCHMARK PRE-TEST: 24/24 = 100% - PASSED")


# PHASE 1: Architecture audit - no hardcoded canonical references in extraction
def test_no_canonical_hardcoding_in_extraction_pipeline():
    extraction_svc = BASE_DIR / "app" / "services" / "extraction" / "service.py"
    extraction_db_file  = BASE_DIR / "app" / "services" / "extraction" / "db.py"
    FORBIDDEN = [
        "BH-204", "BH204", "SEAM-VIII", "SEAM-VII",
        "Sector-B", "accounts0607",
        "Borehole_Logging_Data", "CMPDI_Mining_Feasibility",
        "CMPDI_Geological_Report_NK", "Scanned_Borehole",
    ]
    for path in [extraction_svc, extraction_db_file]:
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, f"Hardcoding found in {path.name}: {token!r}"
    for fname in ["generator.py", "assembler.py", "exporters.py", "service.py"]:
        path = BASE_DIR / "app" / "services" / "reports" / fname
        if path.exists():
            text = path.read_text(encoding="utf-8")
            for token in FORBIDDEN:
                assert token not in text, f"Hardcoding found in reports/{fname}: {token!r}"
    print("ARCHITECTURE: No canonical hardcoding in extraction/report pipeline - PASSED")


# PHASE 2: Upload novel documents
def test_upload_dhanpuri_pdf():
    doc_id = _upload_and_process(DOC_DHANPURI)
    res = client.get(f"/api/documents/{doc_id}")
    assert res.status_code == 200
    fname = (res.json().get("metadata") or {}).get("filename") or res.json().get("filename")
    assert fname == "GeoMine_Test_Mine_Report_02.pdf"
    print(f"UPLOAD: Dhanpuri East PDF - PASSED (id={doc_id[:12]})")


def test_upload_kalyanpur_pdf():
    doc_id = _upload_and_process(DOC_KALYANPUR)
    res = client.get(f"/api/documents/{doc_id}")
    assert res.status_code == 200
    fname = (res.json().get("metadata") or {}).get("filename") or res.json().get("filename")
    assert fname == "GeoMine_Test_Mine_Report_03_Kalyanpur.pdf"
    print(f"UPLOAD: Kalyanpur Block PDF - PASSED (id={doc_id[:12]})")


def test_upload_korba_xlsx():
    doc_id = _upload_and_process(DOC_KORBA)
    res = client.get(f"/api/documents/{doc_id}")
    assert res.status_code == 200
    fname = (res.json().get("metadata") or {}).get("filename") or res.json().get("filename")
    assert fname == "GeoMine_Test_Korba_Exploration.xlsx"
    print(f"UPLOAD: Korba XLSX - PASSED (id={doc_id[:12]})")


# PHASE 3: Extraction from novel documents
def test_extract_dhanpuri():
    doc_id = _uploaded_doc_ids.get("GeoMine_Test_Mine_Report_02.pdf")
    if not doc_id:
        doc_id = _upload_and_process(DOC_DHANPURI)

    mines = extraction_service.get_mines(document_id=doc_id)
    if not mines and extraction_service.is_configured:
        res = client.post(f"/api/extraction/document/{doc_id}")
        assert res.status_code == 200
        assert res.json().get("success"), f"Extraction failure: {res.json()}"
        mines = extraction_service.get_mines(document_id=doc_id)

    bores = extraction_service.get_boreholes(document_id=doc_id)
    seams = extraction_service.get_seams(document_id=doc_id)
    metrics = extraction_service.get_metrics(document_id=doc_id)

    assert len(mines) > 0, "Dhanpuri: zero mines extracted"
    assert len(bores) > 0, "Dhanpuri: zero boreholes extracted"
    assert len(seams) > 0, "Dhanpuri: zero seams extracted"

    names = [m.project_name.lower() for m in mines]
    bh_ids = [b.borehole_id.upper() for b in bores]
    seam_ids = [s.seam_id.lower() for s in seams]

    assert any("dhanpuri" in n or "deocm" in n for n in names), f"Expected Dhanpuri mine, got: {names}"
    assert any("DE-BH" in b or "DEBH" in b for b in bh_ids), f"Expected DE-BH boreholes, got: {bh_ids}"
    assert any("johilla" in s for s in seam_ids), f"Expected Johilla seams, got: {seam_ids}"

    for bh in bores:
        assert bh.evidence_text and bh.source_document and bh.source_page >= 1
    print(f"EXTRACTION: Dhanpuri East - mines={len(mines)}, bores={len(bores)}, seams={len(seams)}, metrics={len(metrics)} - PASSED")


def test_extract_kalyanpur():
    doc_id = _uploaded_doc_ids.get("GeoMine_Test_Mine_Report_03_Kalyanpur.pdf")
    if not doc_id:
        doc_id = _upload_and_process(DOC_KALYANPUR)

    mines = extraction_service.get_mines(document_id=doc_id)
    if not mines and extraction_service.is_configured:
        res = client.post(f"/api/extraction/document/{doc_id}")
        assert res.status_code == 200
        assert res.json().get("success")
        mines = extraction_service.get_mines(document_id=doc_id)

    bores = extraction_service.get_boreholes(document_id=doc_id)
    seams = extraction_service.get_seams(document_id=doc_id)
    metrics = extraction_service.get_metrics(document_id=doc_id)

    assert len(mines) > 0, "Kalyanpur: zero mines extracted"
    assert len(bores) > 0, "Kalyanpur: zero boreholes extracted"
    assert len(seams) > 0, "Kalyanpur: zero seams extracted"

    names = [m.project_name.lower() for m in mines]
    bh_ids = [b.borehole_id.upper() for b in bores]
    seam_n = [s.seam_id.lower() for s in seams]

    assert any("kalyanpur" in n or "mcl" in n or "talcher" in n for n in names), f"Expected Kalyanpur, got: {names}"
    assert any("KB" in b for b in bh_ids), f"Expected KB-xxx boreholes, got: {bh_ids}"
    assert any("lajkura" in s or "rampur" in s or "balaji" in s for s in seam_n), f"Expected Talcher seams, got: {seam_n}"
    print(f"EXTRACTION: Kalyanpur Block - mines={len(mines)}, bores={len(bores)}, seams={len(seams)}, metrics={len(metrics)} - PASSED")


def test_extract_korba_xlsx():
    doc_id = _uploaded_doc_ids.get("GeoMine_Test_Korba_Exploration.xlsx")
    if not doc_id:
        doc_id = _upload_and_process(DOC_KORBA)

    bores = extraction_service.get_boreholes(document_id=doc_id)
    if not bores and extraction_service.is_configured:
        res = client.post(f"/api/extraction/document/{doc_id}")
        assert res.status_code == 200
        assert res.json().get("success")
        bores = extraction_service.get_boreholes(document_id=doc_id)

    mines = extraction_service.get_mines(document_id=doc_id)
    seams = extraction_service.get_seams(document_id=doc_id)
    prox = extraction_service.get_proximate_analyses(document_id=doc_id)
    metrics = extraction_service.get_metrics(document_id=doc_id)

    combined = len(mines) + len(bores) + len(seams) + len(prox) + len(metrics)
    assert combined > 0, "Korba XLSX: all entity lists empty"

    bh_ids = [b.borehole_id.upper() for b in bores]
    seam_n = [s.seam_id.lower() for s in seams]
    met_n = [m.metric_name.lower() for m in metrics]

    has_novel = (
        any("KN" in b or "KORBA" in b for b in bh_ids)
        or any("korba" in s or "seam-a" in s for s in seam_n)
        or any("korba" in m or "drilling" in m for m in met_n)
    )
    assert has_novel, f"Expected Korba-specific entities. bh={bh_ids}, seams={seam_n}, metrics={met_n}"
    print(f"EXTRACTION: Korba XLSX - total entities={combined}, bores={len(bores)}, seams={len(seams)} - PASSED")


# PHASE 4: Null field preservation
def test_null_fields_not_hallucinated():
    doc_id = _uploaded_doc_ids.get("GeoMine_Test_Mine_Report_02.pdf")
    if not doc_id:
        doc_id = _upload_and_process(DOC_DHANPURI)
    bores = extraction_service.get_boreholes(document_id=doc_id)
    assert len(bores) > 0
    for bh in bores:
        assert bh.latitude is None, f"Borehole {bh.borehole_id}: lat should be null, got {bh.latitude}"
        assert bh.longitude is None, f"Borehole {bh.borehole_id}: lon should be null, got {bh.longitude}"
    print(f"NULL-FIELDS: {len(bores)} boreholes have lat/lon=null (no hallucination) - PASSED")


# PHASE 5: No cross-document contamination
def test_no_contamination_of_canonical_records():
    bores = extraction_service.get_boreholes()
    assert any(b.borehole_id == "BH-204" for b in bores), "Canonical BH-204 missing!"
    seams = extraction_service.get_seams()
    assert any("SEAM-VIII" in s.seam_id for s in seams), "Canonical SEAM-VIII missing!"
    mines = extraction_service.get_mines()
    assert any("Sector-B" in m.project_name for m in mines), "Canonical Sector-B missing!"
    result = benchmark_service.get_accuracy_benchmark()
    assert result.total_correct_fields == 24, f"Benchmark degraded: {result.total_correct_fields}/24"
    print("NO-CONTAMINATION: Canonical records intact, benchmark still 24/24 - PASSED")


# PHASE 6: Scoped report isolation
def test_scoped_report_no_canonical_leakage():
    doc_id = _uploaded_doc_ids.get("GeoMine_Test_Mine_Report_02.pdf")
    if not doc_id:
        doc_id = _upload_and_process(DOC_DHANPURI)
    res = client.post("/api/reports/generate", json={
        "report_type": "cmpdi_geological_summary",
        "scope": "document",
        "document_id": doc_id,
        "custom_title": "Dhanpuri East OC Mine Geological Summary",
    })
    assert res.status_code == 200, f"Report generation failed: {res.text}"
    markdown = res.json().get("markdown_content", "")
    assert len(markdown) > 100
    canonical_entities = ["BH-204", "Sector-B", "SEAM-VIII", "SEAM-VII", "accounts0607"]
    for entity in canonical_entities:
        assert entity not in markdown, f"Canonical entity {entity!r} leaked into scoped report!"
    print("REPORT-ISOLATION: Scoped report contains no canonical data leakage - PASSED")


# PHASE 7: Provenance integrity on novel entities
def test_novel_entity_provenance():
    novel_filenames = {
        "GeoMine_Test_Mine_Report_02.pdf",
        "GeoMine_Test_Mine_Report_03_Kalyanpur.pdf",
        "GeoMine_Test_Korba_Exploration.xlsx",
    }
    all_entities = []
    all_entities += [(b, "borehole") for b in extraction_service.get_boreholes() if b.source_document in novel_filenames]
    all_entities += [(s, "seam")     for s in extraction_service.get_seams()     if s.source_document in novel_filenames]
    all_entities += [(p, "proximate")for p in extraction_service.get_proximate_analyses() if p.source_document in novel_filenames]
    all_entities += [(m, "mine")     for m in extraction_service.get_mines()     if m.source_document in novel_filenames]
    all_entities += [(g, "metric")   for g in extraction_service.get_metrics()   if g.source_document in novel_filenames]
    assert len(all_entities) > 0, "No novel entities found in database!"

    violations = []
    for entity, etype in all_entities:
        if not entity.evidence_text: violations.append(f"{etype} missing evidence_text")
        if not entity.source_document: violations.append(f"{etype} missing source_document")
        if not entity.source_page or entity.source_page < 1: violations.append(f"{etype} invalid source_page")
        if not entity.document_id: violations.append(f"{etype} missing document_id")
    assert not violations, "Provenance violations:\n" + "\n".join(violations)
    print(f"PROVENANCE: {len(all_entities)} novel entities all have complete provenance - PASSED")


# PHASE 8: RAG queries on novel documents (scoped retrieval, citations, anti-hallucination)
def test_rag_novel_document_and_anti_hallucination():
    rag = GroundedRAGService()
    if not rag.embedding_service.is_configured:
        print("RAG: Gemini not configured - skipping RAG query test")
        return

    doc_id_dhanpuri = _uploaded_doc_ids.get("GeoMine_Test_Mine_Report_02.pdf")
    if not doc_id_dhanpuri:
        doc_id_dhanpuri = _upload_and_process(DOC_DHANPURI)

    # 1. Scoped query on Dhanpuri
    req1 = RAGQueryRequest(
        query="What is the total gross coal reserve and stripping ratio for Dhanpuri East OC Mine?",
        document_ids=[doc_id_dhanpuri],
    )
    res1 = rag.query(req1)
    assert res1.evidence_found, f"RAG failed to find evidence: {res1.answer}"
    assert len(res1.sources) > 0
    # Provenance citation check: sources must only cite Dhanpuri document
    for s in res1.sources:
        assert s.filename == "GeoMine_Test_Mine_Report_02.pdf", f"Unexpected source document: {s.filename}"
    assert "88.1" in res1.answer or "gross" in res1.answer.lower()
    print("RAG-SCOPED: Dhanpuri scoped query returned grounded answer with citations - PASSED")

    # 2. Insufficient evidence query (anti-hallucination)
    req2 = RAGQueryRequest(
        query="What is the uranium-235 concentration in borehole DE-BH-01?",
        document_ids=[doc_id_dhanpuri],
    )
    res2 = rag.query(req2)
    assert "not found" in res2.answer.lower(), f"Expected not found message, got: {res2.answer}"
    assert not res2.evidence_found
    print("RAG-ANTI-HALLUCINATION: Unanswerable query correctly returned not-found - PASSED")


# PHASE 9: Post-test canonical benchmark guard
def test_canonical_benchmark_post():
    result = benchmark_service.get_accuracy_benchmark()
    assert result.total_fields_tested == 24
    assert result.total_correct_fields == 24
    assert result.overall_extraction_accuracy_percent == 100.0
    print("CANONICAL BENCHMARK POST-TEST: 24/24 = 100% - PASSED")
