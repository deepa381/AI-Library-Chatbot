"""
merge.py
========
STEP 3 (dedupe) + STEP 4 (merge) of the pipeline.

Dedup key priority (first match wins):
  1. ISBN-13
  2. ISBN-10
  3. Google Books ID
  4. Open Library ID
  5. normalized(title) + normalized(primary author)

When multiple raw records collapse to the same book, fields are merged with
a source-priority order so the richest/most reliable value wins per field
(e.g. Open Library for pages/subjects, Google Books for description/ratings).
"""
import re

SOURCE_PRIORITY = {"open_library": 1, "google_books": 2, "seed": 3}


def _title_author_key(rec):
    t = re.sub(r"[^a-z0-9]", "", (rec.get("title") or "").lower())
    a = re.sub(r"[^a-z0-9]", "", (rec.get("authors") or [""])[0].lower())
    return f"{t}::{a}"


def dedup_key(rec):
    if rec.get("isbn_13"):
        return f"isbn13:{rec['isbn_13']}"
    if rec.get("isbn_10"):
        return f"isbn10:{rec['isbn_10']}"
    if rec.get("google_books_id"):
        return f"gbid:{rec['google_books_id']}"
    if rec.get("open_library_id"):
        return f"olid:{rec['open_library_id']}"
    return f"ta:{_title_author_key(rec)}"


def merge_field(existing, new, field, prefer_longer=False):
    ev, nv = existing.get(field), new.get(field)
    if ev in (None, "", [], {}):
        return nv
    if nv in (None, "", [], {}):
        return ev
    if prefer_longer and isinstance(ev, str) and isinstance(nv, str):
        return nv if len(nv) > len(ev) else ev
    # otherwise: prefer the higher-priority source's value (already merged in order)
    return ev


def merge_records(records):
    """Group raw/cleaned records by dedup key and merge each group into one."""
    groups = {}
    for r in records:
        k = dedup_key(r)
        groups.setdefault(k, []).append(r)

    merged = []
    for key, group in groups.items():
        group.sort(key=lambda r: SOURCE_PRIORITY.get(r.get("source", "seed"), 99))
        base = dict(group[0])
        for other in group[1:]:
            for field in set(base.keys()) | set(other.keys()):
                prefer_longer = field in ("description",)
                base[field] = merge_field(base, other, field, prefer_longer)
            # union list-type fields instead of overwriting
            for listfield in ("subjects", "authors"):
                if listfield in base or listfield in other:
                    union = list({*(base.get(listfield) or []), *(other.get(listfield) or [])})
                    base[listfield] = sorted(union)
        base["_merged_from"] = [g.get("source") for g in group]
        merged.append(base)
    return merged
