import os
import re
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.conf import settings

from books.models import Author, Publisher, Category, Tag, Book, validate_isbn, validate_publication_year
from chatbot.models import ChatbotMetadata
from recommendation.models import RecommendationMetadata, SimilarBook

class Command(BaseCommand):
    help = "Imports the complete library dataset from Excel files in a production-grade manner."

    def add_arguments(self, parser):
        parser.add_argument(
            "--directory",
            type=str,
            default=os.path.join(settings.BASE_DIR, "dataset"),
            help="Path to the directory containing Excel files."
        )

    def handle(self, *args, **options):
        directory = options["directory"]
        if not os.path.exists(directory):
            self.stderr.write(self.style.ERROR(f"Directory '{directory}' does not exist."))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(f"Starting import from directory: {directory}"))

        # Mappings from Excel IDs to Database Objects or IDs
        self.publisher_map = {}
        self.author_map = {}
        self.category_map = {}
        self.tag_map = {}
        self.book_map = {}  # excel book_id -> db Book object

        # Report stats
        self.stats = {}
        self.errors = []

        # List of files to process in dependency order
        files_config = [
            ("publishers.xlsx", self.import_publishers),
            ("authors.xlsx", self.import_authors),
            ("categories.xlsx", self.import_categories),
            ("tags.xlsx", self.import_tags),
            ("books.xlsx", self.import_books),
            ("book_authors.xlsx", self.import_book_authors),
            ("book_categories.xlsx", self.import_book_categories),
            ("book_tags.xlsx", self.import_book_tags),
            ("recommendation_metadata.xlsx", self.import_recommendation_metadata),
            ("chatbot_metadata.xlsx", self.import_chatbot_metadata),
            ("similar_books.xlsx", self.import_similar_books),
        ]

        for filename, import_func in files_config:
            file_path = os.path.join(directory, filename)
            if not os.path.exists(file_path):
                self.stdout.write(self.style.WARNING(f"Skipping optional file {filename} (not found)"))
                continue

            self.stdout.write(self.style.NOTICE(f"\nProcessing {filename}..."))
            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to read {filename}: {e}"))
                self.errors.append({"file": filename, "row": "N/A", "error": f"Read failed: {e}"})
                continue

            self.stats[filename] = {"total": len(df), "created": 0, "updated": 0, "failed": 0}
            import_func(df, filename)

        self.print_report()

    # --- HELPER SANITIZATION FUNCTIONS ---
    def clean_str(self, val):
        if pd.isna(val):
            return ""
        if isinstance(val, float):
            if val.is_integer():
                return str(int(val))
        val_str = str(val).strip()
        if val_str.endswith(".0"):
            parts = val_str.split(".")
            if parts[0].isdigit():
                return parts[0]
        return val_str

    def clean_int(self, val, default=None):
        if pd.isna(val):
            return default
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default

    def clean_float(self, val, default=0.0):
        if pd.isna(val):
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def clean_bool(self, val, default=True):
        if pd.isna(val):
            return default
        s = str(val).strip().lower()
        if s in ("true", "1", "yes", "y", "t"):
            return True
        if s in ("false", "0", "no", "n", "f"):
            return False
        return default

    # --- IMPORTER FUNCTIONS ---

    def import_publishers(self, df, filename):
        for idx, row in df.iterrows():
            excel_id = self.clean_str(row.get("id"))
            name = self.clean_str(row.get("name"))

            if not name:
                self.errors.append({"file": filename, "row": idx + 2, "error": "Publisher name is missing."})
                self.stats[filename]["failed"] += 1
                continue

            try:
                with transaction.atomic():
                    publisher, created = Publisher.objects.update_or_create(
                        name=name,
                        defaults={
                            "address": self.clean_str(row.get("address")),
                            "website": self.clean_str(row.get("website")) or None,
                            "email": self.clean_str(row.get("email")) or None,
                            "phone": self.clean_str(row.get("phone")),
                            "is_active": self.clean_bool(row.get("is_active"), True),
                        }
                    )
                    self.publisher_map[excel_id] = publisher
                    if created:
                        self.stats[filename]["created"] += 1
                    else:
                        self.stats[filename]["updated"] += 1
            except Exception as e:
                self.errors.append({"file": filename, "row": idx + 2, "error": str(e)})
                self.stats[filename]["failed"] += 1

    def import_authors(self, df, filename):
        for idx, row in df.iterrows():
            excel_id = self.clean_str(row.get("id"))
            name = self.clean_str(row.get("name"))

            if not name:
                self.errors.append({"file": filename, "row": idx + 2, "error": "Author name is missing."})
                self.stats[filename]["failed"] += 1
                continue

            # Split full name into first and last name
            parts = name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

            try:
                with transaction.atomic():
                    # Parse date of birth if present
                    dob = row.get("date_of_birth")
                    if pd.notna(dob):
                        try:
                            dob = pd.to_datetime(dob).date()
                        except Exception:
                            dob = None

                    author, created = Author.objects.update_or_create(
                        first_name=first_name,
                        last_name=last_name,
                        defaults={
                            "biography": self.clean_str(row.get("biography")),
                            "country": self.clean_str(row.get("country")),
                            "date_of_birth": dob,
                            "website": self.clean_str(row.get("website")) or None,
                            "is_active": self.clean_bool(row.get("is_active"), True),
                        }
                    )
                    self.author_map[excel_id] = author
                    if created:
                        self.stats[filename]["created"] += 1
                    else:
                        self.stats[filename]["updated"] += 1
            except Exception as e:
                self.errors.append({"file": filename, "row": idx + 2, "error": str(e)})
                self.stats[filename]["failed"] += 1

    def import_categories(self, df, filename):
        for idx, row in df.iterrows():
            excel_id = self.clean_str(row.get("id"))
            name = self.clean_str(row.get("name"))

            if not name:
                self.errors.append({"file": filename, "row": idx + 2, "error": "Category name is missing."})
                self.stats[filename]["failed"] += 1
                continue

            slug = slugify(name)
            try:
                with transaction.atomic():
                    # Handle slug collision
                    original_slug = slug
                    count = 2
                    while Category.objects.filter(slug=slug).exclude(name__iexact=name).exists():
                        slug = f"{original_slug}-{count}"
                        count += 1

                    category, created = Category.objects.update_or_create(
                        name__iexact=name,
                        defaults={
                            "name": name,
                            "description": self.clean_str(row.get("description")),
                            "slug": slug,
                        }
                    )
                    self.category_map[excel_id] = category
                    if created:
                        self.stats[filename]["created"] += 1
                    else:
                        self.stats[filename]["updated"] += 1
            except Exception as e:
                self.errors.append({"file": filename, "row": idx + 2, "error": str(e)})
                self.stats[filename]["failed"] += 1

    def import_tags(self, df, filename):
        for idx, row in df.iterrows():
            excel_id = self.clean_str(row.get("id"))
            name = self.clean_str(row.get("name"))

            if not name:
                self.errors.append({"file": filename, "row": idx + 2, "error": "Tag name is missing."})
                self.stats[filename]["failed"] += 1
                continue

            slug = slugify(name)
            try:
                with transaction.atomic():
                    # Handle slug collision
                    original_slug = slug
                    count = 2
                    while Tag.objects.filter(slug=slug).exclude(name__iexact=name).exists():
                        slug = f"{original_slug}-{count}"
                        count += 1

                    tag, created = Tag.objects.update_or_create(
                        name__iexact=name,
                        defaults={
                            "name": name,
                            "slug": slug,
                        }
                    )
                    self.tag_map[excel_id] = tag
                    if created:
                        self.stats[filename]["created"] += 1
                    else:
                        self.stats[filename]["updated"] += 1
            except Exception as e:
                self.errors.append({"file": filename, "row": idx + 2, "error": str(e)})
                self.stats[filename]["failed"] += 1

    def import_books(self, df, filename):
        for idx, row in df.iterrows():
            excel_book_id = self.clean_int(row.get("book_id"))
            isbn_13 = self.clean_str(row.get("isbn_13"))
            isbn_10 = self.clean_str(row.get("isbn_10"))
            isbn = isbn_13 or isbn_10

            if not isbn:
                self.errors.append({"file": filename, "row": idx + 2, "error": f"Book ID {excel_book_id} is missing both ISBN-10 and ISBN-13."})
                self.stats[filename]["failed"] += 1
                continue

            # Standardize and validate ISBN
            isbn_clean = re.sub(r'[-\s]', '', isbn).upper()
            try:
                validate_isbn(isbn_clean)
            except ValidationError as ve:
                self.errors.append({"file": filename, "row": idx + 2, "error": f"Invalid ISBN format: {isbn_clean}. {ve.messages[0]}"})
                self.stats[filename]["failed"] += 1
                continue

            # Validate publication year
            pub_year = self.clean_int(row.get("pub_year"))
            if pub_year is not None:
                try:
                    validate_publication_year(pub_year)
                except ValidationError as ve:
                    self.errors.append({"file": filename, "row": idx + 2, "error": f"Invalid publication year: {pub_year}. {ve.messages[0]}"})
                    self.stats[filename]["failed"] += 1
                    continue
            else:
                self.errors.append({"file": filename, "row": idx + 2, "error": f"Book ID {excel_book_id} has missing publication year."})
                self.stats[filename]["failed"] += 1
                continue

            # Foreign Key check: Publisher
            excel_pub_id = self.clean_str(row.get("publisher_id"))
            publisher_obj = self.publisher_map.get(excel_pub_id)
            if not publisher_obj:
                self.errors.append({"file": filename, "row": idx + 2, "error": f"Publisher ID {excel_pub_id} referenced by book {isbn_clean} not found in imported publishers."})
                self.stats[filename]["failed"] += 1
                continue

            # Sanitize numeric copy fields
            total_copies = max(self.clean_int(row.get("total_copies"), 1), 0)
            available_copies = max(self.clean_int(row.get("available_copies"), 1), 0)
            if available_copies > total_copies:
                available_copies = total_copies

            try:
                with transaction.atomic():
                    # We check if Book already exists with this ISBN
                    book = Book.objects.filter(isbn=isbn_clean).first()
                    created = False
                    if not book:
                        # Attempt to assign the exact primary key from Excel to preserve references
                        if Book.objects.filter(id=excel_book_id).exists():
                            book = Book(isbn=isbn_clean)
                        else:
                            book = Book(id=excel_book_id, isbn=isbn_clean)
                        created = True

                    book.title = self.clean_str(row.get("title"))
                    book.subtitle = self.clean_str(row.get("subtitle"))
                    book.description = self.clean_str(row.get("description"))
                    book.publication_year = pub_year
                    book.edition = self.clean_str(row.get("edition"))
                    
                    lang_code = self.clean_str(row.get("language_code")).upper()
                    # Check choice validity
                    from books.models import BookLanguage
                    if lang_code in dict(BookLanguage.choices):
                        book.language = lang_code
                    else:
                        book.language = BookLanguage.OTHER

                    book.pages = self.clean_int(row.get("num_pages"))
                    book.total_copies = total_copies
                    book.available_copies = available_copies
                    book.average_rating = self.clean_float(row.get("avg_rating"), 0.0)
                    
                    status_val = self.clean_str(row.get("status")).upper()
                    from books.models import BookStatus
                    if status_val in dict(BookStatus.choices):
                        book.status = status_val
                    else:
                        book.status = BookStatus.AVAILABLE

                    book.shelf_location = self.clean_str(row.get("shelf_location"))
                    book.publisher = publisher_obj
                    
                    # Triggers full clean and saves
                    book.save()

                    self.book_map[excel_book_id] = book
                    if created:
                        self.stats[filename]["created"] += 1
                    else:
                        self.stats[filename]["updated"] += 1
            except Exception as e:
                self.errors.append({"file": filename, "row": idx + 2, "error": str(e)})
                self.stats[filename]["failed"] += 1

    def import_book_authors(self, df, filename):
        for idx, row in df.iterrows():
            excel_book_id = self.clean_int(row.get("book_id"))
            excel_author_id = self.clean_str(row.get("author_id"))

            book = self.book_map.get(excel_book_id)
            author = self.author_map.get(excel_author_id)

            if not book or not author:
                self.errors.append({"file": filename, "row": idx + 2, "error": f"FK mismatch: Book {excel_book_id} or Author {excel_author_id} not found."})
                self.stats[filename]["failed"] += 1
                continue

            try:
                with transaction.atomic():
                    if author not in book.authors.all():
                        book.authors.add(author)
                        self.stats[filename]["created"] += 1
                    else:
                        self.stats[filename]["updated"] += 1  # idempotent
            except Exception as e:
                self.errors.append({"file": filename, "row": idx + 2, "error": str(e)})
                self.stats[filename]["failed"] += 1

    def import_book_categories(self, df, filename):
        for idx, row in df.iterrows():
            excel_book_id = self.clean_int(row.get("book_id"))
            excel_cat_id = self.clean_str(row.get("category_id"))

            book = self.book_map.get(excel_book_id)
            category = self.category_map.get(excel_cat_id)

            if not book or not category:
                self.errors.append({"file": filename, "row": idx + 2, "error": f"FK mismatch: Book {excel_book_id} or Category {excel_cat_id} not found."})
                self.stats[filename]["failed"] += 1
                continue

            try:
                with transaction.atomic():
                    if category not in book.categories.all():
                        book.categories.add(category)
                        self.stats[filename]["created"] += 1
                    else:
                        self.stats[filename]["updated"] += 1
            except Exception as e:
                self.errors.append({"file": filename, "row": idx + 2, "error": str(e)})
                self.stats[filename]["failed"] += 1

    def import_book_tags(self, df, filename):
        for idx, row in df.iterrows():
            excel_book_id = self.clean_int(row.get("book_id"))
            excel_tag_id = self.clean_str(row.get("tag_id"))

            book = self.book_map.get(excel_book_id)
            tag = self.tag_map.get(excel_tag_id)

            if not book or not tag:
                self.errors.append({"file": filename, "row": idx + 2, "error": f"FK mismatch: Book {excel_book_id} or Tag {excel_tag_id} not found."})
                self.stats[filename]["failed"] += 1
                continue

            try:
                with transaction.atomic():
                    if tag not in book.tags.all():
                        book.tags.add(tag)
                        self.stats[filename]["created"] += 1
                    else:
                        self.stats[filename]["updated"] += 1
            except Exception as e:
                self.errors.append({"file": filename, "row": idx + 2, "error": str(e)})
                self.stats[filename]["failed"] += 1

    def import_recommendation_metadata(self, df, filename):
        for idx, row in df.iterrows():
            excel_book_id = self.clean_int(row.get("book_id"))
            book = self.book_map.get(excel_book_id)

            if not book:
                self.errors.append({"file": filename, "row": idx + 2, "error": f"Book ID {excel_book_id} not found for recommendation metadata."})
                self.stats[filename]["failed"] += 1
                continue

            try:
                with transaction.atomic():
                    rec_meta, created = RecommendationMetadata.objects.update_or_create(
                        book=book,
                        defaults={
                            "mood": self.clean_str(row.get("mood")),
                            "writing_style": self.clean_str(row.get("writing_style")),
                            "difficulty_level": self.clean_str(row.get("difficulty_level")),
                            "reading_level": self.clean_str(row.get("reading_level")),
                            "target_audience": self.clean_str(row.get("target_audience")),
                            "learning_outcomes": self.clean_str(row.get("learning_outcomes")),
                            "skills_covered": self.clean_str(row.get("skills_covered")),
                            "recommendation_keywords": self.clean_str(row.get("recommendation_keywords")),
                            "fantasy_elements": self.clean_str(row.get("fantasy_elements")),
                            "scifi_elements": self.clean_str(row.get("scifi_elements")),
                            "themes": self.clean_str(row.get("themes")),
                            "keywords": self.clean_str(row.get("keywords")),
                            "tags": self.clean_str(row.get("tags")),
                            "subjects": self.clean_str(row.get("subjects")),
                        }
                    )
                    if created:
                        self.stats[filename]["created"] += 1
                    else:
                        self.stats[filename]["updated"] += 1
            except Exception as e:
                self.errors.append({"file": filename, "row": idx + 2, "error": str(e)})
                self.stats[filename]["failed"] += 1

    def import_chatbot_metadata(self, df, filename):
        for idx, row in df.iterrows():
            excel_book_id = self.clean_int(row.get("book_id"))
            book = self.book_map.get(excel_book_id)

            if not book:
                self.errors.append({"file": filename, "row": idx + 2, "error": f"Book ID {excel_book_id} not found for chatbot metadata."})
                self.stats[filename]["failed"] += 1
                continue

            try:
                with transaction.atomic():
                    cb_meta, created = ChatbotMetadata.objects.update_or_create(
                        book=book,
                        defaults={
                            "short_ai_summary": self.clean_str(row.get("short_ai_summary")),
                            "long_ai_summary": self.clean_str(row.get("long_ai_summary")),
                            "recommendation_reason": self.clean_str(row.get("recommendation_reason")),
                            "search_text": self.clean_str(row.get("search_text")),
                        }
                    )
                    if created:
                        self.stats[filename]["created"] += 1
                    else:
                        self.stats[filename]["updated"] += 1
            except Exception as e:
                self.errors.append({"file": filename, "row": idx + 2, "error": str(e)})
                self.stats[filename]["failed"] += 1

    def import_similar_books(self, df, filename):
        for idx, row in df.iterrows():
            excel_book_id = self.clean_int(row.get("book_id"))
            excel_similar_id = self.clean_int(row.get("similar_book_id"))

            book = self.book_map.get(excel_book_id)
            similar_book = self.book_map.get(excel_similar_id)

            if not book or not similar_book:
                self.errors.append({"file": filename, "row": idx + 2, "error": f"FK mismatch: Book {excel_book_id} or Similar Book {excel_similar_id} not found."})
                self.stats[filename]["failed"] += 1
                continue

            try:
                with transaction.atomic():
                    sim, created = SimilarBook.objects.update_or_create(
                        book=book,
                        similar_book=similar_book,
                        defaults={
                            "similarity_score": self.clean_float(row.get("similarity_score")),
                            "rank": self.clean_int(row.get("rank"), 0),
                        }
                    )
                    if created:
                        self.stats[filename]["created"] += 1
                    else:
                        self.stats[filename]["updated"] += 1
            except Exception as e:
                self.errors.append({"file": filename, "row": idx + 2, "error": str(e)})
                self.stats[filename]["failed"] += 1

    def print_report(self):
        self.stdout.write(self.style.MIGRATE_HEADING("\n" + "=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING("IMPORT PROCESS REPORT"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))

        # Format stats table
        self.stdout.write(f"{'Filename':<35} | {'Total':<6} | {'Created':<7} | {'Updated':<7} | {'Failed':<6}")
        self.stdout.write("-" * 72)
        for filename, stats in self.stats.items():
            self.stdout.write(
                f"{filename:<35} | {stats['total']:<6} | {stats['created']:<7} | {stats['updated']:<7} | {stats['failed']:<6}"
            )

        if self.errors:
            self.stdout.write(self.style.ERROR("\nDetailed Import Errors:"))
            for err in self.errors:
                self.stdout.write(
                    self.style.ERROR(f"File: {err['file']} | Row: {err['row']} | Error: {err['error']}")
                )
        else:
            self.stdout.write(self.style.SUCCESS("\nAll records processed without failures!"))
