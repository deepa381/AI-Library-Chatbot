"""
preprocess.py
=============
STEP 2 (normalize) + quality checks (ISBN validation, missing-value handling,
corrupted-record removal) described in the spec.
"""
import re
import unicodedata


def normalize_whitespace(s):
    if not s:
        return s
    return re.sub(r"\s+", " ", s).strip()


def normalize_name(name):
    """Normalize author/publisher names: trim, fix case artifacts, strip acc?"""
    if not name:
        return name
    name = normalize_whitespace(name)
    name = unicodedata.normalize("NFC", name)
    return name


def normalize_isbn(isbn):
    """Strip hyphens/spaces; return None if not a plausible ISBN length."""
    if not isbn:
        return None
    cleaned = re.sub(r"[^0-9Xx]", "", str(isbn))
    if len(cleaned) not in (10, 13):
        return None
    return cleaned.upper()


def valid_isbn13(isbn13):
    """Checksum validation for ISBN-13."""
    isbn13 = normalize_isbn(isbn13)
    if not isbn13 or len(isbn13) != 13 or not isbn13.isdigit():
        return False
    total = sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(isbn13[:12]))
    check = (10 - total % 10) % 10
    return check == int(isbn13[12])


def valid_isbn10(isbn10):
    """Checksum validation for ISBN-10 (supports 'X' check digit)."""
    isbn10 = normalize_isbn(isbn10)
    if not isbn10 or len(isbn10) != 10:
        return False
    total = 0
    for i, ch in enumerate(isbn10):
        if ch == "X" and i == 9:
            val = 10
        elif ch.isdigit():
            val = int(ch)
        else:
            return False
        total += (10 - i) * val
    return total % 11 == 0


def valid_pub_year(year, min_year=1450, max_year=2027):
    """1450 ~ Gutenberg press era; adjust as needed. Rejects garbage years."""
    try:
        y = int(year)
    except (TypeError, ValueError):
        return False
    return min_year <= y <= max_year


def isbn13_to_isbn10(isbn13):
    """Deterministically derive ISBN-10 from a valid 978-prefixed ISBN-13."""
    isbn13 = normalize_isbn(isbn13)
    if not isbn13 or not valid_isbn13(isbn13) or not isbn13.startswith("978"):
        return None
    core = isbn13[3:12]
    total = sum((10 - i) * int(d) for i, d in enumerate(core))
    check = (11 - total % 11) % 11
    check_char = "X" if check == 10 else str(check)
    return core + check_char


def isbn10_to_isbn13(isbn10):
    """Deterministically derive ISBN-13 from a valid ISBN-10 (978 prefix)."""
    isbn10 = normalize_isbn(isbn10)
    if not isbn10 or not valid_isbn10(isbn10):
        return None
    core = "978" + isbn10[:9]
    total = sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(core))
    check = (10 - total % 10) % 10
    return core + str(check)


def normalize_genre(genre):
    if not genre:
        return "Uncategorized"
    g = normalize_whitespace(genre).title()
    aliases = {
        "Scifi": "Science Fiction", "Sci-Fi": "Science Fiction",
        "Ya": "Young Adult", "Non Fiction": "Nonfiction", "Non-Fiction": "Nonfiction",
    }
    return aliases.get(g, g)


def normalize_language(lang_code):
    table = {"en": "English", "fr": "French", "es": "Spanish", "de": "German",
             "hi": "Hindi", "ta": "Tamil", "ja": "Japanese", "zh": "Chinese"}
    if not lang_code:
        return "en", "English"
    lang_code = lang_code.lower()[:2]
    return lang_code, table.get(lang_code, lang_code.title())


def clean_record(raw):
    """
    Apply normalization + quality checks to a single raw record.
    Returns the cleaned record, or None if the record is corrupted beyond use
    (no title, or no usable author).
    """
    if not raw.get("title"):
        return None  # corrupted: unusable without a title
    authors = [normalize_name(a) for a in (raw.get("authors") or []) if a]
    if not authors:
        return None  # corrupted: no author

    rec = dict(raw)
    rec["title"] = normalize_whitespace(raw["title"])
    rec["subtitle"] = normalize_whitespace(raw.get("subtitle")) if raw.get("subtitle") else None
    rec["authors"] = authors
    rec["publisher"] = normalize_name(raw.get("publisher"))
    rec["genre"] = normalize_genre(raw.get("genre"))
    isbn10 = normalize_isbn(raw.get("isbn_10"))
    isbn13 = normalize_isbn(raw.get("isbn_13"))
    isbn10_ok = bool(isbn10 and valid_isbn10(isbn10))
    isbn13_ok = bool(isbn13 and valid_isbn13(isbn13))
    if isbn13_ok and not isbn10_ok:
        isbn10 = isbn13_to_isbn10(isbn13) or None
        isbn10_ok = isbn10 is not None
    elif isbn10_ok and not isbn13_ok:
        isbn13 = isbn10_to_isbn13(isbn10) or None
        isbn13_ok = isbn13 is not None
    rec["isbn_10"] = isbn10 if isbn10_ok else None
    rec["isbn_13"] = isbn13 if isbn13_ok else None
    rec["_isbn_invalid"] = bool((raw.get("isbn_10") and not isbn10_ok) or
                                 (raw.get("isbn_13") and not isbn13_ok))

    # Missing-value handling: intelligent defaults instead of blank cells
    if not valid_pub_year(raw.get("pub_year")):
        rec["pub_year"] = None  # unknown, rather than a bad guess
    else:
        rec["pub_year"] = int(raw["pub_year"])

    rec["description"] = normalize_whitespace(raw.get("description")) or \
        f"{rec['title']} by {', '.join(authors)}."  # minimal safe fallback
    rec["subjects"] = sorted({normalize_whitespace(s) for s in (raw.get("subjects") or []) if s})
    rec["pages"] = raw.get("pages") if isinstance(raw.get("pages"), int) and raw.get("pages", 0) > 0 else None

    lang_code, lang_name = normalize_language(raw.get("language"))
    rec["language_code"], rec["language_name"] = lang_code, lang_name

    return rec


def preprocess_all(raw_records):
    cleaned, dropped, isbn_flagged = [], 0, 0
    for r in raw_records:
        c = clean_record(r)
        if c is None:
            dropped += 1
            continue
        if c.pop("_isbn_invalid", False):
            isbn_flagged += 1
        cleaned.append(c)
    return cleaned, dropped, isbn_flagged
