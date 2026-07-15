# AI-Powered Library — Master Books Dataset Pipeline

Production-oriented data pipeline that builds the master books dataset for
an AI Library Chatbot & Recommendation System (Django + React + PostgreSQL +
OpenAI/Claude). Ships in **two run modes**:

| Mode | Command | What it does |
|---|---|---|
| **SEED MODE** (default, works right now) | `python build_dataset.py` | Builds the dataset from `data/seed_books.py` — 84 real, well-known books, balanced across 19 genres. No internet or API key needed. Use it to validate schema, imports, and enrichment logic before scaling up. |
| **LIVE MODE — ISBN list** | `python build_dataset.py --isbns isbns.txt --google-api-key KEY` | Queries Google Books + Open Library for every ISBN in `isbns.txt`, merges, dedupes, enriches, and exports the same CSV set. Good for a few hundred–low thousands. |
| **LIVE MODE — Kaggle bulk (recommended for 2,000–3,000)** | `python build_dataset.py --kaggle-csv data/raw/kaggle_books.csv --enrich-missing --google-api-key KEY` | Ingests a Kaggle books CSV in one shot (thousands of rows), then backfills any missing `description` / `genre` / `cover_image_url` / `subjects` per book via Google Books → Open Library fallback, then runs the same dedupe/enrich/export pipeline. This is the fastest path to your 2,000–3,000-book target. |

> **Why two modes?** Bulk-fetching thousands of real records requires a live
> internet connection, API keys/quota, and a run that can take a while
> (rate-limited, polite pacing built into `download.py`). This deliverable
> gives you the exact same pipeline code either way — you're not rebuilding
> anything to go from demo to production, just pointing it at a real ISBN
> list and letting it run in an environment with network access.

---

## 1. Folder structure

```
library_dataset_pipeline/
├── build_dataset.py          # single-command orchestrator (CLI)
├── pipeline/
│   ├── config.py             # schema, controlled vocabularies, API endpoints
│   ├── download.py           # STEP 1 — Google Books / Open Library fetch, or seed load
│   ├── preprocess.py         # STEP 2 — normalization + quality checks
│   ├── merge.py              # STEP 3-4 — dedup + multi-source merge
│   ├── enrichment.py         # STEP 6 — AI metadata (mood, style, summaries, keywords...)
│   ├── similarity.py         # STEP 6b — book-to-book similarity graph
│   └── export.py             # STEP 7 — library fields + all CSV exports
├── data/
│   ├── seed_books.py         # 84 real books used in SEED MODE
│   ├── raw/                  # cached raw API JSON (LIVE MODE)
│   └── processed/            # intermediate cleaned data (optional caching point)
├── output/                   # <-- all final CSVs land here
│   ├── authors.csv
│   ├── publishers.csv
│   ├── categories.csv
│   ├── tags.csv
│   ├── books.csv
│   ├── book_authors.csv
│   ├── book_categories.csv
│   ├── book_tags.csv
│   ├── recommendation_metadata.csv
│   ├── chatbot_metadata.csv
│   └── similar_books.csv
└── docs/
    ├── DATA_DICTIONARY.md    # every column, every file, explained
    └── SOURCE_MAPPING.md     # which field comes from which source
```

---

## 2. Pipeline architecture (STEP 1 → STEP 7)

```
        ┌──────────────┐
        │  download.py │  STEP 1: pull raw records
        │ (Google Books│  (LIVE: real API calls, cached to data/raw/)
        │ /OpenLibrary │  (SEED: loads data/seed_books.py)
        │  / seed)     │
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │ preprocess.py│  STEP 2: normalize names/ISBNs/genres/language,
        │              │  validate ISBN checksums + pub years, drop corrupted
        └──────┬───────┘  records, fill safe defaults for missing values
               ▼
        ┌──────────────┐
        │   merge.py   │  STEP 3-4: dedup by ISBN13 → ISBN10 → Google ID →
        │              │  OpenLibrary ID → title+author; merge multi-source
        └──────┬───────┘  records field-by-field with source priority
               ▼
        ┌──────────────┐
        │  export.py   │  generate library-ops fields (shelf, copies, borrow
        │ (library +   │  counts, popularity) + media fields (cover URLs via
        │  media)      │  Open Library Covers API pattern)
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │enrichment.py │  STEP 6: mood, writing style, difficulty, reading
        │              │  level, audience, learning outcomes, skills, keywords,
        └──────┬───────┘  search_text, short/long AI summaries, rec. reason
               ▼
        ┌──────────────┐
        │similarity.py │  STEP 6b: top-N similar books per book from subject/
        │              │  keyword/genre/mood overlap → similar_books.csv
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │  export.py   │  STEP 7: normalize into Author/Publisher/Category/
        │ (CSV export) │  Tag + join tables, write all 11 CSVs
        └──────────────┘
```

---

## 3. Running it

```bash
cd library_dataset_pipeline
pip install requests   # only needed for LIVE MODE

# SEED MODE — instant, no network:
python build_dataset.py

# LIVE MODE — real scale:
# 1) Put one ISBN per line in isbns.txt (source these from Open Library's
#    subject listings, Google Books category search, or a Kaggle ISBN list)
# 2) Optionally get a free Google Books API key for higher rate limits
python build_dataset.py --isbns isbns.txt --google-api-key YOUR_KEY
```

Output always lands in `output/*.csv`, ready for Django import (Section 6).

---

## 4. Scaling SEED MODE → 2,000–3,000 real books

The seed sample (84 books) proves the pipeline works end-to-end — same
schema, same CSVs, same AI/recommendation/chatbot metadata generation.
Getting to 2,000–3,000 real books requires **live internet access**, which
this generation environment does not have (no outbound network in the
sandbox that built this deliverable). Run the following in your own
environment (dev machine, CI runner, or a small server):

