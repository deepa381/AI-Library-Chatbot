import logging
from collections import Counter

from django.conf import settings
from django.db.models import Q, Value, IntegerField, Case, When

from google import genai
from google.genai import errors as genai_errors

from books.models import Book
from chatbot.models import ChatSession, ChatMessage
from recommendation.models import RecommendationHistory
from core.gemini_utils import GeminiUtils

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User Preference Service
# ---------------------------------------------------------------------------

class UserPreferenceService:
    """
    Analyses a user's borrow/reservation/recommendation history to automatically
    learn their preferences and build a profile for personalised AI responses.
    """

    @staticmethod
    def get_profile(user) -> dict:
        """
        Returns a dict with aggregated user preference signals:
        - favorite_categories: top 5 category names
        - favorite_authors: top 5 author full names
        - favorite_tags: top 5 tag names
        - favorite_moods: top 3 moods from recommendation metadata
        - favorite_difficulty: most common difficulty level
        - recently_borrowed_ids: list of book IDs (to avoid re-recommending)
        """
        # Lazy imports to avoid circular dependencies
        from borrow.models import BorrowRecord
        from reservations.models import Reservation

        borrowed_books = list(
            BorrowRecord.objects.filter(member__user=user)
            .select_related('book')
            .prefetch_related(
                'book__categories', 'book__authors', 'book__tags',
                'book__recommendation_metadata'
            )
            .order_by('-borrow_date')[:50]
        )
        reserved_books = list(
            Reservation.objects.filter(member__user=user)
            .select_related('book')
            .prefetch_related(
                'book__categories', 'book__authors', 'book__tags'
            )
            .order_by('-reservation_date')[:30]
        )

        all_books = [r.book for r in borrowed_books] + [r.book for r in reserved_books]

        cat_counter: Counter = Counter()
        author_counter: Counter = Counter()
        tag_counter: Counter = Counter()
        mood_counter: Counter = Counter()
        difficulty_counter: Counter = Counter()

        for book in all_books:
            for cat in book.categories.all():
                cat_counter[cat.name] += 1
            for author in book.authors.all():
                author_counter[str(author)] += 1
            for tag in book.tags.all():
                tag_counter[tag.name] += 1
            if hasattr(book, 'recommendation_metadata'):
                meta = book.recommendation_metadata
                for mood in meta.mood.split(';'):
                    m = mood.strip()
                    if m:
                        mood_counter[m] += 1
                if meta.difficulty_level:
                    difficulty_counter[meta.difficulty_level] += 1

        recently_borrowed_ids = [r.book_id for r in borrowed_books[:20]]

        return {
            'favorite_categories': [k for k, _ in cat_counter.most_common(5)],
            'favorite_authors': [k for k, _ in author_counter.most_common(5)],
            'favorite_tags': [k for k, _ in tag_counter.most_common(5)],
            'favorite_moods': [k for k, _ in mood_counter.most_common(3)],
            'favorite_difficulty': difficulty_counter.most_common(1)[0][0] if difficulty_counter else '',
            'recently_borrowed_ids': recently_borrowed_ids,
        }

    @staticmethod
    def format_for_prompt(profile: dict) -> str:
        """Renders the preference profile as a concise natural-language string."""
        parts = []
        if profile['favorite_categories']:
            parts.append(f"Favorite genres/categories: {', '.join(profile['favorite_categories'])}")
        if profile['favorite_authors']:
            parts.append(f"Favorite authors: {', '.join(profile['favorite_authors'])}")
        if profile['favorite_tags']:
            parts.append(f"Preferred topics/tags: {', '.join(profile['favorite_tags'])}")
        if profile['favorite_moods']:
            parts.append(f"Preferred reading mood: {', '.join(profile['favorite_moods'])}")
        if profile['favorite_difficulty']:
            parts.append(f"Preferred difficulty: {profile['favorite_difficulty']}")
        return '\n'.join(parts) if parts else 'No preference history available yet.'


# ---------------------------------------------------------------------------
# Gemini AI Service
# ---------------------------------------------------------------------------

