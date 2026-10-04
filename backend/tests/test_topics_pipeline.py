"""
Topic Intelligence Test Suite
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Tests:
1. GET /api/topics/summary — All documents
2. GET /api/topics/summary — Document-scoped
3. GET /api/topics/word-cloud — All documents
4. GET /api/topics/word-cloud — Document-scoped
5. GET /api/topics/documents/{id} — Valid document
6. GET /api/topics/documents/{id} — Invalid document (404)
7. Topic extraction: keyword presence verification
8. Topic cluster matching: geological domains present
9. Empty text safety (unit test)
10. Deterministic output (same call = same result)
11. Keyword structure validation
12. Word cloud weight normalization
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.services.topics.service import (
    TopicIntelligenceService,
    normalize_token,
    STOPWORDS,
    VALID_SHORT_DOMAIN_TOKENS,
    GENERIC_ADMIN_TERMS,
    CORE_DOMAIN_TERMS,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Summary — All Documents
# ---------------------------------------------------------------------------
def test_topics_summary_all_documents():
    """GET /api/topics/summary should return valid structure for all docs."""
    print("\n--- Test 1: Topics Summary (All Documents) ---")
    res = client.get("/api/topics/summary")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()

    # Required fields
    assert "total_documents_analyzed" in data
    assert "total_topics_detected" in data
    assert "total_keywords_extracted" in data
    assert "topics" in data
    assert "top_keywords" in data
    assert "word_cloud" in data
    assert data["scope"] == "all"

    # Should have actual content from existing documents
    assert data["total_documents_analyzed"] >= 1, "Expected at least 1 document"
    print(f"  Documents analyzed: {data['total_documents_analyzed']}")
    print(f"  Topics detected: {data['total_topics_detected']}")
    print(f"  Keywords extracted: {data['total_keywords_extracted']}")


# ---------------------------------------------------------------------------
# 2. Summary — Document-Scoped with non-existent ID (graceful empty)
# ---------------------------------------------------------------------------
def test_topics_summary_invalid_document_id():
    """GET /api/topics/summary?document_id=nonexistent should return empty gracefully."""
    print("\n--- Test 2: Topics Summary (Invalid Document ID) ---")
    res = client.get("/api/topics/summary", params={"document_id": "00000000-0000-0000-0000-000000000000"})
    assert res.status_code == 200
    data = res.json()
    assert data["total_documents_analyzed"] == 0
    print("  Correctly returned empty result for non-existent document")


# ---------------------------------------------------------------------------
# 3. Word Cloud — All Documents
# ---------------------------------------------------------------------------
def test_word_cloud_all_documents():
    """GET /api/topics/word-cloud should return a list of word cloud items."""
    print("\n--- Test 3: Word Cloud (All Documents) ---")
    res = client.get("/api/topics/word-cloud")
    assert res.status_code == 200
    data = res.json()

    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "text" in item
        assert "value" in item
        assert "count" in item
        assert item["value"] >= 1.0
        assert item["value"] <= 100.0
        assert item["count"] >= 1
    print(f"  Word cloud items: {len(data)}")
    if data:
        print(f"  Top word: '{data[0]['text']}' (value={data[0]['value']}, count={data[0]['count']})")


# ---------------------------------------------------------------------------
# 4. Word Cloud Weight Normalization
# ---------------------------------------------------------------------------
def test_word_cloud_weight_range():
    """Word cloud values must all be within [1, 100]."""
    print("\n--- Test 4: Word Cloud Weight Normalization ---")
    res = client.get("/api/topics/word-cloud")
    assert res.status_code == 200
    data = res.json()

    for item in data:
        assert 1.0 <= item["value"] <= 100.0, (
            f"Word cloud value out of range: {item['text']} = {item['value']}"
        )
    print(f"  All {len(data)} word cloud items within [1, 100] range")


# ---------------------------------------------------------------------------
# 5. Document-Specific Topics (uses first real document from DB)
# ---------------------------------------------------------------------------
def test_document_specific_topics():
    """GET /api/topics/documents/{id} for a real document."""
    print("\n--- Test 5: Document-Specific Topics ---")
    # Get list of documents first
    docs_res = client.get("/api/documents")
    if docs_res.status_code != 200 or not docs_res.json():
        print("  No documents available — skipping document-specific test")
        return

    docs = docs_res.json()
    # Use first document
    doc_id = docs[0]["id"]
    doc_filename = docs[0]["filename"]

    res = client.get(f"/api/topics/documents/{doc_id}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()

    assert data["document_id"] == doc_id
    assert data["document_filename"] == doc_filename
    assert "topics" in data
    assert "top_keywords" in data
    assert "word_cloud" in data
    assert isinstance(data["total_topics_detected"], int)
    assert isinstance(data["total_keywords_extracted"], int)
    print(f"  Document: {doc_filename}")
    print(f"  Topics: {data['total_topics_detected']}, Keywords: {data['total_keywords_extracted']}")


# ---------------------------------------------------------------------------
# 6. 404 for Invalid Document ID
# ---------------------------------------------------------------------------
def test_document_topics_404():
    """GET /api/topics/documents/{non_existent_id} should return 404."""
    print("\n--- Test 6: Document Topics 404 ---")
    res = client.get("/api/topics/documents/non-existent-id-12345")
    assert res.status_code == 404
    print("  Correctly returned 404 for non-existent document ID")


# ---------------------------------------------------------------------------
# 7. Keyword Structure Validation
# ---------------------------------------------------------------------------
def test_keyword_structure():
    """Keywords should have word, count, relevance, documents fields."""
    print("\n--- Test 7: Keyword Structure ---")
    res = client.get("/api/topics/summary")
    assert res.status_code == 200
    data = res.json()

    for kw in data["top_keywords"]:
        assert "word" in kw, "Missing 'word' field"
        assert "count" in kw, "Missing 'count' field"
        assert "relevance" in kw, "Missing 'relevance' field"
        assert "documents" in kw, "Missing 'documents' field"
        assert 0.0 <= kw["relevance"] <= 1.0, f"Relevance {kw['relevance']} out of range"
        assert kw["count"] >= 1, f"Count {kw['count']} must be >= 1"
        assert isinstance(kw["documents"], list), "Documents must be a list"

    print(f"  All {len(data['top_keywords'])} keyword items have valid structure")


# ---------------------------------------------------------------------------
# 8. Topic Structure Validation
# ---------------------------------------------------------------------------
def test_topic_structure():
    """Topics should have name, score, keywords, document_count fields."""
    print("\n--- Test 8: Topic Structure ---")
    res = client.get("/api/topics/summary")
    assert res.status_code == 200
    data = res.json()

    for topic in data["topics"]:
        assert "name" in topic
        assert "score" in topic
        assert "keywords" in topic
        assert "document_count" in topic
        assert "document_names" in topic
        assert 0.0 <= topic["score"] <= 1.0, f"Score {topic['score']} out of range"
        assert isinstance(topic["keywords"], list)
        assert isinstance(topic["document_names"], list)

    print(f"  All {len(data['topics'])} topic items have valid structure")


# ---------------------------------------------------------------------------
# 9. Mining Domain Keywords in Results
# ---------------------------------------------------------------------------
def test_mining_domain_keywords_present():
    """
    Real mining documents should produce domain-relevant keywords.
    This validates the feature works with real data — NOT hardcoded.
    """
    print("\n--- Test 9: Mining Domain Keywords Present ---")
    res = client.get("/api/topics/summary")
    assert res.status_code == 200
    data = res.json()

    if data["total_keywords_extracted"] == 0:
        print("  No keywords extracted (no processed documents available)")
        return

    extracted_words = {kw["word"].lower() for kw in data["top_keywords"]}
    print(f"  Extracted top words: {sorted(list(extracted_words))[:20]}")

    # At least some domain terms should appear if real docs are processed
    mining_terms = {"coal", "mine", "drilling", "seam", "borehole", "reserves",
                    "production", "mining", "geological", "exploration", "ccl",
                    "cmpdi", "subsidiary", "report", "accounts"}
    found = mining_terms.intersection(extracted_words)
    print(f"  Domain terms found in top keywords: {found}")
    # Only assert if there are enough documents; otherwise just informational
    if data["total_documents_analyzed"] >= 1 and data["total_keywords_extracted"] >= 10:
        assert len(found) >= 2, (
            f"Expected at least 2 mining domain terms in keywords, found: {found}"
        )


# ---------------------------------------------------------------------------
# 10. Deterministic Output
# ---------------------------------------------------------------------------
def test_deterministic_output():
    """Two calls with same parameters should return identical results."""
    print("\n--- Test 10: Deterministic Output ---")
    res1 = client.get("/api/topics/summary")
    res2 = client.get("/api/topics/summary")
    assert res1.status_code == 200
    assert res2.status_code == 200

    data1 = res1.json()
    data2 = res2.json()

    assert data1["total_keywords_extracted"] == data2["total_keywords_extracted"]
    assert data1["total_topics_detected"] == data2["total_topics_detected"]
    assert data1["top_topic"] == data2["top_topic"]

    if data1["top_keywords"]:
        assert data1["top_keywords"][0]["word"] == data2["top_keywords"][0]["word"]
        assert data1["top_keywords"][0]["count"] == data2["top_keywords"][0]["count"]

    print("  Deterministic: both calls returned identical top keyword and topic counts")


# ---------------------------------------------------------------------------
# 11. Empty Text Safety (Unit Test)
# ---------------------------------------------------------------------------
def test_empty_text_safety():
    """Service should handle empty text without raising exceptions."""
    print("\n--- Test 11: Empty Text Safety (Unit Test) ---")
    service = TopicIntelligenceService()

    # Clean empty text
    cleaned = service._clean_text("")
    assert cleaned == "", f"Expected empty string, got: '{cleaned}'"

    # Extract tokens from empty text
    tokens = service._extract_tokens("")
    assert tokens == [], f"Expected empty token list, got: {tokens}"

    # Compute keywords with empty doc dict
    keywords = service._compute_keywords({})
    assert keywords == [], f"Expected empty keywords, got: {keywords}"

    # Build word cloud from empty keywords
    cloud = service._build_word_cloud([])
    assert cloud == [], f"Expected empty word cloud, got: {cloud}"

    print("  All empty text edge cases handled safely")


# ---------------------------------------------------------------------------
# 12. Relevance Score Ordering
# ---------------------------------------------------------------------------
def test_keywords_sorted_by_relevance():
    """Keywords should be sorted by relevance descending."""
    print("\n--- Test 12: Keywords Sorted by Relevance ---")
    res = client.get("/api/topics/summary")
    assert res.status_code == 200
    data = res.json()

    keywords = data["top_keywords"]
    if len(keywords) >= 2:
        for i in range(len(keywords) - 1):
            assert keywords[i]["relevance"] >= keywords[i + 1]["relevance"], (
                f"Keywords not sorted: '{keywords[i]['word']}' ({keywords[i]['relevance']}) "
                f"< '{keywords[i+1]['word']}' ({keywords[i+1]['relevance']})"
            )
    print(f"  Keywords correctly sorted by relevance (checked {len(keywords)} items)")


# ---------------------------------------------------------------------------
# 13. Zero Duplicate Keywords within Topics
# ---------------------------------------------------------------------------
def test_no_duplicate_keywords_within_any_topic():
    """Every topic must have unique keywords — zero duplicate tokens (e.g. 'seam, coal', not 'seam, seam, coal')."""
    print("\n--- Test 13: Zero Duplicate Keywords Within Any Topic ---")
    res = client.get("/api/topics/summary")
    assert res.status_code == 200
    data = res.json()

    for topic in data["topics"]:
        kws = topic["keywords"]
        assert len(kws) == len(set(kws)), (
            f"Topic '{topic['name']}' has duplicate keywords: {kws}"
        )
        # Check specifically for known former duplicate culprits
        assert kws.count("seam") <= 1, f"Duplicate 'seam' in {topic['name']}"
        assert kws.count("mine") <= 1, f"Duplicate 'mine' in {topic['name']}"
        assert kws.count("drilling") <= 1, f"Duplicate 'drilling' in {topic['name']}"

    print(f"  All {len(data['topics'])} topics verified: 0 duplicate keywords")


# ---------------------------------------------------------------------------
# 14. Noisy Token & OCR Fragment Filtering
# ---------------------------------------------------------------------------
def test_noisy_token_filtering():
    """OCR artifacts, meaningless fragments ('off', Roman numerals, engine text) must be filtered."""
    print("\n--- Test 14: Noisy Token & OCR Fragment Filtering ---")
    res = client.get("/api/topics/summary")
    assert res.status_code == 200
    data = res.json()

    top_words = {kw["word"].lower() for kw in data["top_keywords"]}

    # Obvious noise words that must NEVER appear in top keywords
    prohibited_noise = {
        "off", "vii", "iii", "viii", "iv", "tesseract", "installed",
        "engine", "found", "system", "use", "seen", "done", "sn", "sl"
    }
    found_noise = prohibited_noise.intersection(top_words)
    assert not found_noise, f"Noise tokens found in top keywords: {found_noise}"

    # Also verify that no topic contains 'off' or OCR fragments
    for topic in data["topics"]:
        for kw in topic["keywords"]:
            assert kw not in prohibited_noise, (
                f"Prohibited noise word '{kw}' found in topic '{topic['name']}'"
            )

    print("  Verified: No OCR fragments or meaningless noise tokens present in keywords")


# ---------------------------------------------------------------------------
# 15. Mining Domain Terms Preserved & Administrative Words Down-Ranked
# ---------------------------------------------------------------------------
def test_mining_terms_preserved_and_admin_downranked():
    """Legitimate mining terminology must remain prominent; generic administrative words down-ranked."""
    print("\n--- Test 15: Mining Domain Terms Preserved & Admin Words Down-Ranked ---")
    res = client.get("/api/topics/summary")
    assert res.status_code == 200
    data = res.json()

    top_20 = [kw["word"].lower() for kw in data["top_keywords"][:20]]
    print(f"  Top 20 extracted keywords: {top_20}")

    # Core mining domain terms should be present in top keywords
    expected_domain = {"coal", "mine", "drilling", "project", "cmpdi"}
    present_domain = expected_domain.intersection(set(top_20))
    assert len(present_domain) >= 3, (
        f"Expected at least 3 of {expected_domain} in top 20 keywords, got: {present_domain}"
    )

    # Check that generic admin terms (like 'comment', 'march', 'audit') are not outranking 'coal' or 'mine'
    kw_relevance = {kw["word"].lower(): kw["relevance"] for kw in data["top_keywords"]}
    coal_rel = kw_relevance.get("coal", 0.0)
    mine_rel = kw_relevance.get("mine", 0.0)

    # Coal or mine must have high relevance (>= 0.70)
    assert coal_rel >= 0.70 or mine_rel >= 0.70, (
        f"Expected coal ({coal_rel}) or mine ({mine_rel}) to have high relevance >= 0.70"
    )

    print(f"  Domain prominence verified: coal={coal_rel}, mine={mine_rel}")


# ---------------------------------------------------------------------------
# 16. Token Normalization Logic (Unit Test)
# ---------------------------------------------------------------------------
def test_token_normalization_logic():
    """Unit test for normalize_token verifying singularization and invariant protection."""
    print("\n--- Test 16: Token Normalization Logic (Unit Test) ---")

    # Regular plurals -> singular
    assert normalize_token("mines") == "mine"
    assert normalize_token("projects") == "project"
    assert normalize_token("reports") == "report"
    assert normalize_token("seams") == "seam"
    assert normalize_token("reserves") == "reserve"
    assert normalize_token("resources") == "resource"
    assert normalize_token("companies") == "company"
    assert normalize_token("subsidiaries") == "subsidiary"
    assert normalize_token("analyses") == "analysis"

    # Invariant terms (must not strip trailing 's' or alter gerund)
    assert normalize_token("thickness") == "thickness"
    assert normalize_token("gross") == "gross"
    assert normalize_token("loss") == "loss"
    assert normalize_token("process") == "process"
    assert normalize_token("gas") == "gas"
    assert normalize_token("drilling") == "drilling"
    assert normalize_token("mining") == "mining"
    assert normalize_token("logging") == "logging"
    assert normalize_token("stripping") == "stripping"
    assert normalize_token("planning") == "planning"

    print("  All normalization rules and invariant protections verified")