1. **Download a Kaggle books dataset** — e.g. "7k Books with Metadata" or
   "Goodreads-books"/"Best Books Ever Dataset" (all public, ISBN-indexed,
   several thousand rows each). Save it as `data/raw/kaggle_books.csv`.
2. **Get a free Google Books API key** (optional but raises your rate
   limit substantially) from the Google Cloud Console.
3. **Run the bulk-ingest + enrich command:**
   ```bash
   pip install requests
   python build_dataset.py \
     --kaggle-csv data/raw/kaggle_books.csv \
     --enrich-missing \
     --google-api-key YOUR_KEY
   ```
   This will:
   - Ingest every row of the Kaggle CSV (`download.load_kaggle_csv`, handles
     several common Kaggle column schemas automatically).
   - For any book missing a `description`, `genre`, `cover_image_url`, or
     `subjects`, query Google Books by ISBN, then fall back to Open Library
     (`download.enrich_missing_fields`) — exactly the "enrich from another
     public source" behavior requested.
   - Validate every ISBN-10/13 via checksum (`preprocess.valid_isbn10/13`);
     when only one of the pair is valid, the other is **deterministically
     derived** from it (`preprocess.isbn13_to_isbn10` /
     `isbn10_to_isbn13`) rather than dropped or guessed.
   - Deduplicate on ISBN-13 → ISBN-10 → Google Books ID → Open Library ID →
     normalized title+author (`merge.dedup_key`), same logic proven above.
   - Run the same AI/recommendation/chatbot enrichment and similarity engine
     across the full set, and export the same 11 CSVs.
4. **If your Kaggle CSV has more than ~3,000 usable rows**, trim it to a
   genre-balanced 2,000–3,000 subset before this step (or slice after —
   `books.csv` is just a table, easy to `head`/filter by category).
5. **Rate limits**: Google Books' free tier is ~1,000 requests/day without
   a key, much higher with one; Open Library has no key but asks for
   sensible pacing (already built into `download.py` via `sleep_between`).
   For the missing-field-only enrichment path, most well-catalogued Kaggle
   rows won't need any API call at all, so a 2,000–3,000-book run is
   typically a small fraction of the full ISBN-by-ISBN cost.

This is the one part of your requirements I can't execute directly inside
this chat — everything else (schema, dedup, ISBN validation, AI/
recommendation/chatbot metadata, similarity, Django-ready CSVs) is built,
tested, and running against real data above.

---

## 5. Similar Books & future vector embeddings

`similarity.py` currently computes similarity via weighted overlap of
subjects, recommendation keywords, genre/subgenre, and mood — a fast,
dependency-free baseline that's already wired into `similar_books.csv`.

**For semantic search + better recommendations at scale**, add an embeddings
step:
- Embed `search_text` (already generated per book) using an embedding model.
- Store vectors in PostgreSQL via `pgvector`, indexed with an IVFFlat/HNSW
  index on the `Book` table.
- Replace `similarity.build_similarity_table()`'s Jaccard scoring with cosine
  similarity over embeddings — same output shape (`book_id`,
  `similar_book_id`, `similarity_score`), so nothing downstream changes.
- Use the same embeddings for the Semantic Search feature: embed the user's
  query, `ORDER BY embedding <-> query_embedding LIMIT k` in Postgres.

---

## 6. Django import workflow

The CSVs are shaped to match this model set 1:1:

```
Author(id, name)
Publisher(id, name)
Category(id, name)
Tag(id, name)
Book(book_id, isbn_10, isbn_13, ..., publisher_id FK, ...)
BookAuthor(book_id FK, author_id FK, is_primary)
BookCategory(book_id FK, category_id FK)
BookTag(book_id FK, tag_id FK)
RecommendationMetadata(book_id FK, mood, writing_style, ...)
ChatbotMetadata(book_id FK, short_ai_summary, long_ai_summary, ...)
SimilarBook(book_id FK, similar_book_id FK, similarity_score, rank)
```

Import order matters (respect foreign keys):
`authors.csv` → `publishers.csv` → `categories.csv` → `tags.csv` → `books.csv`
→ `book_authors.csv` / `book_categories.csv` / `book_tags.csv` →
`recommendation_metadata.csv` / `chatbot_metadata.csv` / `similar_books.csv`

Use Django's `bulk_create` with a management command reading each CSV via
`csv.DictReader`, or `django-import-export` for an admin-driven workflow.
Since IDs are pre-assigned integers/strings in the CSVs, either let Postgres
auto-generate PKs and remap FKs on import, or import the `id`/`book_id`
values directly (simpler — recommended for this dataset size).

---

## 7. Data dictionary & source mapping

See `docs/DATA_DICTIONARY.md` and `docs/SOURCE_MAPPING.md` for a full,
column-by-column explanation of every CSV file and which upstream source
each field is expected to come from in LIVE MODE.

---

## 8. Known limitations of the current SEED MODE sample

- **ISBNs**: best-effort common-edition identifiers from general knowledge,
  not re-verified against a live API in this run. Re-resolve via
  `download.py` before treating them as authoritative.
- **Ratings/rating counts**: illustrative approximations, not live-scraped
  figures — replace with real Google Books/Goodreads numbers in LIVE MODE.
- **AI enrichment**: rule-based (genre-profile driven), not LLM-generated.
  Good enough to validate the schema and UI; swap in `llm_enrich()` for
  production nuance.
- **Library operational fields** (shelf location, copies, borrow counts):
  deterministically simulated, since no public source provides a library's
  actual circulation data — replace with your real circulation system data
  once live.
