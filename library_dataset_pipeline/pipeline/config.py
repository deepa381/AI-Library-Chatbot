"""
config.py — shared constants, paths, and controlled vocabularies for the
AI-Powered Library dataset pipeline.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

for d in (RAW_DIR, PROCESSED_DIR, OUTPUT_DIR):
    os.makedirs(d, exist_ok=True)

# ---- external API endpoints (used by download.py when network is available) ----
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
OPEN_LIBRARY_BOOKS_API = "https://openlibrary.org/api/books"
OPEN_LIBRARY_SEARCH_API = "https://openlibrary.org/search.json"
OPEN_LIBRARY_COVERS = "https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg"  # size: S, M, L

# ---- controlled vocabularies for AI enrichment (rule-based fallback) ----
# Each genre maps to a plausible default mood / style / difficulty / audience
# profile. This is a deterministic, explainable fallback for when no LLM call
# is configured. Swap `enrichment.rule_based_enrich()` for an LLM-backed
# implementation (see enrichment.py docstring) for higher-fidelity tagging
# at production scale.
GENRE_PROFILE = {
    "Literary Fiction":  dict(mood=["Emotional", "Thought-provoking"], style=["Narrative", "Slow-paced"],
                              difficulty="Intermediate", reading_level="Adult", audience=["General Readers", "Students"]),
    "Science Fiction":   dict(mood=["Suspenseful", "Thrilling"], style=["Narrative", "Fast-paced"],
                              difficulty="Intermediate", reading_level="Adult", audience=["General Readers", "Engineers"]),
    "Fantasy":           dict(mood=["Mysterious", "Inspirational"], style=["Narrative", "Descriptive"],
                              difficulty="Intermediate", reading_level="Young Adult", audience=["General Readers"]),
    "Mystery/Thriller":  dict(mood=["Suspenseful", "Dark"], style=["Fast-paced", "Narrative"],
                              difficulty="Intermediate", reading_level="Adult", audience=["General Readers"]),
    "Romance":           dict(mood=["Romantic", "Emotional"], style=["Conversational", "Narrative"],
                              difficulty="Beginner", reading_level="Adult", audience=["General Readers"]),
    "Nonfiction":        dict(mood=["Educational", "Inspirational"], style=["Academic", "Conversational"],
                              difficulty="Intermediate", reading_level="Adult", audience=["Students", "Professionals", "Researchers"]),
    "Biography":         dict(mood=["Inspirational", "Emotional"], style=["Narrative", "Conversational"],
                              difficulty="Intermediate", reading_level="Adult", audience=["General Readers", "Students"]),
    "Self-Help":         dict(mood=["Inspirational", "Educational"], style=["Conversational", "Simple"],
                              difficulty="Beginner", reading_level="Adult", audience=["Professionals", "General Readers"]),
    "Business":          dict(mood=["Educational", "Inspirational"], style=["Conversational", "Technical"],
                              difficulty="Intermediate", reading_level="Professional", audience=["Professionals", "Students"]),
    "Young Adult":       dict(mood=["Emotional", "Heartwarming"], style=["Fast-paced", "Conversational"],
                              difficulty="Beginner", reading_level="Teen", audience=["Students", "General Readers"]),
    "Children's":        dict(mood=["Heartwarming", "Funny"], style=["Simple", "Narrative"],
                              difficulty="Beginner", reading_level="Children", audience=["Children", "Parents", "Teachers"]),
    "Horror":            dict(mood=["Dark", "Suspenseful"], style=["Fast-paced", "Narrative"],
                              difficulty="Intermediate", reading_level="Adult", audience=["General Readers"]),
    "Classics":          dict(mood=["Thought-provoking", "Dark"], style=["Poetic", "Slow-paced"],
                              difficulty="Advanced", reading_level="Adult", audience=["Students", "Researchers", "General Readers"]),
}

GENRE_LEARNING_OUTCOMES = {
    "Literary Fiction": ["Empathy", "Critical Thinking"],
    "Science Fiction": ["Problem Solving", "Critical Thinking"],
    "Fantasy": ["Imagination", "Personal Growth"],
    "Mystery/Thriller": ["Critical Thinking", "Problem Solving"],
    "Romance": ["Emotional Intelligence", "Communication"],
    "Nonfiction": ["Critical Thinking", "History"],
    "Biography": ["Leadership", "Personal Growth"],
    "Self-Help": ["Personal Growth", "Career"],
    "Business": ["Leadership", "Career", "Problem Solving"],
    "Young Adult": ["Personal Growth", "Communication"],
    "Children's": ["Empathy", "Communication"],
    "Horror": ["Critical Thinking"],
    "Classics": ["Critical Thinking", "History", "Communication"],
}

WORDS_PER_MINUTE = 250  # used for reading-time estimate

STATUS_CHOICES = ["Available", "Borrowed", "Reserved", "Lost"]

BOOKS_FIELDS = [
    "book_id", "isbn_10", "isbn_13", "open_library_id", "google_books_id",
    "title", "subtitle", "series_name", "volume_number", "edition",
    "publisher_id", "publication_year", "publication_date",
    "language_code", "language_name",
    "category", "genre", "subgenre",
    "shelf_location", "total_copies", "available_copies", "status",
    "description", "subjects", "keywords", "tags", "themes",
    "num_pages", "reading_time_minutes",
    "cover_image_url", "thumbnail_url", "large_cover_url", "preview_link", "info_link",
    "average_rating", "rating_count", "review_count", "popularity_score",
    "mood", "writing_style", "difficulty_level", "reading_level",
    "target_audience", "learning_outcomes", "skills_covered",
    "recommendation_keywords", "fantasy_elements", "scifi_elements",
    "historical_period", "country_region_setting", "time_period_setting",
    "borrow_count", "reservation_count", "popularity_rank",
    "last_borrowed_date", "availability_score",
    "search_text",
]
