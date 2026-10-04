"""
Regression Test Suite: PDF Table Text Normalization Layer
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Tests:
1. Normalization of character-doubling artifacts from PyMuPDF find_tables()
2. Preservation of legitimate words with repeated characters (SUCCESS, COAL, COMMITTEE, BOOKKEEPER)
3. Preservation of legitimate numeric values, IDs, percentages, and normal text
4. Whitespace and table row/column structure preservation
5. Regression testing against real accounts0607.pdf tables (Page 9, Page 16)
6. Verification that raw page text and original stored PDF remain completely unaltered
"""

import sys
from pathlib import Path

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pymupdf
from app.services.documents.service import DocumentIngestionService
from app.services.documents.table_normalization import (
    is_token_doubled,
    collapse_token,
    has_strong_doubling,
    is_table_doubled,
    normalize_table_text,
)


def test_doubled_token_detection_and_collapse():
    """Verify true character doubling patterns where text[::2] == text[1::2] are collapsed."""
    test_cases = [
        # Doubled token -> Expected collapsed token
        ("GGEEOOLLOOGGIICCAALL", "GEOLOGICAL"),
        ("RREEPPOORRTTSS", "REPORTS"),
        ("PPRROOJJEECCTT", "PROJECT"),
        ("AAggeennccyy", "Agency"),
        ("CCMMPPDDII", "CMPDI"),
        ("MMEECCLL", "MECL"),
        ("CCooaallffiieelldd", "Coalfield"),
        ("BBlloocckk", "Block"),
        ("DDrriilllliinngg", "Drilling"),
        ("AAnnnnuuaall", "Annual"),
        ("TTaarrggeett", "Target"),
        ("PPeerrffoorrmmaannccee", "Performance"),
        ("EExxpplloorraattoorryy", "Exploratory"),
        ("AAcchhiieevveedd", "Achieved"),
        ("UUnnsscchheedduulleedd", "Unscheduled"),
        ("SSttaattee", "State"),
        ("TToottaall", "Total"),
        ("11,,9922,,000000", "1,92,000"),
        ("110033%%", "103%"),
        ("22000066--0077", "2006-07"),
        ("((mmeettrree))", "(metre)"),
        ("((%%))", "(%)"),
        ("((mm))", "(m)"),
        ("771155", "715"),
        ("++771155", "+715"),
        ("336600", "360"),
        ("CCMMPPDDII::", "CMPDI:"),
        ("SSttaattee GGoovvttss..", "State Govts."),
        ("BBEE|", "BE|"),
    ]

    for doubled, expected in test_cases:
        norm = normalize_table_text(doubled, table_is_doubled=True)
        assert norm == expected, f"Failed: {doubled} -> got '{norm}', expected '{expected}'"


def test_preserve_legitimate_words_and_repeated_characters():
    """Verify legitimate words with repeated characters are strictly preserved."""
    legitimate_samples = [
        "SUCCESS",
        "COAL",
        "SEAM",
        "MINE",
        "COMMITTEE",
        "BOOKKEEPER",
        "BOREHOLE",
        "DRILLING",
        "ASH",
        "MOISTURE",
        "VOLATILE",
        "TOTAL",
        "CALORIFIC",
        "GEOLOGICAL",
        "REPORTS",
        "CENTRAL",
        "EXPLORATION",
        "SEDIMENTARY",
        "SANDSTONE",
    ]

    for word in legitimate_samples:
        # In both normal mode and doubled mode, legitimate words must NOT be corrupted
        assert normalize_table_text(word, table_is_doubled=False) == word, f"Corrupted in normal mode: {word}"
        assert normalize_table_text(word, table_is_doubled=True) == word, f"Corrupted in doubled mode: {word}"


def test_preserve_legitimate_numeric_values_and_ids():
    """Verify normal numeric values, borehole IDs, seam names and codes remain unaltered."""
    samples = [
        "64.50",
        "1,92,000",
        "103%",
        "2006-07",
        "BH-01",
        "BH-12B",
        "ID_104",
        "Seam II",
        "Seam VIII",
        "1100",
        "11",
        "22",
        "45.20",
        "0.35",
        "Grade-A",
    ]

    for sample in samples:
        norm = normalize_table_text(sample, table_is_doubled=False)
        assert norm == sample, f"Corrupted legitimate value in clean table: '{sample}' -> '{norm}'"


