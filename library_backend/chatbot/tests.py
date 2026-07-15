"""
Comprehensive tests for the AI Backend Layer.

Tests cover:
  - SearchService (keyword extraction, multi-field ranked search)
  - PromptBuilder (hybrid prompt construction)
  - GeminiService (mocked — never calls real API)
  - RecommendationService (candidates always list, hybrid output)
  - ChatbotEngine (hybrid pipeline)
  - Chat/Search/Recommend API endpoints
  - Permission enforcement (unauthenticated blocked)
"""

from unittest.mock import patch, MagicMock, PropertyMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from books.models import Book, Author, Publisher, Category, Tag
from recommendation.models import RecommendationMetadata, RecommendationHistory
from chatbot.models import ChatSession, ChatMessage
from chatbot.services import (
    GeminiService,
    PromptBuilder,
    SearchService,
    RecommendationService,
    ChatbotEngine,
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def create_test_user(username="testuser", password="testpass123"):
    return User.objects.create_user(username=username, password=password)


def create_test_book(
    title="Test Book",
    isbn="9780000000001",
    description="A test book about Python programming",
    available_copies=2,
    category_name="Technology",
    tag_name="python",
):
    publisher = Publisher.objects.get_or_create(name="Test Publisher")[0]
    author = Author.objects.get_or_create(first_name="Test", last_name="Author")[0]
    book = Book(
        isbn=isbn,
        title=title,
        subtitle="A subtitle",
        description=description,
        publication_year=2023,
        total_copies=3,
        available_copies=available_copies,
        publisher=publisher,
    )
    book.save()
    book.authors.add(author)
    cat = Category.objects.get_or_create(name=category_name, slug=category_name.lower())[0]
    book.categories.add(cat)
    tag = Tag.objects.get_or_create(name=tag_name, slug=tag_name.lower())[0]
    book.tags.add(tag)
    return book


# ─────────────────────────────────────────────
# SearchService Tests
# ─────────────────────────────────────────────

class SearchServiceTests(TestCase):

    def setUp(self):
        self.book1 = create_test_book("Clean Code", isbn="9780132350884")
        self.book2 = create_test_book(
            "Design Patterns", isbn="9780201633610",
            description="Design patterns in object-oriented programming",
            tag_name="design",
        )

    # Return type contract ---------------------------------------------------

    def test_search_always_returns_list(self):
        """search_books MUST always return a Python list, never a QuerySet."""
        result = SearchService.search_books("Clean Code")
        self.assertIsInstance(result, list, "search_books must return a list")

    def test_empty_query_returns_list(self):
        result = SearchService.search_books("")
        self.assertIsInstance(result, list)

    def test_no_match_returns_empty_list(self):
        result = SearchService.search_books("xyzzyunlikelytermqqqq12345")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    # Keyword extraction -----------------------------------------------------

    def test_extract_keywords_removes_stop_words(self):
        kws = SearchService.extract_keywords("recommend me a beginner Python book")
        self.assertNotIn("recommend", kws)
        self.assertNotIn("me", kws)
        self.assertNotIn("a", kws)
        self.assertNotIn("book", kws)
        self.assertIn("beginner", kws)
        self.assertIn("python", kws)

    def test_extract_keywords_fallback_when_all_filtered(self):
        """If all words are stop words, fallback to words > 2 chars."""
        kws = SearchService.extract_keywords("a an the")
        self.assertIsInstance(kws, list)
        # "the" (len 3) should survive
        self.assertIn("the", kws)

    def test_extract_keywords_returns_list(self):
        kws = SearchService.extract_keywords("python machine learning")
        self.assertIsInstance(kws, list)

    # Field matching ---------------------------------------------------------

    def test_search_by_title(self):
        results = SearchService.search_books("Clean Code")
        self.assertTrue(any(b.title == "Clean Code" for b in results))

    def test_search_by_description(self):
        results = SearchService.search_books("Python programming")
        self.assertTrue(any(b.title == "Clean Code" for b in results))

    def test_search_by_author_last_name(self):
        results = SearchService.search_books("Author")
        self.assertGreaterEqual(len(results), 1)

    def test_search_by_category(self):
        results = SearchService.search_books("Technology")
        self.assertGreaterEqual(len(results), 1)

    def test_search_by_tag(self):
        results = SearchService.search_books("python")
        self.assertGreaterEqual(len(results), 1)

    # Ranking ----------------------------------------------------------------

    def test_title_match_ranks_higher_than_description_match(self):
        """Book whose title matches should come before one where only desc matches."""
        title_book = create_test_book(
            "Python Fluent", isbn="9780000000010",
            description="General programming guide",
            tag_name="general",
        )
        desc_book = create_test_book(
            "General Computing", isbn="9780000000011",
            description="A guide covering python syntax and semantics",
            tag_name="computing",
        )
        results = SearchService.search_books("python", limit=10)
        titles = [b.title for b in results]
        if "Python Fluent" in titles and "General Computing" in titles:
            self.assertLess(
                titles.index("Python Fluent"),
                titles.index("General Computing"),
                "Title match should rank higher than description-only match",
            )

    # Deduplication ----------------------------------------------------------

    def test_no_duplicate_books_in_results(self):
        results = SearchService.search_books("python programming")
        ids = [b.id for b in results]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate books returned by search_books")

    # Limit ------------------------------------------------------------------

    def test_limit_is_respected(self):
        for i in range(12):
            create_test_book(f"Limit Test Book {i}", isbn=f"978000001{i:04d}")
        results = SearchService.search_books("Limit Test Book", limit=5)
        self.assertLessEqual(len(results), 5)

    # Recommendation metadata ------------------------------------------------

    def test_search_recommendation_metadata_mood(self):
        book = create_test_book("Mood Book", isbn="9780000000099")
        RecommendationMetadata.objects.create(
            book=book, mood="inspirational", difficulty_level="beginner",
        )
        results = SearchService.search_books("inspirational")
        self.assertTrue(any(b.id == book.id for b in results))


# ─────────────────────────────────────────────
# PromptBuilder Tests
# ─────────────────────────────────────────────

class PromptBuilderTests(TestCase):

    def setUp(self):
        self.book = create_test_book("The Pragmatic Programmer", isbn="9780135957059")

    def test_chatbot_system_prompt_contains_critical_rules(self):
        prompt = PromptBuilder.build_chatbot_system_prompt()
        self.assertIn("CRITICAL", prompt)
        self.assertIn("invent", prompt.lower())

    def test_recommendation_system_prompt_anti_hallucination(self):
        prompt = PromptBuilder.build_recommendation_system_prompt()
        self.assertIn("CRITICAL", prompt)
        self.assertIn("candidate list", prompt)

    # Hybrid prompt ----------------------------------------------------------

    def test_hybrid_prompt_with_books_contains_library_section(self):
        books = [self.book]
        prompt = PromptBuilder.build_hybrid_chatbot_prompt(
            "Python book", books, ai_recommendations_enabled=True
        )
        self.assertIn("LIBRARY DATABASE RESULTS", prompt)
        self.assertIn("The Pragmatic Programmer", prompt)
        self.assertIn("WORLD KNOWLEDGE", prompt)

    def test_hybrid_prompt_empty_library_shows_no_match_notice(self):
        prompt = PromptBuilder.build_hybrid_chatbot_prompt(
            "kubernetes", [], ai_recommendations_enabled=True
        )
        self.assertIn("No matching books are currently available", prompt)
        self.assertIn("WORLD KNOWLEDGE", prompt)

    def test_hybrid_prompt_ai_disabled_no_world_section(self):
        books = [self.book]
        prompt = PromptBuilder.build_hybrid_chatbot_prompt(
            "Python book", books, ai_recommendations_enabled=False
        )
        self.assertNotIn("PART 2 — WORLD KNOWLEDGE", prompt)

    def test_library_section_shows_availability_status(self):
        section = PromptBuilder.build_library_section([self.book])
        self.assertIn("[AVAILABLE]", section)

    def test_library_section_empty_shows_notice(self):
        section = PromptBuilder.build_library_section([])
        self.assertIn("No matching books", section)

    # build_chatbot_user_message (legacy path) -------------------------------

    def test_chatbot_user_message_empty_books_no_hallucination_instruction(self):
        msg = PromptBuilder.build_chatbot_user_message("any query", [])
        self.assertIn("MUST respond", msg)
        self.assertIn("hallucinate", msg.lower())


# ─────────────────────────────────────────────
# GeminiService Tests (fully mocked)
# ─────────────────────────────────────────────

class GeminiServiceTests(TestCase):

    @patch('chatbot.services.GeminiUtils.get_client')
    @patch('chatbot.services.GeminiUtils.get_available_model')
    def test_call_gemini_returns_text(self, mock_model, mock_client):
        mock_model.return_value = "gemini-flash-latest"
        mock_response = MagicMock()
        mock_response.text = "Gemini test response"
        mock_client.return_value.models.generate_content.return_value = mock_response

        service = GeminiService()
        result = service.call_gemini([{"role": "user", "content": "Hello"}])
        self.assertEqual(result, "Gemini test response")

    @patch('chatbot.services.GeminiUtils.get_client')
    def test_call_gemini_without_client_returns_error_message(self, mock_client):
        mock_client.side_effect = Exception("No client")
        service = GeminiService()
        result = service.call_gemini([{"role": "user", "content": "Hello"}])
        self.assertIn("error", result.lower())


# ─────────────────────────────────────────────
# RecommendationService Tests
# ─────────────────────────────────────────────

class RecommendationServiceTests(TestCase):

    def setUp(self):
        self.user = create_test_user("recuser")
        self.service = RecommendationService()

    # ---- Type contract tests -----------------------------------------------

    @patch('chatbot.services.GeminiService.call_gemini')
    def test_get_recommendations_returns_list_not_queryset(self, mock_gemini):
        """candidates in the return value MUST always be a plain list."""
        mock_gemini.return_value = "Recommended books: ..."
        create_test_book("Python Book", isbn="9780000000100")
        _, candidates = self.service.get_recommendations("python", self.user)
        self.assertIsInstance(candidates, list,
                              "get_recommendations must return list, not QuerySet")

    @patch('chatbot.services.GeminiService.call_gemini')
    def test_candidates_list_has_no_exists_method(self, mock_gemini):
        """Ensure candidates is a list — lists do not have .exists()."""
        mock_gemini.return_value = "..."
        create_test_book("Rust Book", isbn="9780000000101", tag_name="rust")
        _, candidates = self.service.get_recommendations("rust", self.user)
        self.assertFalse(
            hasattr(candidates, 'exists'),
            "candidates should be a list, not a QuerySet with .exists()"
        )

    # ---- Empty library results ---------------------------------------------

    @patch('chatbot.services.GeminiService.call_gemini')
    @override_settings(CHATBOT_AI_RECOMMENDATIONS_ENABLED=True)
    def test_empty_library_with_ai_enabled_still_calls_gemini(self, mock_gemini):
        """No library match + AI enabled => Gemini still called for world recs."""
        mock_gemini.return_value = "Popular worldwide books: ..."
        response_text, candidates = self.service.get_recommendations(
            "xyzzyunlikelytermqqqq", self.user
        )
        mock_gemini.assert_called_once()
        self.assertIsInstance(candidates, list)
        self.assertEqual(len(candidates), 0)
        self.assertIsInstance(response_text, str)

    @override_settings(CHATBOT_AI_RECOMMENDATIONS_ENABLED=False)
    def test_empty_library_with_ai_disabled_returns_no_match_message(self):
        """No library match + AI disabled => returns static message, no Gemini call."""
        response_text, candidates = self.service.get_recommendations(
            "xyzzyunlikelytermqqqq", self.user
        )
        self.assertIsInstance(response_text, str)
        self.assertIn("couldn't find", response_text.lower())
        self.assertIn("AI recommendations are currently disabled", response_text)
        self.assertEqual(candidates, [])

    # ---- Non-empty library results -----------------------------------------

    @patch('chatbot.services.GeminiService.call_gemini')
    @override_settings(CHATBOT_AI_RECOMMENDATIONS_ENABLED=True)
    def test_non_empty_library_returns_books_and_ai_response(self, mock_gemini):
        """Library match + AI enabled => returns books list + AI text."""
        mock_gemini.return_value = "Recommended: Fluent Python..."
        create_test_book("Fluent Python", isbn="9780000000200")
        response_text, candidates = self.service.get_recommendations("python", self.user)
        self.assertIsInstance(candidates, list)
        self.assertGreater(len(candidates), 0)
        self.assertIsInstance(response_text, str)
        self.assertEqual(response_text, "Recommended: Fluent Python...")

    @patch('chatbot.services.GeminiService.call_gemini')
    @override_settings(CHATBOT_AI_RECOMMENDATIONS_ENABLED=False)
    def test_non_empty_library_ai_disabled_returns_library_only_response(self, mock_gemini):
        """Library match + AI disabled => Gemini called but no world recs instruction."""
        mock_gemini.return_value = "Library books only response."
        create_test_book("Rust Programming", isbn="9780000000201", tag_name="rust")
        response_text, candidates = self.service.get_recommendations("rust", self.user)
        # Gemini still called for Part 1 formatting
        mock_gemini.assert_called_once()
        self.assertIsInstance(candidates, list)
        self.assertGreater(len(candidates), 0)

    # ---- Persistence -------------------------------------------------------

    @patch('chatbot.services.GeminiService.call_gemini')
    def test_get_recommendations_persists_history(self, mock_gemini):
        mock_gemini.return_value = "Some recommendation."
        create_test_book("Science Book", isbn="9780000000300", tag_name="science")
        self.service.get_recommendations("science", self.user)
        self.assertTrue(RecommendationHistory.objects.filter(user=self.user).exists())

    # ---- Hybrid response text ----------------------------------------------

    @patch('chatbot.services.GeminiService.call_gemini')
    @override_settings(CHATBOT_AI_RECOMMENDATIONS_ENABLED=True)
    def test_hybrid_mode_prompt_contains_world_knowledge_instruction(self, mock_gemini):
        """When AI enabled, the prompt sent to Gemini should contain Part 2 instruction."""
        mock_gemini.return_value = "Hybrid response"
        create_test_book("Django Book", isbn="9780000000400", tag_name="django")
        self.service.get_recommendations("django", self.user)
        call_args = mock_gemini.call_args
        messages = call_args[0][0]
        full_prompt = " ".join(m['content'] for m in messages)
        self.assertIn("WORLD KNOWLEDGE", full_prompt)

    @patch('chatbot.services.GeminiService.call_gemini')
    @override_settings(CHATBOT_AI_RECOMMENDATIONS_ENABLED=False)
    def test_library_only_mode_prompt_has_no_world_knowledge(self, mock_gemini):
        """When AI disabled, the prompt must NOT instruct Gemini to add world recs."""
        mock_gemini.return_value = "Library-only response"
        create_test_book("Flask Book", isbn="9780000000401", tag_name="flask")
        self.service.get_recommendations("flask", self.user)
        call_args = mock_gemini.call_args
        messages = call_args[0][0]
        full_prompt = " ".join(m['content'] for m in messages)
        self.assertNotIn("PART 2", full_prompt)


# ─────────────────────────────────────────────
# ChatbotEngine Tests
# ─────────────────────────────────────────────

class ChatbotEngineTests(TestCase):

    def setUp(self):
        self.user = create_test_user("chatuser")
        self.engine = ChatbotEngine()
        self.session = ChatSession.objects.create(user=self.user)

    @patch('chatbot.services.GeminiService.call_gemini')
    @override_settings(CHATBOT_AI_RECOMMENDATIONS_ENABLED=True)
    def test_response_is_returned(self, mock_gemini):
        mock_gemini.return_value = "Here are some books!"
        create_test_book("Flask Guide", isbn="9780000000500", tag_name="flask")
        response = self.engine.get_chatbot_response(self.user, self.session, "python book")
        self.assertIsInstance(response, str)
        self.assertEqual(response, "Here are some books!")

    @patch('chatbot.services.GeminiService.call_gemini')
    def test_messages_are_persisted(self, mock_gemini):
        mock_gemini.return_value = "Bot says hi"
        self.engine.get_chatbot_response(self.user, self.session, "hello")
        msg_count = ChatMessage.objects.filter(session=self.session).count()
        self.assertEqual(msg_count, 2)  # user message + bot response

    @patch('chatbot.services.GeminiService.call_gemini')
    def test_session_title_set_on_first_message(self, mock_gemini):
        mock_gemini.return_value = "Response"
        self.engine.get_chatbot_response(self.user, self.session, "My first message")
        self.session.refresh_from_db()
        self.assertEqual(self.session.title, "My first message")

    @patch('chatbot.services.GeminiService.call_gemini')
    @override_settings(CHATBOT_AI_RECOMMENDATIONS_ENABLED=True)
    def test_prompt_contains_world_knowledge_instruction_when_enabled(self, mock_gemini):
        mock_gemini.return_value = "Hybrid response"
        self.engine.get_chatbot_response(self.user, self.session, "python book")
        messages = mock_gemini.call_args[0][0]
        full_text = " ".join(m['content'] for m in messages)
        self.assertIn("WORLD KNOWLEDGE", full_text)

    @patch('chatbot.services.GeminiService.call_gemini')
    @override_settings(CHATBOT_AI_RECOMMENDATIONS_ENABLED=False)
    def test_no_world_knowledge_in_prompt_when_disabled(self, mock_gemini):
        mock_gemini.return_value = "Library only"
        self.engine.get_chatbot_response(self.user, self.session, "python book")
        messages = mock_gemini.call_args[0][0]
        # Only check the user message content (last message), not the system prompt
        user_message_content = messages[-1]['content']
        self.assertNotIn("PART 2", user_message_content)


# ─────────────────────────────────────────────
# API Endpoint Tests
# ─────────────────────────────────────────────

class ChatAPITest(TestCase):
    """Test the /api/chat/ endpoint with mocked Gemini."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)
        create_test_book("The Clean Coder", isbn="9780137081073")

    @patch('chatbot.services.GeminiService.call_gemini')
    def test_chat_creates_session_and_returns_response(self, mock_gemini):
        mock_gemini.return_value = "Here is my recommendation!"
        response = self.client.post('/api/chat/', {'message': 'recommend me books'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', response.data)
        self.assertIn('response', response.data)

    @patch('chatbot.services.GeminiService.call_gemini')
    def test_chat_continues_existing_session(self, mock_gemini):
        mock_gemini.return_value = "Second response."
        session = ChatSession.objects.create(user=self.user)
        response = self.client.post(
            '/api/chat/',
            {'message': 'tell me more', 'session_id': str(session.session_id)},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['session_id']), str(session.session_id))

    def test_chat_without_message_returns_400(self):
        response = self.client.post('/api/chat/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chat_with_invalid_session_id_returns_404(self):
        response = self.client.post(
            '/api/chat/',
            {'message': 'hello', 'session_id': '00000000-0000-0000-0000-000000000000'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_chat_unauthenticated_returns_401(self):
        unauthed = APIClient()
        response = unauthed.post('/api/chat/', {'message': 'hi'}, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class SearchAPITest(TestCase):
    """Test the /api/search/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)
        create_test_book("Python Cookbook", isbn="9780596007973")

    def test_search_returns_matching_books(self):
        response = self.client.get('/api/search/?q=Python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(b['title'] == 'Python Cookbook' for b in response.data))

    def test_search_without_query_param_returns_400(self):
        response = self.client.get('/api/search/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_no_results_returns_empty_list(self):
        response = self.client.get('/api/search/?q=xyzzyunlikelytermqqqq')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_search_unauthenticated_returns_401(self):
        unauthed = APIClient()
        response = unauthed.get('/api/search/?q=python')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class RecommendAPITest(TestCase):
    """Test the /api/recommend/ endpoint — never fails due to type mismatch."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)
        create_test_book("Deep Learning", isbn="9780262035613", tag_name="ml")

    @patch('chatbot.services.GeminiService.call_gemini')
    def test_recommend_returns_response_and_books(self, mock_gemini):
        mock_gemini.return_value = "Top picks: Deep Learning."
        response = self.client.post(
            '/api/recommend/', {'query': 'machine learning deep learning'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('response', response.data)
        self.assertIn('books', response.data)

    @patch('chatbot.services.GeminiService.call_gemini')
    def test_recommend_zero_library_results_still_200(self, mock_gemini):
        """Critical: even with 0 library results, endpoint must return 200, not 500."""
        mock_gemini.return_value = "World recommendations: ..."
        response = self.client.post(
            '/api/recommend/', {'query': 'xyzzyunlikelytermqqqq'}, format='json'
        )
        self.assertIn(response.status_code, [status.HTTP_200_OK])
        self.assertIn('response', response.data)
        self.assertEqual(response.data['books'], [])

    def test_recommend_without_query_returns_400(self):
        response = self.client.post('/api/recommend/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recommend_unauthenticated_returns_401(self):
        unauthed = APIClient()
        response = unauthed.post('/api/recommend/', {'query': 'python'}, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    @patch('chatbot.services.GeminiService.call_gemini')
    @override_settings(CHATBOT_AI_RECOMMENDATIONS_ENABLED=False)
    def test_recommend_ai_disabled_returns_library_only(self, mock_gemini):
        """AI disabled: endpoint returns only library books without world recs."""
        mock_gemini.return_value = "Library only."
        response = self.client.post(
            '/api/recommend/', {'query': 'machine learning'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