class GeminiService:
    """
    Reusable Gemini service that initialises the Google GenAI client once
    and exposes a single call_gemini() method for all AI interactions.
    """

    def __init__(self):
        try:
            self.client = GeminiUtils.get_client()
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.client = None

    def _messages_to_prompt(self, messages: list) -> str:
        """
        Converts an OpenAI-style messages list into a single prompt string
        that the Gemini generate_content API accepts.

        Each message dict has 'role' (system | user | assistant) and 'content'.
        """
        parts = []
        for msg in messages:
            role = msg.get('role', 'user').capitalize()
            content = msg.get('content', '')
            parts.append(f"{role}:\n{content}")
        return "\n\n".join(parts)

    def call_gemini(self, messages: list) -> str:
        """
        Converts the messages list to a prompt and calls the Gemini API.
        Returns the text response or a meaningful error message on failure.
        """
        if not self.client:
            return "Gemini API error: Client not initialized. Please check configuration."

        prompt = self._messages_to_prompt(messages)
        try:
            model_name = GeminiUtils.get_available_model()
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text

        except genai_errors.APIError as e:
            status = getattr(e, 'status_code', None) or getattr(e, 'code', None)
            if status == 401:
                msg = "Gemini API error: Invalid API key. Please check your GEMINI_API_KEY configuration."
            elif status == 429:
                msg = "Gemini API error: Quota exceeded. Please check your Google AI quota."
            elif status == 503:
                msg = "Gemini API error: Service temporarily unavailable. Please try again later."
            else:
                msg = f"Gemini API error: {str(e)}"
            logger.error(msg)
            return msg

        except Exception as e:
            error_str = str(e).lower()
            if 'timeout' in error_str:
                msg = "Gemini request timed out. Please try again."
            elif 'network' in error_str or 'connection' in error_str:
                msg = "Network error while contacting Gemini. Please check your connection."
            else:
                msg = f"Unexpected error calling Gemini API: {str(e)}"
            logger.error(msg, exc_info=True)
            return msg

    def call_gemini_raw(self, prompt: str) -> str:
        """
        Calls Gemini with a raw prompt string (no message list conversion).
        Used for the hybrid recommendation world-knowledge section.
        """
        if not self.client:
            return ""
        try:
            model_name = GeminiUtils.get_available_model()
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text or ""
        except Exception as e:
            logger.warning(f"[GeminiService] call_gemini_raw failed: {e}")
            return ""


# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------

