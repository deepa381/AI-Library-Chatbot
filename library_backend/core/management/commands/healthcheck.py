import os
import sys
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
from django.conf import settings
from django.core.management import call_command
from io import StringIO
from core.gemini_utils import GeminiUtils

class Command(BaseCommand):
    help = 'Checks the health of the Library Chatbot project'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting comprehensive health check...\n")
        failures = 0
        
        # 1. Environment variables
        self.stdout.write("1. Checking Environment Variables...")
        env_vars = ['SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS', 'GEMINI_API_KEY', 'DATABASE_URL']
        for var in env_vars:
            if not os.getenv(var):
                self.stdout.write(self.style.ERROR(f"  [FAIL] {var} is missing in .env"))
                failures += 1
            else:
                self.stdout.write(self.style.SUCCESS(f"  [OK] {var} is present"))

        # 2. Database connection
        self.stdout.write("\n2. Checking Database Connection...")
        db_conn = connections['default']
        try:
            db_conn.cursor()
            self.stdout.write(self.style.SUCCESS("  [OK] Database connected successfully"))
        except OperationalError as e:
            self.stdout.write(self.style.ERROR(f"  [FAIL] Database connection failed: {e}"))
            failures += 1

        # 3. Pending migrations
        self.stdout.write("\n3. Checking Pending Migrations...")
        out = StringIO()
        try:
            call_command('showmigrations', stdout=out)
            if '[ ]' in out.getvalue():
                self.stdout.write(self.style.ERROR("  [FAIL] Unapplied migrations found. Run 'python manage.py migrate'"))
                failures += 1
            else:
                self.stdout.write(self.style.SUCCESS("  [OK] All migrations applied"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  [FAIL] Could not check migrations: {e}"))
            failures += 1

        # 4. Gemini API & Model Availability
        self.stdout.write("\n4. Checking Gemini API Connectivity & Model Availability...")
        if not os.getenv('GEMINI_API_KEY'):
            self.stdout.write(self.style.ERROR("  [SKIP] Skipping Gemini check due to missing API key"))
            failures += 1
        else:
            try:
                model = GeminiUtils.get_available_model()
                self.stdout.write(self.style.SUCCESS(f"  [OK] Gemini API is reachable. Selected model: {model}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [FAIL] Gemini API connectivity failed: {e}"))
                failures += 1

        # 5. Dataset availability
        self.stdout.write("\n5. Checking Dataset Directory...")
        dataset_dir = os.path.join(settings.BASE_DIR, 'dataset')
        if not os.path.exists(dataset_dir):
            self.stdout.write(self.style.WARNING("  [WARN] Dataset directory 'dataset/' is missing. Create one or run import_datasets command to generate samples."))
        else:
            csv_files = [f for f in os.listdir(dataset_dir) if f.endswith('.csv')]
            if not csv_files:
                self.stdout.write(self.style.WARNING("  [WARN] No CSV files found in 'dataset/'. Run import_datasets to generate samples."))
            else:
                self.stdout.write(self.style.SUCCESS(f"  [OK] Found {len(csv_files)} CSV files in 'dataset/'"))

        # 6. Static and Media directories
        self.stdout.write("\n6. Checking Static and Media directories...")
        for name, path in [("STATIC_ROOT", settings.STATIC_ROOT), ("MEDIA_ROOT", settings.MEDIA_ROOT)]:
            if path and os.path.exists(path):
                self.stdout.write(self.style.SUCCESS(f"  [OK] {name} exists at {path}"))
            else:
                self.stdout.write(self.style.WARNING(f"  [WARN] {name} directory does not exist at {path} (expected for development but needed in production)"))

        self.stdout.write("\n--- Health Check Summary ---")
        if failures == 0:
            self.stdout.write(self.style.SUCCESS(f"Project is HEALTHY! 0 critical failures."))
        else:
            self.stdout.write(self.style.ERROR(f"Project has {failures} critical failures. Please fix them before proceeding."))
