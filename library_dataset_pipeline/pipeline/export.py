"""
export.py
=========
STEP 7: normalization into relational tables + CSV export, matching the
Django model shape (Author, Publisher, Category, Tag, Book + join tables).

Also generates the "Library Management Fields" (shelf location, copies,
borrow/reservation counts, popularity rank, availability score) — these are
operational/simulated fields with no public-data source, produced
deterministically from a hash of book_id so re-running the pipeline gives
stable, reproducible values (not random noise every run).
"""
import csv
import hashlib
import os

from pipeline.config import OUTPUT_DIR, STATUS_CHOICES, OPEN_LIBRARY_COVERS


def _stable_int(seed_str, low, high):
    h = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    return low + (h % (high - low + 1))


def assign_ids(records):
    for i, r in enumerate(records, start=1):
        r["book_id"] = i
    return records


def generate_library_fields(records):
    shelves = ["A", "B", "C", "D", "E", "F"]
    for r in records:
        seed = f"{r.get('isbn_13') or r['title']}"
        total_copies = _stable_int(seed + "copies", 1, 8)
        borrowed = _stable_int(seed + "borrowed", 0, total_copies)
        available = max(total_copies - borrowed, 0)
        status = STATUS_CHOICES[0] if available > 0 else STATUS_CHOICES[1]

        r["shelf_location"] = f"{shelves[_stable_int(seed + 'shelf', 0, len(shelves)-1)]}-{_stable_int(seed+'num', 1, 40):02d}"
        r["total_copies"] = total_copies
        r["available_copies"] = available
        r["status"] = status
        r["borrow_count"] = _stable_int(seed + "bc", 0, 500)
        r["reservation_count"] = _stable_int(seed + "rc", 0, 30)
        r["last_borrowed_date"] = None  # left null: needs a real circulation log
        r["review_count"] = _stable_int(seed + "rev", 0, int((r.get("rating_count") or 1000) * 0.02) + 10)
        rating = r.get("avg_rating") or 3.8
        rating_count = r.get("rating_count") or 1000
        r["popularity_score"] = round((rating / 5) * 0.6 + min(rating_count / 5_000_000, 1) * 0.4, 4)
    # popularity rank: higher popularity_score = better (lower) rank
    ranked = sorted(records, key=lambda r: r["popularity_score"], reverse=True)
    for rank, r in enumerate(ranked, start=1):
        r["popularity_rank"] = rank
        max_score = ranked[0]["popularity_score"] or 1
        r["availability_score"] = round(
            0.5 * (r["available_copies"] / max(r["total_copies"], 1)) +
            0.5 * (r["popularity_score"] / max_score), 4)
    return records


def generate_media_fields(records):
    for r in records:
        isbn = r.get("isbn_13") or r.get("isbn_10")
        if isbn:
            r["cover_image_url"] = r.get("cover_image_url") or OPEN_LIBRARY_COVERS.format(isbn=isbn, size="L")
            r["thumbnail_url"] = r.get("thumbnail_url") or OPEN_LIBRARY_COVERS.format(isbn=isbn, size="M")
            r["large_cover_url"] = OPEN_LIBRARY_COVERS.format(isbn=isbn, size="L")
        r["preview_link"] = r.get("preview_link")
        r["info_link"] = r.get("info_link")
    return records


def _write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _listify(v, sep="; "):
    if isinstance(v, list):
        return sep.join(str(x) for x in v)
    return v if v is not None else ""


def build_lookup_tables(records):
    """Normalize authors / publishers / categories / tags into their own tables."""
    authors, publishers, categories, tags = {}, {}, {}, {}

    def get_id(table, name, prefix):
        if name is None:
            return None
        key = name.strip().lower()
        if key not in table:
            table[key] = {"id": f"{prefix}{len(table)+1}", "name": name}
        return table[key]["id"]

    book_authors, book_categories, book_tags = [], [], []

    for r in records:
        r["_author_ids"] = [get_id(authors, a, "AU") for a in r.get("authors", [])]
        r["publisher_id"] = get_id(publishers, r.get("publisher"), "PUB")
        r["_category_id"] = get_id(categories, r.get("genre"), "CAT")
        r["_tag_ids"] = [get_id(tags, t, "TAG") for t in (r.get("tags") or [])]

        for i, aid in enumerate(r["_author_ids"]):
            book_authors.append({"book_id": r["book_id"], "author_id": aid, "is_primary": i == 0})
        book_categories.append({"book_id": r["book_id"], "category_id": r["_category_id"]})
        for tid in r["_tag_ids"]:
            book_tags.append({"book_id": r["book_id"], "tag_id": tid})

    return authors, publishers, categories, tags, book_authors, book_categories, book_tags