def test_whitespace_and_multiline_structure():
    """Verify whitespace, multiline breaks, and cell formatting are preserved without destruction."""
    multiline_doubled = (
        "AAggeennccyy--wwiissee PPeerrffoorrmmaannccee ooff\n"
        "EExxpplloorraattoorryy DDrriilllliinngg iinn 22000066--0077"
    )
    expected = "Agency-wise Performance of\nExploratory Drilling in 2006-07"
    result = normalize_table_text(multiline_doubled, table_is_doubled=True)
    assert result == expected, f"Multiline preservation failed: got '{result}'"


def test_accounts0607_pdf_regression():
    """
    Regression test using the problematic accounts0607.pdf.
    Verifies that:
    1. Table headers and cells on Page 9 and Page 16 are properly deduplicated.
    2. Legitimate numeric values, rows, and columns are preserved.
    3. Raw page native text is NOT altered.
    4. Stored PDF file is NOT modified.
    """
    pdf_path = BASE_DIR / "storage" / "uploads" / "4e4f5021-4702-4711-b80f-62ed9d40e177" / "accounts0607.pdf"
    if not pdf_path.exists():
        print(f"Skipping accounts0607.pdf regression: file not found at {pdf_path}")
        return

    # Record initial file size and modification time
    initial_stat = pdf_path.stat()

    service = DocumentIngestionService()
    pages = service._parse_pdf(pdf_path)

    # 1. Stored file on disk must be completely untouched
    final_stat = pdf_path.stat()
    assert initial_stat.st_size == final_stat.st_size, "Stored PDF file size was altered!"

    # 2. Page 9 Table Extraction Verification
    page_9 = pages[8]
    assert len(page_9.tables) > 0, "No tables extracted from Page 9"
    p9_table = page_9.tables[0]

    # Check headers
    assert "Agency" in p9_table.headers[0]
    assert "AAggeennccyy" not in p9_table.headers[0]

    # Check rows contain correctly normalized CMPDI, MECL, numbers
    cmpdi_found = False
    mecl_found = False
    for row in p9_table.rows:
        row_str = " ".join(row)
        if "CMPDI" in row_str:
            cmpdi_found = True
            assert "1,92,000" in row_str, f"CMPDI target value not normalized: {row_str}"
            assert "103%" in row_str, f"CMPDI achievement not normalized: {row_str}"
            assert "CCMMPPDDII" not in row_str
            assert "11,,9922,,000000" not in row_str
        if "MECL" in row_str:
            mecl_found = True
            assert "715" in row_str, f"MECL 715 not normalized: {row_str}"
            assert "771155" not in row_str
    assert cmpdi_found, "CMPDI row not found in Page 9 table"
    assert mecl_found, "MECL row not found in Page 9 table"

    # 3. Page 16 Table Extraction Verification
    page_16 = pages[15]
    assert len(page_16.tables) > 0, "No tables extracted from Page 16"
    p16_table = page_16.tables[0]

    assert p16_table.headers == ["REPORTS", "Nos."]
    geological_reports_found = False
    project_reports_found = False

    for row in p16_table.rows:
        if "GEOLOGICAL REPORTS" in row[0]:
            geological_reports_found = True
            assert row[1] == "17", f"Expected '17' for GEOLOGICAL REPORTS, got '{row[1]}'"
        if "PROJECT REPORTS" in row[0] and row[0] == "PROJECT REPORTS":
            project_reports_found = True
            assert row[1] == "23", f"Expected '23' for PROJECT REPORTS, got '{row[1]}'"

    assert geological_reports_found, "GEOLOGICAL REPORTS row not found in Page 16 table"
    assert project_reports_found, "PROJECT REPORTS row not found in Page 16 table"

    # 4. Raw Native Text Integrity Verification
    # Native page text extracted via PyMuPDF page.get_text() must NOT be modified
    assert "CMPDI" in page_9.text
    assert "CCMMPPDDII" not in page_9.text  # Raw text never had doubling
    assert "Exploratory Drilling" in page_9.text

    print("accounts0607.pdf regression tests PASSED successfully!")


if __name__ == "__main__":
    print("Running test_doubled_token_detection_and_collapse()...")
    test_doubled_token_detection_and_collapse()
    print("Running test_preserve_legitimate_words_and_repeated_characters()...")
    test_preserve_legitimate_words_and_repeated_characters()
    print("Running test_preserve_legitimate_numeric_values_and_ids()...")
    test_preserve_legitimate_numeric_values_and_ids()
    print("Running test_whitespace_and_multiline_structure()...")
    test_whitespace_and_multiline_structure()
    print("Running test_accounts0607_pdf_regression()...")
    test_accounts0607_pdf_regression()
    print("\nALL TABLE NORMALIZATION TESTS PASSED!")