class PromptBuilder:
    """
    Builds system and user prompts for chatbot and recommendation tasks,
    injecting library metadata and context to prevent hallucinations.
    """

    @staticmethod
    def build_chatbot_system_prompt() -> str:
        return (
            "You are the Library Assistant, a knowledgeable and friendly AI librarian. "
            "Your role has two parts:\n"
            "1. LIBRARY INVENTORY: You know exactly which books are physically available in this library. "
            "You will be given the list of matching books. Summarize them clearly and accurately.\n"
            "2. WORLD KNOWLEDGE: You are also an expert on world-famous books. When asked, you can recommend "
            "well-known books on any topic from your knowledge, but you MUST label them clearly as "
            "'Popular Books Worldwide' and NEVER claim they are in the library inventory.\n"
            "CRITICAL RULES:\n"
            "- Never invent availability information. Only the library database knows what is on the shelf.\n"
            "- Keep the two sections completely separate in your response.\n"
            "- Format your response using markdown."
        )

    @staticmethod
    def _format_book_for_prompt(idx: int, book) -> str:
        """Format a single book as a numbered, structured block for the Gemini prompt."""
        try:
            authors_str = ", ".join([str(a) for a in book.authors.all()]) or "Unknown"
        except Exception:
            authors_str = "Unknown"
        try:
            categories_str = ", ".join([c.name for c in book.categories.all()])
        except Exception:
            categories_str = ""
        try:
            tags_str = ", ".join([t.name for t in book.tags.all()])
        except Exception:
            tags_str = ""

        difficulty = ""
        if hasattr(book, 'recommendation_metadata') and book.recommendation_metadata:
            difficulty = getattr(book.recommendation_metadata, 'difficulty_level', '')

        # Best available description/summary
        summary = ""
        if hasattr(book, 'chatbot_metadata') and book.chatbot_metadata:
            summary = (getattr(book.chatbot_metadata, 'short_ai_summary', '')
                       or getattr(book, 'description', ''))
        if not summary:
            summary = getattr(book, 'description', '')

        availability = "Available" if getattr(book, 'available_copies', 0) > 0 else "Not available"

        lines = [
            f"{idx}.",
            f"Title: {getattr(book, 'title', 'Unknown')}",
            f"Author: {authors_str}",
        ]
        if categories_str:
            lines.append(f"Category: {categories_str}")
        if tags_str:
            lines.append(f"Tags: {tags_str}")
        if difficulty:
            lines.append(f"Difficulty: {difficulty}")
        lines.append(f"Availability: {availability}")
        if summary:
            lines.append(f"Summary: {summary[:300]}")
        return "\n".join(lines)

    @staticmethod
    def build_library_section(library_books: list) -> str:
        """
        Formats the library books into the '### Available in Our Library' section.
        Returns a formatted markdown string, or a 'not found' notice if empty.
        """
        if not library_books:
            return (
                "### [LIBRARY] Available in Our Library\n\n"
                "*No matching books are currently available in our library inventory.*\n"
            )
        lines = ["### [LIBRARY] Available in Our Library\n"]
        for book in library_books:
            try:
                authors_str = ", ".join([str(a) for a in book.authors.all()]) or "Unknown"
            except Exception:
                authors_str = "Unknown"
            try:
                categories_str = ", ".join([c.name for c in book.categories.all()])
            except Exception:
                categories_str = ""

            availability = "[AVAILABLE]" if getattr(book, 'available_copies', 0) > 0 else "[NOT AVAILABLE]"

            # Best available summary
            summary = ""
            if hasattr(book, 'chatbot_metadata') and book.chatbot_metadata:
                summary = (getattr(book.chatbot_metadata, 'short_ai_summary', '')
                           or getattr(book, 'description', ''))
            if not summary:
                summary = getattr(book, 'description', '')

            lines.append(f"**{getattr(book, 'title', 'Unknown')}** — {authors_str}")
            if categories_str:
                lines.append(f"  - Category: {categories_str}")
            lines.append(f"  - Status: {availability}")
            if summary:
                lines.append(f"  - {summary[:200]}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def build_hybrid_chatbot_prompt(
        query: str,
        library_books: list,
        ai_recommendations_enabled: bool = True,
    ) -> str:
        """
        Builds the full hybrid prompt for the chatbot.
        Instructs Gemini to:
          1. Describe the library books (from provided data)
          2. Optionally add a 'Popular Books Worldwide' section from its own knowledge
        """
        library_section = PromptBuilder.build_library_section(library_books)

        book_data_lines = []
        for idx, book in enumerate(library_books, start=1):
            try:
                book_data_lines.append(PromptBuilder._format_book_for_prompt(idx, book))
            except Exception:
                pass
        book_data_str = "\n\n".join(book_data_lines) if book_data_lines else "None"

        ai_instruction = ""
        if ai_recommendations_enabled:
            ai_instruction = (
                "\n\nPART 2 — WORLD KNOWLEDGE RECOMMENDATIONS:\n"
                "After the library section, add a second section titled:"
                " '### [WORLDWIDE] Popular Books Worldwide (May Not Be in Our Library)'\n"
                "In this section, list 5–8 of the most famous, highly regarded books "
                "worldwide that match the user's topic/query, based on your own knowledge.\n"
                "RULES FOR PART 2:\n"
                "- These are AI knowledge-based recommendations ONLY.\n"
                "- Do NOT claim any of these books are in the library.\n"
                "- Do NOT invent availability or shelf information.\n"
                "- End with a disclaimer: "
                "'*Note: These recommendations are based on AI knowledge and are not "
                "guaranteed to be available in our library inventory.*'\n"
            )
        else:
            ai_instruction = (
                "\n\nDo NOT add any recommendations beyond the library books provided above."
            )

        return (
            f"User Question:\n{query}\n\n"
            f"PART 1 — LIBRARY DATABASE RESULTS:\n"
            f"The following books were found in our library database for this query.\n"
            f"Use ONLY this data to describe library availability and details:\n\n"
            f"{book_data_str}\n\n"
            f"Format Part 1 as:\n{library_section}"
            f"{ai_instruction}"
        )

    @staticmethod
    def build_chatbot_user_message(query: str, candidate_books) -> str:
        books_list = list(candidate_books)
        if not books_list:
            return (
                f"User Question:\n{query}\n\n"
                "IMPORTANT: No matching books were found in the current library database.\n"
                "You MUST respond with exactly: \'No matching books were found in the current library database.\'\n"
                "Do NOT suggest, invent, or hallucinate any book titles."
            )

        book_blocks = []
        for idx, book in enumerate(books_list, start=1):
            try:
                book_blocks.append(PromptBuilder._format_book_for_prompt(idx, book))
            except Exception as e:
                logger.warning(f"Error formatting book {getattr(book, 'id', 'unknown')} for prompt: {e}")

        books_context = "\n\n".join(book_blocks)
        return (
            f"User Question:\n{query}\n\n"
            f"Books available in the library database:\n\n"
            f"{books_context}\n\n"
            f"RULES:\n"
            f"- Recommend ONLY from the books listed above.\n"
            f"- NEVER invent, suggest, or hallucinate any book not in the list above.\n"
            f"- If the listed books do not match the user's request, say so clearly.\n"
            f"- Format your response using markdown."
        )

    @staticmethod
    def build_recommendation_system_prompt() -> str:
        return (
            "You are the Library Recommendation Engine. Your job is to rank the candidate books provided "
            "by the system based on the user's preferences, mood, difficulty, and query. "
            "CRITICAL: You must ONLY rank and return books from the candidate list provided to you. Do NOT add, "
            "suggest, or hallucinate any other books outside the candidate list. "
            "Format your response as a detailed, ranked list of books. "
            "Explain the reason why each book was chosen or ranked, referencing user preferences. "
            "Structure your output with clear rankings, e.g., '1. Book Title (ID: X) - Reason'."
        )

    @staticmethod
    def build_recommendation_user_message(
        query: str,
        candidate_books,
        user_profile=None,
        preference_profile: dict | None = None,
        recently_borrowed_ids: list | None = None,
    ) -> str:
        # Membership-level context
        membership_str = "None specified"
        if user_profile:
            membership_str = f"Membership: {user_profile.membership_type} | Department: {user_profile.department or 'N/A'}"

        # Learned preference context
        pref_str = "No preference history available yet."
        if preference_profile:
            pref_str = UserPreferenceService.format_for_prompt(preference_profile)

        # Borrow history note (to avoid re-recommending)
        avoid_note = ""
        if recently_borrowed_ids:
            avoid_note = (
                f"\nNote: The user has already borrowed books with IDs {recently_borrowed_ids[:10]}. "
                "Prefer recommending books they haven't read yet, but still rank them if they are the best match."
            )

        books_list = list(candidate_books)
        if not books_list:
            return (
                f"User Request: \"{query}\"\n\n"
                "IMPORTANT: No matching books were found in the current library database.\n"
                "You MUST respond with: \'No matching books were found in the current library database.\'\n"
                "Do NOT suggest, invent, or hallucinate any book titles."
            )

        book_blocks = []
        for idx, book in enumerate(books_list, start=1):
            try:
                book_blocks.append(PromptBuilder._format_book_for_prompt(idx, book))
            except Exception as e:
                logger.warning(f"Error formatting book {getattr(book, 'id', 'unknown')} for recommendation context: {e}")

        books_context = "\n\n".join(book_blocks)
        return (
            f"User Request: \"{query}\"\n"
            f"User Profile — {membership_str}\n"
            f"User Preference Profile:\n{pref_str}{avoid_note}\n\n"
            f"Candidate Books in the library database:\n\n{books_context}\n\n"
            f"RULES:\n"
            f"- Rank and recommend ONLY books from the list above.\n"
            f"- NEVER invent or hallucinate books outside the candidate list.\n"
            f"- For each book: provide rank, title, and a 2-3 sentence personalised explanation.\n"
            f"- Consider genre, difficulty, mood, and availability."
        )

    @staticmethod
    def detect_intent(message: str) -> str:
        """Detects the chatbot intent from the user message for specialised prompt routing."""
        msg = message.lower()
        if any(w in msg for w in ['compare', 'vs', 'versus', 'difference between']):
            return 'compare'
        if any(w in msg for w in ['summarize', 'summarise', 'summary', 'what is', 'tell me about']):
            return 'summarize'
        if any(w in msg for w in ['available', 'borrow now', 'on shelf', 'borrowable']):
            return 'available_only'
        if any(w in msg for w in ['beginner', 'starter', 'introductory', 'easy', 'simple']):
            return 'beginner'
        if any(w in msg for w in ['advanced', 'expert', 'difficult', 'complex', 'deep dive']):
            return 'advanced'
        if any(w in msg for w in ['by author', 'written by', 'books by']):
            return 'by_author'
        if any(w in msg for w in ['alternative', 'similar to', 'like', 'same as']):
            return 'alternative'
        return 'general'


