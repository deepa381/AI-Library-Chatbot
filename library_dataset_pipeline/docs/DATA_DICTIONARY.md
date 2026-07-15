# Data Dictionary

## books.csv
| Column | Type | Description |
|---|---|---|
| book_id | int | Primary key, stable within a pipeline run |
| isbn_10 / isbn_13 | str | Validated (checksum-checked for ISBN-13) identifiers |
| open_library_id | str | Open Library edition key (LIVE MODE only) |
| google_books_id | str | Google Books volume ID (LIVE MODE only) |
| title / subtitle | str | Normalized (whitespace-trimmed) title fields |
| series_name / volume_number / edition | str/int | Populated when source data provides them |
| publisher_id | str (FK) | References `publishers.csv:id` |
| pub_year | int | Validated publication year (1450–2027 range check) |
| publication_date | str | Full date when available |
| language_code / language_name | str | ISO 639-1 code + human-readable name |
| genre / subgenre | str | Normalized top-level genre + finer subgenre |
| shelf_location | str | Simulated (e.g. "C-14") — replace with real circulation data |
| total_copies / available_copies | int | Simulated inventory counts |
| status | str | Available / Borrowed / Reserved / Lost |
| description | str | Book synopsis (own-words summary; never a verbatim quote) |
| num_pages | int | Page count |
| reading_time_minutes | int | Estimated from pages × ~275 words/page ÷ 250 wpm |
| cover_image_url / thumbnail_url / large_cover_url | str | Open Library Covers API URLs |
| preview_link / info_link | str | External links to the book's page |
| avg_rating / rating_count / review_count | float/int | Quality signals |
| popularity_score / popularity_rank | float/int | Derived composite score (rating × 0.6 + normalized rating volume × 0.4) |
| historical_period / country_setting / time_setting | str | Setting metadata for filtering |
| borrow_count / reservation_count | int | Simulated library-ops counters |
| last_borrowed_date | str/null | Left null — populate from a real circulation log |
| availability_score | float | Blend of copy availability and popularity |

## authors.csv / publishers.csv / categories.csv / tags.csv
| Column | Description |
|---|---|
| id | Normalized surrogate key (e.g. `AU3`, `PUB7`, `CAT2`, `TAG14`) |
| name | Deduplicated, case-insensitive-normalized display name |

## book_authors.csv / book_categories.csv / book_tags.csv
Standard many-to-many join tables: `book_id`, `{author|category|tag}_id`
(`book_authors.csv` additionally has `is_primary` marking the lead author).

## recommendation_metadata.csv
| Column | Description |
|---|---|
| book_id | FK to books.csv |
| mood | Semicolon-separated moods (e.g. `Emotional; Thought-provoking`) |
| writing_style | Semicolon-separated styles |
| difficulty_level | Beginner / Intermediate / Advanced / Expert |
| reading_level | Children / Teen / Young Adult / Adult / Professional |
| target_audience | Semicolon-separated audiences |
| learning_outcomes | Semicolon-separated outcomes (e.g. `Leadership; Career`) |
| skills_covered | Semicolon-separated skills, derived from subjects |
| recommendation_keywords | 10-30 semantic-search keywords |
| fantasy_elements / scifi_elements | Populated only for matching genres |
| themes / keywords / tags / subjects | Supporting semicolon-separated lists |

## chatbot_metadata.csv
| Column | Description |
|---|---|
| book_id | FK to books.csv |
| short_ai_summary | One sentence |
| long_ai_summary | ~150-250 words |
| recommendation_reason | Why the chatbot would recommend this book |
| search_text | Concatenated title/author/genre/description/keywords/tags/subjects for semantic search indexing |

## similar_books.csv
| Column | Description |
|---|---|
| book_id | Source book |
| similar_book_id | Related book (from within this dataset) |
| similarity_score | 0-1 weighted overlap score (subjects 40%, keywords 25%, genre 25%, mood 10%) |
| rank | 1 = most similar, ascending |
