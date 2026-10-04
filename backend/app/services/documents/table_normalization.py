"""
Table Text Normalization Layer for PyMuPDF find_tables()
-------------------------------------------------------
Addresses character-doubling artifacts in PDF table cell and header extraction.

Root Cause:
Some source PDFs contain duplicated or overlapping text objects (used for faux-bolding,
shadowing, or legacy layout passes). While PyMuPDF's full-page get_text("text") engine
deduplicates overlapping text objects during layout analysis, find_tables().tables[].extract()
queries text glyphs within cell bounding boxes without deduplication, resulting in interleaved
duplicated characters (e.g., 'GGEEOOLLOOGGIICCAALL' instead of 'GEOLOGICAL').

Normalization Strategy:
1. Detect true character-doubling patterns where token[::2] == token[1::2].
2. Collapse doubled tokens by sampling every second character (token[::2]).
3. Preserve legitimate repeated characters (e.g., 'SUCCESS', 'COAL', 'COMMITTEE', 'BOOKKEEPER'),
   numeric values, IDs, and normal words.
4. Safely handle surrounding punctuation and multiline/inter-word whitespace.
5. Only apply to extracted table headers and cells—never altering the original stored file
   or native raw page text extraction.
"""

import re
from typing import List, Optional


def is_token_doubled(tok: str) -> bool:
    """
    Checks whether a string exhibits exact character doubling:
    The string must have an even length (>= 2) and satisfy tok[::2] == tok[1::2].
    """
    if len(tok) < 2 or len(tok) % 2 != 0:
        return False
    return tok[::2] == tok[1::2]


def collapse_token(tok: str) -> str:
    """
    Collapses a character-doubled token by taking every second character (tok[::2]).
    Safely inspects leading and trailing non-alphanumeric punctuation so that tokens
    like 'CCMMPPDDII:', 'GGoovvttss..', '((mmeettrree))', or 'BBEE|' collapse accurately.
    """
    if is_token_doubled(tok):
        return tok[::2]

    # Check if stripping leading/trailing punctuation reveals a doubled alphanumeric core
    m = re.match(r"^([^a-zA-Z0-9]*)(.*?)([^a-zA-Z0-9]*)$", tok)
    if m:
        pre, mid, post = m.groups()
        if mid and is_token_doubled(mid):
            collapsed_mid = mid[::2]
            collapsed_pre = pre[::2] if is_token_doubled(pre) else pre
            collapsed_post = post[::2] if is_token_doubled(post) else post
            return f"{collapsed_pre}{collapsed_mid}{collapsed_post}"

    return tok


def has_strong_doubling(text: str) -> bool:
    """
    Evaluates whether a text block contains definitive character-doubled patterns.
    Looks for alphabetic or formatted tokens of length >= 4 satisfying the doubling invariant.
    """
    if not text:
        return False
    for tok in text.split():
        if len(tok) >= 4 and is_token_doubled(tok):
            if any(c.isalpha() for c in tok) or any(c in ",.-/%()|:*" for c in tok):
                return True
        m = re.match(r"^([^a-zA-Z0-9]*)(.*?)([^a-zA-Z0-9]*)$", tok)
        if m:
            _, mid, _ = m.groups()
            if len(mid) >= 4 and is_token_doubled(mid) and any(c.isalpha() for c in mid):
                return True
    return False


def is_table_doubled(raw_rows: List[List[Optional[str]]]) -> bool:
    """
    Inspects all extracted cells across a table to determine if the table exhibits
    systematic character doubling from overlapping text objects.
    """
    if not raw_rows:
        return False
    full_text = " ".join(str(c) for r in raw_rows for c in r if c)
    return has_strong_doubling(full_text)


def normalize_table_text(text: Optional[str], table_is_doubled: Optional[bool] = None) -> str:
    """
    Normalizes extracted table header or cell text safely after PyMuPDF find_tables():
    - Preserves table structure and whitespace across lines.
    - Collapses doubled character patterns where text[::2] == text[1::2].
    - Preserves legitimate words (SUCCESS, COAL), numeric values, IDs, and normal text.
    """
    if not text:
        return ""

    if table_is_doubled is None:
        table_is_doubled = has_strong_doubling(text)

    lines = text.split("\n")
    norm_lines = []
    for line in lines:
        parts = re.split(r"(\s+)", line)
        norm_parts = []
        for p in parts:
            if not p or p.isspace():
                norm_parts.append(p)
                continue

            # In clean tables (not doubled), protect standalone pure digits and short abbreviations
            if not table_is_doubled:
                if p.isdigit() or (p.isalpha() and len(p) <= 2):
                    norm_parts.append(p)
                    continue

            norm_parts.append(collapse_token(p))
        norm_lines.append("".join(norm_parts))

    return "\n".join(norm_lines)