# ---------------------------------------------------------------------------
# Search Service
# ---------------------------------------------------------------------------

class SearchService:
    """
    Performs ranked keyword-based search across all book fields.
    Uses keyword extraction to strip filler words and ranks results by
    field priority: Title (5) > Category (4) > Tag (3) > Author (2) > Description/Other (1).
    """

    # Common filler words that should be stripped before searching
    STOP_WORDS = {
        'recommend', 'suggest', 'give', 'show', 'find', 'get', 'list',
        'me', 'us', 'my', 'i', 'we', 'you', 'your',
        'a', 'an', 'the', 'some', 'any',
        'for', 'about', 'on', 'in', 'of', 'to', 'by', 'with', 'from', 'and', 'or',
        'book', 'books', 'novel', 'novels', 'read', 'reading',
        'please', 'want', 'need', 'looking', 'like', 'good', 'best', 'top',
        'can', 'could', 'would', 'should', 'have', 'has', 'is', 'are', 'that',
    }

    @staticmethod
    def extract_keywords(query_str: str) -> list[str]:
        """
        Strips filler/stop words from the query and returns meaningful keywords.
        Always returns at least the longest meaningful word if all words are filtered.
        """
        words = query_str.lower().strip().split()
        keywords = [w for w in words if w not in SearchService.STOP_WORDS and len(w) > 1]
        # Fallback: if all words were stop words, use the original words minus very short ones
        if not keywords:
            keywords = [w for w in words if len(w) > 2]
        return keywords

    @staticmethod
    def search_books(query_str: str, limit: int = 10):
        """
        Performs keyword-extracted, ranked search across all book fields.
        Annotates a separate relevance score per keyword and sums them so that
        books matching ALL keywords rank highest over books matching only one.
        Falls back to recent books if query is empty.
        """
        if not query_str or not query_str.strip():
            logger.info("[SearchService] Empty query — returning recent books")
            return list(Book.objects.select_related(
                'publisher', 'recommendation_metadata', 'chatbot_metadata'
            ).prefetch_related('authors', 'categories', 'tags')[:limit])

        keywords = SearchService.extract_keywords(query_str)
        logger.info(f"[SearchService] Raw query: '{query_str}'")
        logger.info(f"[SearchService] Extracted keywords: {keywords}")

        if not keywords:
            logger.warning("[SearchService] No keywords after filtering. Returning recent books.")
            return list(Book.objects.select_related(
                'publisher', 'recommendation_metadata', 'chatbot_metadata'
            ).prefetch_related('authors', 'categories', 'tags')[:limit])

        # Build filter: a book must match at least one keyword in at least one field
        filter_q = Q()
        for kw in keywords:
            filter_q |= (
                Q(title__icontains=kw) |
                Q(subtitle__icontains=kw) |
                Q(description__icontains=kw) |
                Q(authors__first_name__icontains=kw) |
                Q(authors__last_name__icontains=kw) |
                Q(publisher__name__icontains=kw) |
                Q(isbn__icontains=kw) |
                Q(categories__name__icontains=kw) |
                Q(tags__name__icontains=kw) |
                Q(recommendation_metadata__subjects__icontains=kw) |
                Q(recommendation_metadata__keywords__icontains=kw) |
                Q(recommendation_metadata__difficulty_level__icontains=kw) |
                Q(recommendation_metadata__mood__icontains=kw) |
                Q(recommendation_metadata__writing_style__icontains=kw) |
                Q(recommendation_metadata__target_audience__icontains=kw) |
                Q(recommendation_metadata__recommendation_keywords__icontains=kw)
            )

        # Annotate a separate relevance score per keyword, summed together.
        # Books matching ALL keywords get a much higher combined score.
        qs = Book.objects.filter(filter_q)
        total_score_cases = []
        for kw in keywords:
            # Each keyword contributes its own weighted Case/When score
            total_score_cases += [
                When(title__icontains=kw, then=Value(5)),
                When(categories__name__icontains=kw, then=Value(4)),
                When(tags__name__icontains=kw, then=Value(3)),
                When(authors__first_name__icontains=kw, then=Value(2)),
                When(authors__last_name__icontains=kw, then=Value(2)),
                When(subtitle__icontains=kw, then=Value(1)),
                When(description__icontains=kw, then=Value(1)),
                When(publisher__name__icontains=kw, then=Value(1)),
                When(isbn__icontains=kw, then=Value(1)),
                When(recommendation_metadata__subjects__icontains=kw, then=Value(1)),
                When(recommendation_metadata__keywords__icontains=kw, then=Value(1)),
                When(recommendation_metadata__difficulty_level__icontains=kw, then=Value(2)),
                When(recommendation_metadata__mood__icontains=kw, then=Value(1)),
            ]

        queryset = (
            qs
            .annotate(relevance=Case(*total_score_cases, default=Value(0), output_field=IntegerField()))
            .select_related('publisher', 'recommendation_metadata', 'chatbot_metadata')
            .prefetch_related('authors', 'categories', 'tags')
            .order_by('-relevance')
            .distinct()
        )

        seen_ids = set()
        unique_results = []
        for b in queryset[:limit * 2]:  # Fetch extra to cover duplicates
            if b.id not in seen_ids:
                seen_ids.add(b.id)
                unique_results.append(b)
            if len(unique_results) >= limit:
                break
        results = unique_results
        titles = [b.title for b in results]
        logger.info(f"[SearchService] Books found: {len(titles)}")
        logger.info(f"[SearchService] Book list: {titles}")
        return results


