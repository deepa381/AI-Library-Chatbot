"""
download.py
============
Responsible for STEP 1 of the pipeline: acquiring raw book records.

Two modes:
  1. LIVE MODE (requires internet + `requests`): pulls real metadata from the
     Google Books API and Open Library Books API for a list of ISBNs, or by
     free-text/genre search. Use this in your real deployment environment.
  2. SEED MODE (no internet required): loads data/seed_books.py, a curated
     sample of 48 real, well-known books, for pipeline testing/demos.

Both modes emit the SAME raw record shape so preprocess.py / merge.py /
enrichment.py never need to know which source produced a record.
"""
import json
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.config import GOOGLE_BOOKS_API, OPEN_LIBRARY_BOOKS_API, RAW_DIR


def load_seed():
    """SEED MODE — load the curated real-book sample (no network required)."""
    from data.seed_books import SEED_BOOKS
    records = []
    for b in SEED_BOOKS:
        records.append({
            "source": "seed",
            "title": b["title"],
            "subtitle": b.get("subtitle"),
            "authors": b["authors"],
            "isbn_10": b.get("isbn10"),
            "isbn_13": b.get("isbn13"),
            "publisher": b.get("publisher"),
            "pub_year": b.get("pub_year"),
            "language": b.get("language", "en"),
            "pages": b.get("pages"),
            "genre": b.get("genre"),
            "subgenre": b.get("subgenre"),
            "description": b.get("description"),
            "subjects": b.get("subjects", []),
            "historical_period": b.get("historical_period"),
            "country_setting": b.get("country_setting"),
            "time_setting": b.get("time_setting"),
            "avg_rating": b.get("avg_rating"),
            "rating_count": b.get("rating_count"),
            "open_library_id": None,
            "google_books_id": None,
        })
    return records


def fetch_google_books(isbn, api_key=None, session=None, retries=3, backoff=2.0):
    """LIVE MODE — query Google Books by ISBN. Returns a normalized dict or None."""
    import requests
    session = session or requests.Session()
    params = {"q": f"isbn:{isbn}"}
    if api_key:
        params["key"] = api_key
    for attempt in range(retries):
        resp = session.get(GOOGLE_BOOKS_API, params=params, timeout=15)
        if resp.status_code == 429:
            time.sleep(backoff * (attempt + 1))
            continue
        resp.raise_for_status()
        data = resp.json()
        if not data.get("items"):
            return None
        item = data["items"][0]
        info = item.get("volumeInfo", {})
        return {
            "source": "google_books",
            "google_books_id": item.get("id"),
            "title": info.get("title"),
            "subtitle": info.get("subtitle"),
            "authors": info.get("authors", []),
            "publisher": info.get("publisher"),
            "pub_year": (info.get("publishedDate") or "")[:4] or None,
            "language": info.get("language"),
            "pages": info.get("pageCount"),
            "description": info.get("description"),
            "subjects": info.get("categories", []),
            "avg_rating": info.get("averageRating"),
            "rating_count": info.get("ratingsCount"),
            "thumbnail_url": info.get("imageLinks", {}).get("thumbnail"),
            "preview_link": info.get("previewLink"),
            "info_link": info.get("infoLink"),
            "isbn_10": next((i["identifier"] for i in info.get("industryIdentifiers", [])
                              if i["type"] == "ISBN_10"), None),
            "isbn_13": next((i["identifier"] for i in info.get("industryIdentifiers", [])
                              if i["type"] == "ISBN_13"), None),
        }
    return None


def fetch_open_library(isbn, session=None, retries=3, backoff=2.0):
    """LIVE MODE — query Open Library by ISBN. Returns a normalized dict or None."""
    import requests
    session = session or requests.Session()
    params = {"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"}
    for attempt in range(retries):
        resp = session.get(OPEN_LIBRARY_BOOKS_API, params=params, timeout=15)
        if resp.status_code == 429:
            time.sleep(backoff * (attempt + 1))
            continue
        resp.raise_for_status()
        data = resp.json()
        key = f"ISBN:{isbn}"
        if key not in data:
            return None
        d = data[key]
        return {
            "source": "open_library",
            "open_library_id": (d.get("key") or "").split("/")[-1] or None,
            "title": d.get("title"),
            "subtitle": d.get("subtitle"),
            "authors": [a.get("name") for a in d.get("authors", [])],
            "publisher": (d.get("publishers") or [{}])[0].get("name") if d.get("publishers") else None,
            "pub_year": (d.get("publish_date") or "")[-4:] or None,
            "pages": d.get("number_of_pages"),
            "subjects": [s.get("name") for s in d.get("subjects", [])],
            "cover_image_url": d.get("cover", {}).get("large"),
            "thumbnail_url": d.get("cover", {}).get("small"),
            "preview_link": d.get("preview_url") or d.get("url"),
            "info_link": d.get("url"),
        }
    return None


