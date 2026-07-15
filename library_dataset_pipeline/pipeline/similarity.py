"""
similarity.py
=============
Builds the book-to-book similarity graph used for `similar_books.csv`.

Approach: weighted Jaccard-style overlap across four signals — subjects,
recommendation_keywords, genre/subgenre, and mood — computed pairwise.
This is deliberately dependency-free (no sklearn/numpy required) so the
pipeline runs anywhere. At full 1,000-5,000 book scale, swap this for
embedding-based cosine similarity (see README "Future: vector embeddings"
section) for much better semantic matches — this keyword-overlap version
is a solid, fast baseline and a reasonable fallback either way.
"""
from itertools import combinations

WEIGHTS = {"subjects": 0.4, "keywords": 0.25, "genre": 0.25, "mood": 0.1}


def _set(rec, field):
    v = rec.get(field)
    if isinstance(v, list):
        return {str(x).lower() for x in v}
    if isinstance(v, str):
        return {v.lower()}
    return set()


def _jaccard(a, b):
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def pairwise_score(a, b):
    score = 0.0
    score += WEIGHTS["subjects"] * _jaccard(_set(a, "subjects"), _set(b, "subjects"))
    score += WEIGHTS["keywords"] * _jaccard(_set(a, "recommendation_keywords"), _set(b, "recommendation_keywords"))
    score += WEIGHTS["genre"] * (1.0 if a.get("genre") == b.get("genre") else
                                  (0.4 if a.get("subgenre") == b.get("subgenre") else 0.0))
    score += WEIGHTS["mood"] * _jaccard(_set(a, "mood"), _set(b, "mood"))
    return round(score, 4)


def build_similarity_table(records, top_n=10, min_score=0.05):
    """
    records: list of enriched book dicts, each must have 'book_id'.
    Returns list of rows: {book_id, similar_book_id, similarity_score, rank}
    """
    scores = {r["book_id"]: [] for r in records}
    for a, b in combinations(records, 2):
        s = pairwise_score(a, b)
        if s >= min_score:
            scores[a["book_id"]].append((b["book_id"], s))
            scores[b["book_id"]].append((a["book_id"], s))

    rows = []
    for book_id, sims in scores.items():
        sims.sort(key=lambda x: x[1], reverse=True)
        for rank, (sim_id, s) in enumerate(sims[:top_n], start=1):
            rows.append({"book_id": book_id, "similar_book_id": sim_id,
                         "similarity_score": s, "rank": rank})
    return rows


def attach_similar_titles(records, similarity_rows, top_n=10):
    """Convenience: add a `similar_books` (title list) field back onto each record."""
    by_id = {r["book_id"]: r for r in records}
    grouped = {}
    for row in similarity_rows:
        grouped.setdefault(row["book_id"], []).append(row)
    for r in records:
        rows = sorted(grouped.get(r["book_id"], []), key=lambda x: x["rank"])[:top_n]
        r["similar_books"] = [by_id[row["similar_book_id"]]["title"] for row in rows
                               if row["similar_book_id"] in by_id]
    return records