# ---------------------------------------------------------------------------
# Recommendation Service
# ---------------------------------------------------------------------------

class RecommendationService:
    """
    Coordinates candidate book retrieval, user preference profiling,
    prompt building with rich context, and Gemini-powered ranking.
    """

    def __init__(self):
        self.ai_service = GeminiService()

    def get_recommendations(self, query: str, user, limit: int = 10) -> tuple[str, list]:
        """
        Returns (response_text: str, candidates: list[Book]).
        Candidates is ALWAYS a plain Python list — never a QuerySet.
        This prevents AttributeError from calling .exists() on a list.
        """
        # 1. Build user preference profile from history
        try:
            preference_profile = UserPreferenceService.get_profile(user)
        except Exception as e:
            logger.warning(f"[RecommendationService] Could not build preference profile: {e}")
            preference_profile = {}

        # 2. Enrich query with user preferences for better search
        enriched_query = query
        if preference_profile.get('favorite_categories'):
            enriched_query += " " + " ".join(preference_profile['favorite_categories'][:2])
        if preference_profile.get('favorite_tags'):
            enriched_query += " " + " ".join(preference_profile['favorite_tags'][:2])

        # 3. Search DB — search_books always returns a list
        candidates: list = SearchService.search_books(enriched_query, limit=limit)
        logger.info(f"[RecommendationService] candidates type={type(candidates).__name__}, count={len(candidates)}")

        # Fallback to raw query if enriched search yielded nothing
        if not candidates:
            logger.info("[RecommendationService] Enriched search empty — retrying with raw query")
            candidates = SearchService.search_books(query, limit=limit)
            logger.info(f"[RecommendationService] Fallback candidates count={len(candidates)}")

        # 4. Read hybrid toggle
        ai_recs_enabled: bool = getattr(settings, 'CHATBOT_AI_RECOMMENDATIONS_ENABLED', True)

        # 5. If no library books found at all, still provide AI world recs if enabled
        if not candidates:
            logger.info("[RecommendationService] No library books found for query.")
            if ai_recs_enabled:
                response_text = self._build_hybrid_response(
                    query=query,
                    library_books=[],
                    user_profile=getattr(user, 'profile', None),
                    preference_profile=preference_profile,
                )
            else:
                response_text = (
                    "I couldn't find any books in our library database that match your query. "
                    "AI recommendations are currently disabled."
                )
            RecommendationHistory.objects.create(user=user, query=query, response=response_text)
            return response_text, []

        # 6. Build prompt and call Gemini with hybrid output
        response_text = self._build_hybrid_response(
            query=query,
            library_books=candidates,
            user_profile=getattr(user, 'profile', None),
            preference_profile=preference_profile,
            recently_borrowed_ids=preference_profile.get('recently_borrowed_ids', []),
            ai_recs_enabled=ai_recs_enabled,
        )

        # 7. Persist to RecommendationHistory
        history = RecommendationHistory.objects.create(
            user=user, query=query, response=response_text
        )
        history.recommended_books.set(candidates)

        return response_text, candidates

    def _build_hybrid_response(
        self,
        query: str,
        library_books: list,
        user_profile=None,
        preference_profile: dict | None = None,
        recently_borrowed_ids: list | None = None,
        ai_recs_enabled: bool = True,
    ) -> str:
        """
        Calls Gemini once to produce a hybrid response:
        Section 1 - Library books (from DB data only)
        Section 2 - World recommendations (Gemini knowledge, if enabled)
        """
        preference_profile = preference_profile or {}
        recently_borrowed_ids = recently_borrowed_ids or []

        # Membership-level context
        membership_str = "None specified"
        if user_profile:
            membership_str = (
                f"Membership: {user_profile.membership_type} | "
                f"Department: {user_profile.department or 'N/A'}"
            )

        pref_str = UserPreferenceService.format_for_prompt(preference_profile) if preference_profile else "No preference history."
        avoid_note = ""
        if recently_borrowed_ids:
            avoid_note = (
                f"\nNote: User already borrowed IDs {recently_borrowed_ids[:10]}. "
                "Prefer books they haven't read yet."
            )

        system_prompt = PromptBuilder.build_recommendation_system_prompt()
        user_message = PromptBuilder.build_hybrid_chatbot_prompt(
            query=query,
            library_books=library_books,
            ai_recommendations_enabled=ai_recs_enabled,
        )
        # Prepend user profile context to the user message
        user_message = (
            f"User Profile — {membership_str}\n"
            f"Preferences: {pref_str}{avoid_note}\n\n"
        ) + user_message

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return self.ai_service.call_gemini(messages)


