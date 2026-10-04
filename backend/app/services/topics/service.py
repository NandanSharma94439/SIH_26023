"""
Topic Intelligence Service
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)

Analyzes processed geological and mining documents to identify:
1. High-relevance domain keywords using TF-IDF-inspired scoring
2. Thematic topics via keyword cluster co-occurrence (no heavy ML dependency)
3. Word cloud data for frontend visualization

Text is read from storage/processed/{doc_id}.json files that already exist.
No new processing pipeline is introduced.
"""

import re
import json
import math
from pathlib import Path
from typing import List, Optional, Dict, Set, Tuple
from collections import Counter

from app.core.config import settings
from app.services.documents.db import doc_db
from app.schemas.topics import (
    KeywordItem,
    TopicItem,
    WordCloudItem,
    TopicSummaryResponse,
    DocumentTopicResponse,
)


# ---------------------------------------------------------------------------
# Mining / Geological Domain Stopword List & Token Invariants
# Combines standard English stopwords, prepositions, OCR artifacts & generic noise
# ---------------------------------------------------------------------------
STOPWORDS: Set[str] = {
    # Standard English & prepositions
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "that", "this",
    "these", "those", "it", "its", "as", "not", "no", "nor", "so", "yet",
    "both", "either", "neither", "than", "such", "while", "since", "if",
    "then", "which", "who", "whom", "whose", "when", "where", "how", "why",
    "what", "all", "each", "every", "any", "few", "more", "most", "other",
    "some", "he", "she", "they", "we", "you", "i", "me", "him", "her",
    "them", "us", "my", "your", "his", "our", "their", "about", "above",
    "after", "before", "between", "into", "through", "during", "upon",
    "over", "under", "again", "further", "once", "here", "there", "out",
    "up", "very", "just", "also", "only", "same", "own", "too", "s", "t",
    "re", "ll", "ve", "d", "m", "because", "therefore", "hence", "off",
    "within", "without", "among", "against", "towards", "across",
    "throughout", "along", "behind", "beside", "below", "beneath",
    "underneath", "around", "via", "per", "non",

    # Document & OCR boilerplate noise
    "page", "report", "table", "figure", "annex", "annexure", "sl",
    "sr", "no", "number", "total", "sub", "item", "detail", "details",
    "description", "particulars", "statement", "note", "notes",
    "appendix", "section", "chapter", "part", "para", "paragraph",
    "ref", "reference", "see", "viz", "etc", "date", "year", "month",
    "day", "rs", "cr", "lakh", "lakhs", "amount", "nil", "zero",
    "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "sn", "nos", "vol",

    # Financial & Accounting boilerplate noise
    "account", "accounts", "balance", "sheet", "debit", "credit",
    "financial", "fund", "funds", "audit", "auditor", "auditors",

    # Generic organization terms
    "limited", "ltd", "pvt", "india", "indian", "government", "govt",
    "ministry", "department", "division", "office", "committee",
    "chairman", "director", "board", "company", "corporation",

    # Common OCR engine artifacts & fallback strings
    "ocr", "fallback", "text", "block", "extracted", "col", "row",
    "tesseract", "engine", "installed", "found", "system",

    # Roman numerals (section markers)
    "ii", "iii", "iv", "vi", "vii", "viii", "ix", "xi", "xii", "xiii", "xiv", "xv",

    # Generic high-frequency conversational verbs / noise
    "use", "used", "using", "seen", "make", "made", "making",
    "give", "given", "giving", "take", "taken", "taking", "come", "came",
    "done", "like", "well", "good", "need", "know", "much", "many",
    "even", "still", "last", "first", "second", "third", "next", "new",
    "old", "high", "low", "show", "shown", "showing", "find",
}

# Invariant domain words that should NOT have trailing 's' stripped
INVARIANT_WORDS: Set[str] = {
    "gas", "thickness", "gross", "loss", "process", "status", "basis",
    "axis", "series", "species", "strata", "stratum", "analysis",
    # Core gerunds / activity terms that should remain intact
    "drilling", "mining", "logging", "stripping", "planning", "parting",
    "sampling", "mapping", "washing", "blasting", "crushing", "coking",
}

# Valid 3-letter domain words/acronyms (other 3-letter tokens are filtered as noise)
VALID_SHORT_DOMAIN_TOKENS: Set[str] = {
    "ccl", "wcl", "ecl", "mcl", "ncl", "cil", "gcv", "ocp", "ash",
    "dip", "pit", "ore", "mty", "bcm", "gas", "mtp", "log", "core"
}

