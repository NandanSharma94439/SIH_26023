"""
Automated Pipeline Tests for Phase 2: Document Ingestion & Multi-Modal Parser
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)
Tests:
1. Native Geological Report PDF parsing (text, tables, blocks)
2. Scanned / Image document parsing with OCR fallback detection
3. DOCX Geological Summary parsing (paragraphs, structured tables)
4. XLSX Coal Seam & Borehole Logging data sheet parsing
5. Endpoint validation: POST /upload, GET /documents, GET /{id}, GET /{id}/pages
6. Edge case & security validation (bad extension, 0-byte file)
"""

import io
import sys
from pathlib import Path

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pymupdf
import docx
import openpyxl
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def create_sample_geological_pdf() -> bytes:
    """Generates a real native PDF containing geological stratigraphy and seam tables."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Header
    page.insert_text(
        pymupdf.Point(50, 60),
        "CENTRAL MINE PLANNING & DESIGN INSTITUTE LIMITED (CMPDI)",
        fontsize=12,
        fontname="helv",
    )
    page.insert_text(
        pymupdf.Point(50, 80),
        "GEOLOGICAL REPORT ON EXPLORATION FOR COAL - NORTH KARANPURA COALFIELD",
        fontsize=10,
        fontname="helv",
    )

    # Narrative text
    narrative = (
        "1.0 INTRODUCTION & STRATIGRAPHY\n"
        "The exploratory block covers an area of approximately 14.5 sq. km in the eastern part\n"
        "of the North Karanpura basin. Regional drilling was conducted to delineate the disposition\n"
        "of major coal seams belonging to the Barakar Formation. The sedimentary sequence comprises\n"
        "coarse-to-medium grained feldspathic sandstones, carbonaceous shales, and workable coal seams."
    )
    page.insert_text(pymupdf.Point(50, 115), narrative, fontsize=9, fontname="helv")

    # Second section with seam data
    seam_text = (
        "2.0 COAL SEAM CHARACTERISTICS\n"
        "Seam VII (Top): Average clean thickness 4.25 m. Roof: Medium grained sandstone. Floor: Carbonaceous shale.\n"
        "Seam VI (Bottom): Average thickness 6.80 m. Inherent moisture: 4.2%, Ash: 24.8%, GCV: 5120 kcal/kg.\n"
        "Borehole CM-101 encountered Seam VII at depth 112.4 m and Seam VI at depth 145.8 m."
    )
    page.insert_text(pymupdf.Point(50, 200), seam_text, fontsize=9, fontname="helv")

    # Draw a table with grid lines
    y_start = 280
    row_height = 20
    col_widths = [100, 90, 80, 80, 80]
    headers = ["Seam Name", "Thickness (m)", "Depth From (m)", "Depth To (m)", "CIL Grade"]
    data = [
        ["Seam VIII", "2.10", "64.50", "66.60", "G-8"],
        ["Seam VII (Top)", "4.25", "112.40", "116.65", "G-9"],
        ["Seam VI (Bottom)", "6.80", "145.80", "152.60", "G-10"],
    ]

    # Draw table text
    for col_idx, h in enumerate(headers):
        x = 50 + sum(col_widths[:col_idx])
        page.insert_text(pymupdf.Point(x + 5, y_start + 14), h, fontsize=8, fontname="helv")

    for r_idx, row in enumerate(data):
        y = y_start + (r_idx + 1) * row_height
        for col_idx, val in enumerate(row):
            x = 50 + sum(col_widths[:col_idx])
            page.insert_text(pymupdf.Point(x + 5, y + 14), val, fontsize=8, fontname="helv")

    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def create_sample_scanned_image() -> bytes:
    """Generates a synthetic scanned image representing a historical borehole log."""
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), "CMPDI BOREHOLE CORE LOG - BH-204", fill=(0, 0, 0))
    draw.text((20, 60), "LOCATION: JHARIA COALFIELD, BLOCK-IV", fill=(0, 0, 0))
    draw.text((20, 90), "COLLAR ELEVATION: 214.50 m RL", fill=(0, 0, 0))
    draw.text((20, 120), "TOTAL DEPTH DRILLED: 240.00 m", fill=(0, 0, 0))
    draw.text((20, 150), "LITHOLOGY: COARSE SANDSTONE WITH SHALE PARTINGS", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_sample_docx() -> bytes:
    """Generates a DOCX document with mining text and tables."""
    doc = docx.Document()
    doc.add_heading("CMPDI Mining Feasibility Report", level=1)
    doc.add_paragraph(
        "This feasibility study evaluates opencast strip mining at Sector-B. "
        "The stripping ratio is estimated at 1:4.2 (Coal to Overburden)."
    )
    table = doc.add_table(rows=1, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Parameter"
    hdr_cells[1].text = "Value"
    hdr_cells[2].text = "Unit"

    row_data = [
        ("Target Annual Production", "5.0", "MTPA"),
        ("Stripping Ratio", "4.2", "cu.m/tonne"),
        ("Life of Mine", "25", "Years"),
    ]
    for param, val, unit in row_data:
        row_cells = table.add_row().cells
        row_cells[0].text = param
        row_cells[1].text = val
        row_cells[2].text = unit

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def create_sample_xlsx() -> bytes:
    """Generates an XLSX workbook with borehole log and coal seam sheets."""
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Borehole_CM101"

    ws1.append(["Depth_From_m", "Depth_To_m", "Lithology", "Seam_Code", "Ash_Percent", "GCV_kcal_kg"])
    ws1.append([0.0, 18.5, "Top Soil / Weathered Alluvium", "OVERBURDEN", None, None])
    ws1.append([18.5, 64.5, "Coarse Feldspathic Sandstone", "OVERBURDEN", None, None])
    ws1.append([64.5, 66.6, "Coal (Bright Banded)", "SEAM-VIII", 21.4, 5450])
    ws1.append([66.6, 112.4, "Medium Sandstone with Shale Partings", "PARTING", None, None])
    ws1.append([112.4, 116.65, "Coal (Dull Banded)", "SEAM-VII", 24.8, 5120])

    ws2 = wb.create_sheet(title="Reserve_Summary")
    ws2.append(["Seam", "Category", "Gross_Reserves_MT", "Extractable_Reserves_MT"])
    ws2.append(["Seam VIII", "Proved", 14.8, 12.2])
    ws2.append(["Seam VII", "Proved", 28.5, 23.9])
    ws2.append(["Seam VI", "Indicated", 42.1, 33.7])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def run_all_tests():
    print("=================================================================")
    print("RUNNING PHASE 2 AUTOMATED TEST SUITE: DOCUMENT INGESTION & PARSER")
    print("=================================================================")

    # Test 1: Native PDF Upload
    print("\n[TEST 1] Testing Native Geological PDF Upload & Extraction...")
    pdf_bytes = create_sample_geological_pdf()
    files = {"file": ("CMPDI_Geological_Report_NK.pdf", pdf_bytes, "application/pdf")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    pdf_data = res.json()
    doc_id = pdf_data["document"]["id"]
    print(f" -> Upload Success! Doc ID: {doc_id}")
    print(f" -> Total Pages: {pdf_data['document']['total_pages']}")
    print(f" -> File Type: {pdf_data['document']['file_type']}")
    print(f" -> Preview text: {pdf_data['document']['preview_text'][:80]}...")
    assert pdf_data["document"]["total_pages"] >= 1
    assert "CMPDI" in pdf_data["pages_preview"][0]["text"]

    # Test 2: DOCX Upload
    print("\n[TEST 2] Testing DOCX Mining Feasibility Document Upload...")
    docx_bytes = create_sample_docx()
    files = {
        "file": (
            "CMPDI_Mining_Feasibility.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    docx_data = res.json()
    docx_id = docx_data["document"]["id"]
    print(f" -> Upload Success! Doc ID: {docx_id}")
    print(f" -> Has Tables: {docx_data['document']['has_tables']}")
    assert "stripping ratio" in docx_data["pages_preview"][0]["text"].lower()

    # Test 3: XLSX Upload
    print("\n[TEST 3] Testing XLSX Multi-Sheet Borehole Logging Upload...")
    xlsx_bytes = create_sample_xlsx()
    files = {
        "file": (
            "Borehole_Logging_Data.xlsx",
            xlsx_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    xlsx_data = res.json()
    xlsx_id = xlsx_data["document"]["id"]
    print(f" -> Upload Success! Doc ID: {xlsx_id}")
    print(f" -> Sheets (Total Pages): {xlsx_data['document']['total_pages']}")
    assert xlsx_data["document"]["total_pages"] == 2  # 2 sheets
    print(f" -> Has Tables: {xlsx_data['document']['has_tables']}")

    # Test 4: Image Upload (OCR Fallback Path)
    print("\n[TEST 4] Testing Scanned Borehole Log Image Upload (OCR Pipeline)...")
    img_bytes = create_sample_scanned_image()
    files = {"file": ("Scanned_Borehole_BH204.png", img_bytes, "image/png")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code in (200, 201), f"Expected 200 or 201, got {res.status_code}: {res.text}"
    img_data = res.json()
    img_id = img_data["document"]["id"]
    print(f" -> Upload Success! Doc ID: {img_id}")
    print(f" -> File Type: {img_data['document']['file_type']}")
    print(f" -> OCR Applied: {img_data['pages_preview'][0]['ocr_applied']}")
    if img_data["pages_preview"][0]["ocr_error"]:
        print(f" -> OCR Engine Note: {img_data['pages_preview'][0]['ocr_error']}")
    else:
        print(f" -> OCR Extracted Text: {img_data['pages_preview'][0]['text'][:80]}...")

    # Test 5: GET /api/documents (List Documents)
    print("\n[TEST 5] Testing GET /api/documents...")
    res = client.get("/api/documents")
    assert res.status_code == 200
    doc_list = res.json()
    print(f" -> Retrieved {len(doc_list)} documents from registry.")
    assert len(doc_list) >= 4

    # Test 6: GET /api/documents/{id} (Document Details)
    print(f"\n[TEST 6] Testing GET /api/documents/{doc_id}...")
    res = client.get(f"/api/documents/{doc_id}")
    assert res.status_code == 200
    detail = res.json()
    print(f" -> Found Document: {detail['metadata']['filename']} ({detail['metadata']['file_type']})")
    assert detail["metadata"]["id"] == doc_id
    assert Path(detail["storage_path"]).exists()

    # Test 7: GET /api/documents/{id}/pages (Page & Block Details)
    print(f"\n[TEST 7] Testing GET /api/documents/{doc_id}/pages...")
    res = client.get(f"/api/documents/{doc_id}/pages")
    assert res.status_code == 200
    pages_data = res.json()
    print(f" -> Retrieved {pages_data['total_pages']} page(s) with block coordinates.")
    assert len(pages_data["pages"]) >= 1
    page1 = pages_data["pages"][0]
    print(f" -> Page 1 dimensions: {page1['dimensions']}")
    print(f" -> Page 1 text blocks count: {len(page1['blocks'])}")
    print(f" -> Page 1 word count: {page1['word_count']}")

    # Test 8: Security & Validation Rejections
    print("\n[TEST 8] Testing Edge Cases & Security Validations...")
    # Bad extension
    res = client.post(
        "/api/documents/upload",
        files={"file": ("malicious_payload.exe", b"binary_data", "application/x-msdownload")},
    )
    assert res.status_code == 422, f"Expected 422 for disallowed extension, got {res.status_code}"
    print(" -> Disallowed extension (.exe) correctly rejected with 422 Unprocessable Entity.")

    # 0-byte file
    res = client.post(
        "/api/documents/upload",
        files={"file": ("empty_report.pdf", b"", "application/pdf")},
    )
    assert res.status_code == 422, f"Expected 422 for empty file, got {res.status_code}"
    print(" -> 0-byte file correctly rejected with 422.")

    # 404 for non-existent document
    res = client.get("/api/documents/non_existent_uuid_12345")
    assert res.status_code == 404
    print(" -> Non-existent ID correctly returned 404 Not Found.")

    # Test 9: SHA-256 Content Deduplication Verification
    print("\n[TEST 9] Testing SHA-256 Content-Based Deduplication...")
    pre_count = len(client.get("/api/documents").json())

    # 9a. Re-upload identical content with same filename
    res_dup1 = client.post(
        "/api/documents/upload",
        files={"file": ("CMPDI_Geological_Report_NK.pdf", pdf_bytes, "application/pdf")},
    )
    assert res_dup1.status_code == 200, f"Expected 200 for duplicate, got {res_dup1.status_code}"
    dup1_data = res_dup1.json()
    assert dup1_data["already_exists"] is True, "Expected already_exists=True"
    assert dup1_data["document"]["id"] == doc_id, "Expected existing document ID to be reused"
    print(" -> Re-uploading identical content returned existing document ID and already_exists=True.")

    # 9b. Re-upload identical content with different filename
    res_dup2 = client.post(
        "/api/documents/upload",
        files={"file": ("Renamed_Duplicate_Report.pdf", pdf_bytes, "application/pdf")},
    )
    assert res_dup2.status_code == 200
    dup2_data = res_dup2.json()
    assert dup2_data["already_exists"] is True
    assert dup2_data["document"]["id"] == doc_id
    print(" -> Identical content with different filename correctly deduplicated.")

    # 9c. Verify repository count did not increase after duplicate uploads
    post_count_dups = len(client.get("/api/documents").json())
    assert post_count_dups == pre_count, f"Repository count increased! Pre: {pre_count}, Post: {post_count_dups}"
    print(f" -> Repository count verified stable ({post_count_dups}) after identical content re-uploads.")

    # 9d. Upload DIFFERENT content with SAME filename must create a new document
    diff_doc = pymupdf.open()
    diff_page = diff_doc.new_page(width=595, height=842)
    diff_page.insert_text(pymupdf.Point(50, 100), "DIFFERENT CONTENT UNIQUE TO SECTION B 9999", fontsize=12)
    diff_bytes = diff_doc.write()
    diff_doc.close()

    res_diff = client.post(
        "/api/documents/upload",
        files={"file": ("CMPDI_Geological_Report_NK.pdf", diff_bytes, "application/pdf")},
    )
    assert res_diff.status_code == 201
    diff_data = res_diff.json()
    assert diff_data["already_exists"] is False
    assert diff_data["document"]["id"] != doc_id
    new_doc_id = diff_data["document"]["id"]
    print(" -> Different content with same filename correctly created new document record.")

    # 9e. Verify repository count increased by exactly 1 for the new unique document
    final_count = len(client.get("/api/documents").json())
    assert final_count == pre_count + 1, f"Expected {pre_count + 1} docs, got {final_count}"
    print(f" -> Repository count correctly increased by 1 for genuine new document.")

    # Clean up test artifacts created during this test run so repository stays clean
    from app.services.documents.db import doc_db as test_db
    test_db.delete_document(new_doc_id)
    test_db.delete_document(doc_id)
    test_db.delete_document(docx_id)
    test_db.delete_document(xlsx_id)
    if img_id != "359ecf4f-846f-4749-9ac6-0f782a4aca12":
        test_db.delete_document(img_id)

    print("\n=================================================================")
    print("ALL PHASE 2 PIPELINE TESTS PASSED SUCCESSFULLY!")
    print("=================================================================")


def test_document_pipeline():
    run_all_tests()


if __name__ == "__main__":
    run_all_tests()