def export_all(records, similarity_rows, output_dir=OUTPUT_DIR):
    authors, publishers, categories, tags, book_authors, book_categories, book_tags = build_lookup_tables(records)

    _write_csv(os.path.join(output_dir, "authors.csv"), ["id", "name"], authors.values())
    _write_csv(os.path.join(output_dir, "publishers.csv"), ["id", "name"], publishers.values())
    _write_csv(os.path.join(output_dir, "categories.csv"), ["id", "name"], categories.values())
    _write_csv(os.path.join(output_dir, "tags.csv"), ["id", "name"], tags.values())

    _write_csv(os.path.join(output_dir, "book_authors.csv"),
               ["book_id", "author_id", "is_primary"], book_authors)
    _write_csv(os.path.join(output_dir, "book_categories.csv"),
               ["book_id", "category_id"], book_categories)
    _write_csv(os.path.join(output_dir, "book_tags.csv"),
               ["book_id", "tag_id"], book_tags)

    books_fields = [
        "book_id", "isbn_10", "isbn_13", "open_library_id", "google_books_id",
        "title", "subtitle", "series_name", "volume_number", "edition",
        "publisher_id", "pub_year", "publication_date",
        "language_code", "language_name",
        "genre", "subgenre",
        "shelf_location", "total_copies", "available_copies", "status",
        "description", "num_pages", "reading_time_minutes",
        "cover_image_url", "thumbnail_url", "large_cover_url", "preview_link", "info_link",
        "avg_rating", "rating_count", "review_count", "popularity_score", "popularity_rank",
        "historical_period", "country_setting", "time_setting",
        "borrow_count", "reservation_count", "last_borrowed_date", "availability_score",
    ]
    books_rows = []
    for r in records:
        row = {k: r.get(k, "") for k in books_fields}
        row["num_pages"] = r.get("pages", "")
        books_rows.append(row)
    _write_csv(os.path.join(output_dir, "books.csv"), books_fields, books_rows)

    rec_meta_fields = ["book_id", "mood", "writing_style", "difficulty_level", "reading_level",
                        "target_audience", "learning_outcomes", "skills_covered",
                        "recommendation_keywords", "fantasy_elements", "scifi_elements",
                        "themes", "keywords", "tags", "subjects"]
    rec_meta_rows = []
    for r in records:
        row = {k: _listify(r.get(k)) for k in rec_meta_fields if k != "book_id"}
        row["book_id"] = r["book_id"]
        rec_meta_rows.append(row)
    _write_csv(os.path.join(output_dir, "recommendation_metadata.csv"), rec_meta_fields, rec_meta_rows)

    chatbot_fields = ["book_id", "short_ai_summary", "long_ai_summary",
                       "recommendation_reason", "search_text"]
    chatbot_rows = [{k: r.get(k, "") for k in chatbot_fields} for r in records]
    _write_csv(os.path.join(output_dir, "chatbot_metadata.csv"), chatbot_fields, chatbot_rows)

    sim_fields = ["book_id", "similar_book_id", "similarity_score", "rank"]
    _write_csv(os.path.join(output_dir, "similar_books.csv"), sim_fields, similarity_rows)

    return {
        "authors": len(authors), "publishers": len(publishers),
        "categories": len(categories), "tags": len(tags),
        "books": len(books_rows), "book_authors": len(book_authors),
        "book_categories": len(book_categories), "book_tags": len(book_tags),
        "recommendation_metadata": len(rec_meta_rows), "chatbot_metadata": len(chatbot_rows),
        "similar_books": len(similarity_rows),
    }
