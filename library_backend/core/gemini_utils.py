import logging
from django.conf import settings
from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger(__name__)

class GeminiUtils:
    _cached_model = None
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client:
            return cls._client
            
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured in settings.")
        cls._client = genai.Client(api_key=api_key)
        return cls._client

    @classmethod
    def get_available_model(cls):
        if cls._cached_model:
            return cls._cached_model
        
        # We explicitly use the model configured in the environment
        cls._cached_model = getattr(settings, 'GEMINI_MODEL', 'gemini-flash-latest')
        logger.info(f"Using explicitly configured Gemini model: {cls._cached_model}")
        return cls._cached_model
