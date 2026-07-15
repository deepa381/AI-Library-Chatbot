from django.apps import AppConfig
import sys

class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # Prevent validation during management commands except runserver/healthcheck
        if not any(cmd in sys.argv for cmd in ['runserver', 'healthcheck', 'wsgi', 'gunicorn']):
            return

        import os
        from django.core.exceptions import ImproperlyConfigured
        from django.db import connections
        from django.db.utils import OperationalError
        import logging
        
        logger = logging.getLogger(__name__)
        
        # In Django > 3.2, sometimes ready() is called twice with runserver, we just log once or raise.
        errors = []
        
        if not os.getenv('SECRET_KEY'):
            errors.append("SECRET_KEY environment variable is missing.")
            
        if not os.getenv('GEMINI_API_KEY'):
            errors.append("GEMINI_API_KEY environment variable is missing.")
            
        # Check database connection
        try:
            db_conn = connections['default']
            db_conn.cursor()
        except OperationalError:
            errors.append("Database connection failed. Ensure the database is accessible.")

        # Check Gemini API connectivity
        try:
            if os.getenv('GEMINI_API_KEY'):
                from .gemini_utils import GeminiUtils
                # This will list models and cache the available one
                model = GeminiUtils.get_available_model()
        except Exception as e:
            errors.append(f"Gemini API connectivity failed: {e}")
            
        if errors:
            error_msg = "\nSTARTUP VALIDATION FAILED:\n" + "\n".join([f"- {e}" for e in errors]) + "\nPlease fix these issues before starting the server."
            logger.error(error_msg)
            raise ImproperlyConfigured(error_msg)
