# Source Mapping (LIVE MODE)

| Field | Primary Source | Fallback Source | Notes |
|---|---|---|---|
| title, subtitle | Google Books | Open Library | Google Books generally cleaner for subtitle splitting |
| authors | Open Library | Google Books | Open Library resolves author-key → name |
| isbn_10, isbn_13 | Query input | Google Books industryIdentifiers | Validated via checksum in preprocess.py |
| publisher | Open Library | Google Books | |
| pub_year, publication_date | Open Library publish_date | Google Books publishedDate | |
| pages | Open Library number_of_pages | Google Books pageCount | |
| description | Google Books volumeInfo.description | — | Google Books has the most consistently populated descriptions |
| subjects/categories | Open Library subjects | Google Books categories | Unioned, not overwritten, in merge.py |
| cover_image_url, thumbnail_url | Open Library Covers API (`/b/isbn/{isbn}-{size}.jpg`) | Google Books imageLinks | Covers API works even without a prior lookup, given a valid ISBN |
| avg_rating, rating_count | Google Books volumeInfo | — | Google Books; cross-check against Goodreads exports if higher precision needed |
| preview_link, info_link | Google Books / Open Library | — | |
| open_library_id | Open Library response `key` | — | |
| google_books_id | Google Books response `id` | — | |
| mood, writing_style, difficulty_level, reading_level, target_audience, learning_outcomes, skills_covered, recommendation_keywords, short/long AI summary, recommendation_reason | **Generated** (rule-based in this build; recommend LLM-backed for production) | — | See `enrichment.py` |
| shelf_location, total_copies, available_copies, status, borrow_count, reservation_count, popularity_rank, availability_score | **Generated** (simulated, deterministic) | — | No public source exists for a specific library's circulation data — replace with real ILS/circulation records once integrated |
| similar_books / similarity_score | **Computed** from subjects/keywords/genre/mood overlap | — | Upgrade path to embeddings in `similarity.py` |

## Kaggle Dataset Cross-Reference (optional additional source)

If layering in a Kaggle books dataset (e.g. "Books Dataset" or
"Goodbooks-10k"), map their common columns as follows before running through
`preprocess.py`:

| Kaggle column (typical) | Pipeline field |
|---|---|
| isbn / isbn13 | isbn_10 / isbn_13 |
| title | title |
| authors | authors (split on `;` or `,` as needed) |
| average_rating | avg_rating |
| ratings_count / work_ratings_count | rating_count |
| language_code | language_code |
| original_publication_year | pub_year |
| image_url / small_image_url | cover_image_url / thumbnail_url |

Feed these rows into `download.py`'s raw-record shape (add a
`load_kaggle_csv()` function following the same dict shape as `load_seed()`)
so they flow through the exact same `preprocess → merge → enrich → export`
pipeline.