def load_kaggle_csv(csv_path):
    """
    LIVE MODE — ingest a Kaggle books dataset CSV (e.g. "7k Books with
    Metadata", "Goodreads-books", or similar). Column names vary by dataset,
    so this maps several common schemas onto our raw record shape.
    Unrecognized columns are ignored; missing columns are left blank and can
    be backfilled later via enrich_missing_fields().
    """
    import csv as csvmod

    # candidate column names -> canonical field, checked in order
    COLUMN_ALIASES = {
        "title": ["title", "Book-Title", "book_title", "Name"],
        "subtitle": ["subtitle"],
        "authors": ["authors", "Book-Author", "author", "authors_1"],
        "isbn_10": ["isbn10", "isbn", "ISBN", "ISBN10"],
        "isbn_13": ["isbn13", "ISBN13"],
        "publisher": ["publisher", "Publisher"],
        "pub_year": ["published_year", "publication_year", "Year-Of-Publication", "year"],
        "language": ["language_code", "language", "lang"],
        "pages": ["num_pages", "  num_pages", "pages", "Pages"],
        "genre": ["categories", "genre", "Category"],
        "description": ["description", "Description", "summary"],
        "avg_rating": ["average_rating", "avg_rating", "rating"],
        "rating_count": ["ratings_count", "num_ratings", "rating_count"],
        "cover_image_url": ["thumbnail", "Image-URL-L", "cover_url", "image_url"],
    }

    def pick(row, field):
        for col in COLUMN_ALIASES[field]:
            if col in row and row[col] not in (None, ""):
                return row[col]
        return None

    records = []
    with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csvmod.DictReader(f)
        for row in reader:
            title = pick(row, "title")
            if not title:
                continue
            authors_raw = pick(row, "authors") or ""
            authors = [a.strip() for a in re_split_authors(authors_raw) if a.strip()]
            try:
                pages = int(float(pick(row, "pages"))) if pick(row, "pages") else None
            except (ValueError, TypeError):
                pages = None
            try:
                avg_rating = float(pick(row, "avg_rating")) if pick(row, "avg_rating") else None
            except (ValueError, TypeError):
                avg_rating = None
            try:
                rating_count = int(float(pick(row, "rating_count"))) if pick(row, "rating_count") else None
            except (ValueError, TypeError):
                rating_count = None

            records.append({
                "source": "kaggle",
                "title": title,
                "subtitle": pick(row, "subtitle"),
                "authors": authors,
                "isbn_10": pick(row, "isbn_10"),
                "isbn_13": pick(row, "isbn_13"),
                "publisher": pick(row, "publisher"),
                "pub_year": (pick(row, "pub_year") or "")[:4] if pick(row, "pub_year") else None,
                "language": pick(row, "language"),
                "pages": pages,
                "genre": pick(row, "genre"),
                "description": pick(row, "description"),
                "subjects": [],
                "avg_rating": avg_rating,
                "rating_count": rating_count,
                "cover_image_url": pick(row, "cover_image_url"),
                "open_library_id": None,
                "google_books_id": None,
            })
    return records


def re_split_authors(authors_raw):
    """Kaggle datasets separate co-authors with ';', ',', or '&'."""
    import re
    if not authors_raw:
        return []
    return re.split(r"\s*[;&]\s*|\s*,\s*(?![A-Z]\.)", authors_raw)


def enrich_missing_fields(records, google_api_key=None, sleep_between=0.3,
                           fields=("description", "genre", "cover_image_url", "subjects")):
    """
    For any record missing key fields (typically Kaggle rows without a
    description/category/cover), query Google Books then Open Library by
    ISBN and backfill only the missing fields. Leaves everything else
    (including the original source's values) untouched.
    Requires internet + `requests`; run in LIVE MODE only.
    """
    import requests
    session = requests.Session()
    enriched_count = 0
    for rec in records:
        missing = [f for f in fields if not rec.get(f)]
        if not missing:
            continue
        isbn = rec.get("isbn_13") or rec.get("isbn_10")
        if not isbn:
            continue
        supplement = fetch_google_books(isbn, api_key=google_api_key, session=session) \
            or fetch_open_library(isbn, session=session)
        if not supplement:
            continue
        changed = False
        for f in missing:
            src_field = "subjects" if f == "genre" else f
            val = supplement.get(src_field) or (supplement.get("subjects", [None])[0] if f == "genre" and supplement.get("subjects") else None)
            if val:
                rec[f] = val
                changed = True
        if changed:
            enriched_count += 1
        time.sleep(sleep_between)
    return records, enriched_count


def download_by_isbn_list(isbn_list, google_api_key=None, cache_path=None,
                           sleep_between=0.3):
    """
    LIVE MODE entry point: for each ISBN, query Google Books then Open Library,
    return the raw (unmerged) records from both sources. Caches raw JSON to
    disk so repeated runs don't re-hit rate limits.
    """
    import requests
    session = requests.Session()
    cache_path = cache_path or os.path.join(RAW_DIR, "raw_records.json")
    results = []
    for isbn in isbn_list:
        gb = fetch_google_books(isbn, api_key=google_api_key, session=session)
        ol = fetch_open_library(isbn, session=session)
        for rec in (gb, ol):
            if rec:
                rec["_query_isbn"] = isbn
                results.append(rec)
        time.sleep(sleep_between)  # be a polite API citizen
    with open(cache_path, "w") as f:
        json.dump(results, f, indent=2)
    return results


if __name__ == "__main__":
    # Demo/offline default: load the seed sample.
    recs = load_seed()
    out_path = os.path.join(RAW_DIR, "seed_raw.json")
    with open(out_path, "w") as f:
        json.dump(recs, f, indent=2)
    print(f"Loaded {len(recs)} seed records -> {out_path}")