# Generic administrative / financial words to down-rank
GENERIC_ADMIN_TERMS: Set[str] = {
    "report", "work", "current", "previous", "information", "service",
    "management", "schedule", "asset", "tax", "march", "profit", "loss",
    "comment", "company", "cost", "development", "land", "audit", "auditor",
    "expenditure", "income", "provision", "general", "statement", "period",
    "review", "internal", "annual", "share", "capital", "liability",
    "depreciation", "interest", "dividend", "investment", "advance",
    "debtor", "creditor", "statutory", "financial", "particulars",
    "compliance", "administrative", "basis", "manner",
}

# Core mining and geological terminology (protected from down-ranking)
CORE_DOMAIN_TERMS: Set[str] = {
    "coal", "drilling", "borehole", "exploration", "seam", "geological",
    "reserve", "resource", "production", "mining", "survey", "feasibility",
    "lithology", "stratigraphy", "collar", "depth", "ash", "moisture",
    "calorific", "gcv", "mine", "opencast", "underground", "overburden",
    "stripping", "cmpdi", "ccl", "wcl", "ecl", "bccl", "secl", "mcl", "ncl",
    "cil", "tonne", "strata", "stratum", "formation", "core", "ocp", "mtpa",
    "interburden", "parting", "thickness", "grade", "mineable", "lignite",
    "sandstone", "shale", "siltstone", "clay", "fault", "syncline", "anticline",
    "strike", "dip", "coking",
}