# ---------------------------------------------------------------------------
# Chatbot Engine
# ---------------------------------------------------------------------------

class ChatbotEngine:
    """
    Manages chatbot sessions with intent detection, smart context injection,
    and personalised responses grounded in the library database.
    """

    def __init__(self):
        self.ai_service = GeminiService()

    # Intent-specific system prompt addenda
    INTENT_INSTRUCTIONS = {
        'compare': (
            "The user wants to COMPARE two or more books. "
            "Structure your answer as a side-by-side comparison covering: difficulty, writing style, "
            "target audience, and which type of reader each book suits best."
        ),
        'summarize': (
            "The user wants a SUMMARY of a specific book. "
            "Provide: 1) a concise 2-3 sentence plot/content summary, "
            "2) who this book is for, 3) one key takeaway."
        ),
        'available_only': (
            "The user wants books that are CURRENTLY AVAILABLE to borrow. "
            "Only include books from the candidate list that have available_copies > 0."
        ),
        'beginner': (
            "The user is a BEGINNER. Prioritise books marked as 'Beginner' or 'Introductory' difficulty. "
            "Briefly explain why each is good for someone just starting out."
        ),
        'advanced': (
            "The user wants ADVANCED material. Prioritise books with 'Advanced' or 'Expert' difficulty. "
            "Explain what background knowledge helps before reading each."
        ),
        'by_author': (
            "The user is looking for books BY A SPECIFIC AUTHOR. "
            "List all matching books in the candidate list by that author, with a brief description of each."
        ),
        'alternative': (
            "The user wants ALTERNATIVES or SIMILAR books to one they mentioned. "
            "Suggest the most thematically and stylistically similar books from the candidate list "
            "and explain specifically what makes them similar."
        ),
        'general': '',
    }

    def get_chatbot_response(self, user, session: ChatSession, message_content: str):
        logger.info(f"[ChatbotEngine] ===== New Request =====")
        logger.info(f"[ChatbotEngine] User query: '{message_content}'")

        # Read the hybrid recommendations toggle from settings
        ai_recs_enabled = getattr(settings, 'CHATBOT_AI_RECOMMENDATIONS_ENABLED', True)

        # 1. Detect intent
        intent = PromptBuilder.detect_intent(message_content)
        logger.info(f"[ChatbotEngine] Detected intent: {intent}")

        # 2. Save user's message to database
        ChatMessage.objects.create(
            session=session,
            sender=ChatMessage.SenderRole.USER,
            content=message_content
        )

        # 3. Search library DB for relevant books
        candidates = SearchService.search_books(message_content, limit=8)
        candidates_list = list(candidates)

        # For 'available_only' intent, only show books on shelf
        if intent == 'available_only':
            candidates_list = [b for b in candidates_list if b.available_copies > 0]
            logger.info(f"[ChatbotEngine] After availability filter: {len(candidates_list)} books")

        logger.info(f"[ChatbotEngine] Library books found: {len(candidates_list)}")
        logger.info(f"[ChatbotEngine] Titles: {[b.title for b in candidates_list]}")

        # 4. Build system prompt
        system_content = PromptBuilder.build_chatbot_system_prompt()
        intent_addendum = self.INTENT_INSTRUCTIONS.get(intent, '')
        if intent_addendum:
            system_content += f"\n\n{intent_addendum}"

        # 5. Build conversation history (last 10 turns)
        previous_messages = session.messages.all().order_by('created_at')
        messages = [{"role": "system", "content": system_content}]
        history_msgs = list(previous_messages)[:-1]
        for msg in history_msgs[-10:]:
            role = "user" if msg.sender == ChatMessage.SenderRole.USER else "assistant"
            messages.append({"role": role, "content": msg.content})

        # 6. Build the hybrid prompt (library section + AI world recommendations instruction)
        formatted_user_msg = PromptBuilder.build_hybrid_chatbot_prompt(
            query=message_content,
            library_books=candidates_list,
            ai_recommendations_enabled=ai_recs_enabled,
        )
        messages.append({"role": "user", "content": formatted_user_msg})

        logger.info(f"[ChatbotEngine] AI recommendations enabled: {ai_recs_enabled}")
        logger.info(f"[ChatbotEngine] Prompt preview:\n{formatted_user_msg[:600]}...")

        # 7. Call Gemini — one call produces the full hybrid response
        bot_response = self.ai_service.call_gemini(messages)

        # 8. Persist assistant response
        ChatMessage.objects.create(
            session=session,
            sender=ChatMessage.SenderRole.ASSISTANT,
            content=bot_response
        )

        # Set session title from first message
        if not session.title:
            session.title = message_content[:50]
            session.save()

        return bot_response