def normalize_token(word: str) -> str:
    """
    Safely normalizes token without destroying meaningful terminology.
    - Preserves core gerund/process terms (drilling, mining, logging, etc.)
    - Preserves invariant nouns ending in ss, us, is
    - Normalizes regular English plurals (-ies -> -y, -sses/-shes/-ches/-xes -> stem, -s -> stem)
    """
    if len(word) <= 3 or word in INVARIANT_WORDS:
        return word
    if word == "analyses":
        return "analysis"
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("sses", "shes", "ches", "xes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith(("us", "is", "ss")):
        return word[:-1]
    return word


# Domain-significant multi-word bigrams to detect as single compound tokens
DOMAIN_BIGRAMS: List[Tuple[str, str]] = [
    ("coal", "seam"), ("coal", "india"), ("coal", "reserve"),
    ("borehole", "log"), ("borehole", "data"), ("geological", "survey"),
    ("exploratory", "drilling"), ("mine", "planning"), ("mine", "project"),
    ("open", "cast"), ("opencast", "mine"), ("coal", "grade"),
    ("coal", "quality"), ("seam", "thickness"), ("stripping", "ratio"),
    ("life", "mine"), ("drift", "mine"), ("underground", "mine"),
    ("coal", "block"), ("feasibility", "report"), ("geological", "report"),
    ("coal", "resource"), ("coal", "reserve"), ("proximate", "analysis"),
    ("calorific", "value"), ("gross", "calorific"), ("ash", "content"),
    ("volatile", "matter"), ("fixed", "carbon"), ("moisture", "content"),
    ("geophysical", "logging"), ("core", "sample"), ("coal", "field"),
    ("gondwana", "coalfield"), ("jharia", "coalfield"), ("north", "karanpura"),
    ("singrauli", "coalfield"), ("talcher", "coalfield"),
    ("subsidiary", "company"), ("coal", "production"), ("target", "achievement"),
]

# Predefined topic clusters — normalized keywords that define each topic domain
TOPIC_CLUSTERS: Dict[str, List[str]] = {
    "Geological Exploration & Drilling": [
        "borehole", "drilling", "exploratory", "depth", "collar", "geophysical",
        "logging", "core", "stratigraphy", "lithology", "formation", "strata",
        "geological", "survey", "exploration", "drill",
    ],
    "Coal Seam Stratigraphy": [
        "seam", "thickness", "coal", "stratum", "dip", "strike",
        "interburden", "parting", "band", "roof", "floor",
    ],
    "Coal Resources & Reserves": [
        "resource", "reserve", "proved", "indicated", "inferred", "billion",
        "tonne", "million", "mt", "bt", "additional", "category", "classified",
    ],
    "Proximate & Coal Quality Analysis": [
        "ash", "moisture", "volatile", "carbon", "calorific", "gcv", "grade",
        "proximate", "analysis", "quality", "laboratory", "fixed",
    ],
    "Mine Planning & Feasibility": [
        "mine", "project", "planning", "feasibility", "production", "capacity",
        "mtpa", "opencast", "underground", "overburden", "stripping",
        "extraction", "mineable", "mining",
    ],
    "Mining Operations & Production": [
        "production", "target", "achievement", "operational", "output",
        "despatch", "equipment", "machinery", "operation",
    ],
    "Subsidiary & Corporate Structure": [
        "cmpdi", "ccl", "wcl", "ecl", "bccl", "secl", "mcl", "ncl",
        "subsidiary", "coalfield", "headquarter", "ranchi", "nagpur",
    ],
    "Borehole & Structural Geology": [
        "fault", "syncline", "anticline", "structural", "tectonic", "basin",
        "gondwana", "displacement",
    ],
}


class TopicIntelligenceService:
    """
    Extracts keywords and identifies topics from processed geological documents.

    Data Source: storage/processed/{doc_id}.json files (already ingested pages).
    Method: TF-IDF-inspired keyword scoring + domain cluster classification.
    Dependencies: Python stdlib only — zero external heavy ML dependencies.
    """

    def __init__(self):
        self.processed_dir: Path = settings.PROCESSED_DIRECTORY

    def _load_document_text(self, doc_id: str) -> Tuple[str, str]:
        """
        Load all page text from a processed document JSON.
        Returns (full_text, filename).
        """
        processed_file = self.processed_dir / f"{doc_id}.json"
        if not processed_file.exists():
            return "", ""
        try:
            data = json.loads(processed_file.read_text(encoding="utf-8"))
            filename = data.get("metadata", {}).get("filename", doc_id)
            pages = data.get("pages", [])
            text_parts = []
            for page in pages:
                t = page.get("text", "")
                if t:
                    text_parts.append(t)
            return "\n".join(text_parts), filename
        except Exception:
            return "", ""

    def _clean_text(self, raw_text: str) -> str:
        """
        Clean OCR text for keyword analysis.
        - Remove OCR fallback markers and error messages
        - Remove URLs, emails, and non-alphanumeric noise sequences
        - Remove purely numeric tokens and isolated characters
        - Normalize whitespace and lowercase
        """
        text = raw_text

        # Remove OCR fallback and error markers
        text = re.sub(r"\[OCR Fallback Text\]:?", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"\[Error during parsing[^\]]*\]", " ", text)

        # Remove URLs and emails
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"\S+@\S+", " ", text)

        # Remove sequences of special characters (OCR noise)
        text = re.sub(r"[^\w\s\-\/.]", " ", text)

        # Remove pure numbers and isolated digits
        text = re.sub(r"\b\d+\.?\d*\b", " ", text)
        text = re.sub(r"\b[a-zA-Z]\b", " ", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()

    def _extract_tokens(self, cleaned_text: str) -> List[str]:
        """
        Tokenize cleaned text into meaningful, normalized words.
        Filters stopwords, OCR noise, and short non-domain tokens.
        """
        raw_tokens = re.findall(r"\b[a-z]{3,}\b", cleaned_text)
        tokens: List[str] = []
        for raw in raw_tokens:
            if raw in STOPWORDS:
                continue
            norm = normalize_token(raw)
            if norm in STOPWORDS:
                continue
            # If 3 chars, ensure it is a recognized domain abbreviation/word
            if len(norm) == 3 and norm not in VALID_SHORT_DOMAIN_TOKENS:
                continue
            tokens.append(norm)
        return tokens

    def _extract_bigrams(self, tokens: List[str]) -> List[str]:
        """
        Detect and append domain-significant bigrams as compound tokens.
        """
        bigrams = []
        for i in range(len(tokens) - 1):
            pair = (tokens[i], tokens[i + 1])
            if pair in DOMAIN_BIGRAMS:
                bigrams.append(f"{pair[0]}_{pair[1]}")
        return bigrams

    def _compute_keywords(
        self,
        doc_texts: Dict[str, Tuple[str, str]],  # {doc_id: (full_text, filename)}
        target_doc_id: Optional[str] = None,
    ) -> List[KeywordItem]:
        """
        Compute TF-IDF-inspired keyword scores across the corpus or a single document.

        TF: Term frequency within target scope (all docs or one doc)
        IDF: log(N / df) where N=total docs, df=number of docs containing term
        Score is down-ranked for generic admin words and normalized to 0-1.
        """
        N = len(doc_texts)
        if N == 0:
            return []

        # Build per-document token lists
        per_doc_tokens: Dict[str, List[str]] = {}
        per_doc_filename: Dict[str, str] = {}

        for doc_id, (raw_text, filename) in doc_texts.items():
            cleaned = self._clean_text(raw_text)
            tokens = self._extract_tokens(cleaned)
            bigrams = self._extract_bigrams(tokens)
            per_doc_tokens[doc_id] = tokens + bigrams
            per_doc_filename[doc_id] = filename

        # Target scope
        if target_doc_id and target_doc_id in per_doc_tokens:
            scope_tokens = per_doc_tokens[target_doc_id]
        else:
            scope_tokens = []
            for toks in per_doc_tokens.values():
                scope_tokens.extend(toks)

        if not scope_tokens:
            return []

        # Term frequency in scope
        tf_counter = Counter(scope_tokens)
        total_tokens = len(scope_tokens)

        # Document frequency across ALL docs (for IDF)
        df_counter: Counter = Counter()
        for doc_id, toks in per_doc_tokens.items():
            doc_vocab = set(toks)
            for word in doc_vocab:
                df_counter[word] += 1

        # Build document membership map (which filenames have this keyword)
        word_doc_map: Dict[str, List[str]] = {}
        for doc_id, toks in per_doc_tokens.items():
            doc_vocab = set(toks)
            fname = per_doc_filename[doc_id]
            for word in doc_vocab:
                if word not in word_doc_map:
                    word_doc_map[word] = []
                if fname not in word_doc_map[word]:
                    word_doc_map[word].append(fname)

        # Compute TF-IDF scores with admin down-ranking
        scores: Dict[str, float] = {}
        for word, count in tf_counter.items():
            tf = count / total_tokens
            df = df_counter.get(word, 1)
            idf = math.log((N + 1) / (df + 1)) + 1  # smoothed IDF
            raw_score = tf * idf

            # Down-rank generic administrative/reporting words (only when not a core mining term)
            if word in GENERIC_ADMIN_TERMS and word not in CORE_DOMAIN_TERMS:
                raw_score *= 0.25

            scores[word] = raw_score

        # Normalize to 0-1
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                scores = {w: round(s / max_score, 4) for w, s in scores.items()}

        # Build keyword items sorted deterministically by relevance descending, then word
        keywords = []
        min_count = 1 if (target_doc_id is not None or total_tokens < 100) else 2
        for word, relevance in sorted(scores.items(), key=lambda x: (-x[1], x[0])):
            count = tf_counter[word]
            if count < min_count:
                continue
            keywords.append(
                KeywordItem(
                    word=word.replace("_", " "),
                    count=count,
                    relevance=relevance,
                    documents=sorted(word_doc_map.get(word, [])),
                )
            )

        return keywords[:100]  # Return top-100 keywords

    def _identify_topics(
        self,
        keywords: List[KeywordItem],
        per_doc_filename: Dict[str, str],
        doc_texts: Dict[str, Tuple[str, str]],
    ) -> List[TopicItem]:
        """
        Match extracted keywords against domain topic clusters.
        - Guarantees zero duplicate keywords within any topic
        - Prevents prefix/substring false matches (e.g. 'off' matching 'offtake')
        - Scores each topic proportionally and tracks contributing source documents
        """
        keyword_map = {kw.word.replace(" ", "_"): kw for kw in keywords}
        for kw in keywords:
            keyword_map[kw.word] = kw

        topics = []

        for topic_name, cluster_words in TOPIC_CLUSTERS.items():
            matched_keywords: List[str] = []
            seen_topic_kws: Set[str] = set()
            topic_score = 0.0
            topic_docs: Set[str] = set()

            for word in cluster_words:
                norm_word = normalize_token(word)
                kw = keyword_map.get(norm_word) or keyword_map.get(word)

                if kw is not None and kw.word not in seen_topic_kws:
                    seen_topic_kws.add(kw.word)
                    matched_keywords.append(kw.word)
                    topic_score += kw.relevance
                    topic_docs.update(kw.documents)

            if matched_keywords:
                # Normalize: max possible score = len(cluster_words) * 1.0
                normalized_score = min(round(topic_score / len(cluster_words), 4), 1.0)
                topics.append(
                    TopicItem(
                        name=topic_name,
                        score=normalized_score,
                        keywords=matched_keywords[:8],
                        document_count=len(topic_docs),
                        document_names=sorted(topic_docs),
                    )
                )

        # Sort deterministically by score descending, then topic name
        topics.sort(key=lambda t: (-t.score, t.name))
        return topics

    def _build_word_cloud(self, keywords: List[KeywordItem]) -> List[WordCloudItem]:
        """
        Convert keyword list to word cloud items with normalized display weights (1-100).
        """
        if not keywords:
            return []

        top = keywords[:60]  # Top 60 for word cloud
        max_count = max(k.count for k in top) if top else 1
        min_count = min(k.count for k in top) if top else 1
        count_range = max(max_count - min_count, 1)

        cloud = []
        for kw in top:
            # Map count to 10-100 range for visual weight
            normalized = 10 + 90 * (kw.count - min_count) / count_range
            cloud.append(
                WordCloudItem(
                    text=kw.word,
                    value=round(normalized, 1),
                    count=kw.count,
                )
            )
        return cloud

    def get_summary(self, document_id: Optional[str] = None) -> TopicSummaryResponse:
        """
        Compute Topic Intelligence summary for all documents or one specific document.
        """
        all_docs = doc_db.list_documents()
        processed_docs = [d for d in all_docs if d.status == "processed"]

        if not processed_docs:
            return TopicSummaryResponse(
                total_documents_analyzed=0,
                total_topics_detected=0,
                total_keywords_extracted=0,
                scope="all",
            )

        # Determine scope
        if document_id:
            target_docs = [d for d in processed_docs if d.id == document_id]
            scope = document_id
        else:
            target_docs = processed_docs
            scope = "all"

        if not target_docs:
            return TopicSummaryResponse(
                total_documents_analyzed=0,
                total_topics_detected=0,
                total_keywords_extracted=0,
                scope=scope,
            )

        # Load text for all docs (needed for IDF calculation even when scoping to one)
        doc_texts: Dict[str, Tuple[str, str]] = {}
        for doc in processed_docs:
            text, filename = self._load_document_text(doc.id)
            if text.strip():
                doc_texts[doc.id] = (text, filename)

        # Compute keywords
        target_doc_id = target_docs[0].id if document_id else None
        keywords = self._compute_keywords(doc_texts, target_doc_id)

        per_doc_filename = {doc_id: tup[1] for doc_id, tup in doc_texts.items()}

        # Identify topics
        topics = self._identify_topics(keywords, per_doc_filename, doc_texts)

        # Build word cloud
        word_cloud = self._build_word_cloud(keywords)

        top_topic = topics[0].name if topics else None
        top_keyword = keywords[0].word if keywords else None

        analyzed_count = len(target_docs) if document_id else len(doc_texts)

        return TopicSummaryResponse(
            total_documents_analyzed=analyzed_count,
            total_topics_detected=len(topics),
            total_keywords_extracted=len(keywords),
            top_topic=top_topic,
            top_keyword=top_keyword,
            topics=topics,
            top_keywords=keywords[:50],
            word_cloud=word_cloud,
            scope=scope,
        )

    def get_document_topics(self, doc_id: str) -> Optional[DocumentTopicResponse]:
        """
        Compute Topic Intelligence for a specific document.
        Returns None if the document is not found.
        """
        doc_record = doc_db.get_document(doc_id)
        if not doc_record:
            return None

        metadata = doc_record["metadata"]
        filename = metadata.filename

        # Load text for all docs (for IDF denominator)
        all_docs = doc_db.list_documents()
        doc_texts: Dict[str, Tuple[str, str]] = {}
        for doc in all_docs:
            if doc.status == "processed":
                text, fname = self._load_document_text(doc.id)
                if text.strip():
                    doc_texts[doc.id] = (text, fname)

        if doc_id not in doc_texts:
            return DocumentTopicResponse(
                document_id=doc_id,
                document_filename=filename,
                topics=[],
                top_keywords=[],
                word_cloud=[],
                total_topics_detected=0,
                total_keywords_extracted=0,
            )

        keywords = self._compute_keywords(doc_texts, doc_id)
        per_doc_filename = {d: t[1] for d, t in doc_texts.items()}
        topics = self._identify_topics(keywords, per_doc_filename, doc_texts)
        word_cloud = self._build_word_cloud(keywords)

        return DocumentTopicResponse(
            document_id=doc_id,
            document_filename=filename,
            topics=topics,
            top_keywords=keywords[:50],
            word_cloud=word_cloud,
            total_topics_detected=len(topics),
            total_keywords_extracted=len(keywords),
        )

    def get_word_cloud_data(
        self, document_id: Optional[str] = None
    ) -> List[WordCloudItem]:
        """Fetch word cloud data for all docs or a specific document."""
        summary = self.get_summary(document_id=document_id)
        return summary.word_cloud


topic_intelligence_service = TopicIntelligenceService()
