import os
import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from books.models import Book, Author, Publisher, Category, Tag
from recommendation.models import RecommendationMetadata
from chatbot.models import ChatbotMetadata

class Command(BaseCommand):
    help = 'Imports or generates datasets for the Library Chatbot project'

    def handle(self, *args, **kwargs):
        dataset_dir = os.path.join(settings.BASE_DIR, 'dataset')
        os.makedirs(dataset_dir, exist_ok=True)
        sample_file = os.path.join(dataset_dir, 'sample_books.csv')

        if not os.path.exists(sample_file):
            self.stdout.write(self.style.WARNING("Sample dataset not found. Generating one..."))
            self._generate_sample_dataset(sample_file)
            self.stdout.write(self.style.SUCCESS(f"Generated {sample_file}"))
            
        self.stdout.write("Importing dataset...")
        success_count = 0
        error_count = 0
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    self._import_row(row)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f"Error importing row {row.get('isbn', 'unknown')}: {e}"))
                    
        self.stdout.write(self.style.SUCCESS(f"Import complete! Successfully imported: {success_count}. Errors: {error_count}."))

    def _generate_sample_dataset(self, file_path):
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "isbn", "title", "authors", "publisher", "categories", "tags", 
                "total_copies", "difficulty_level", "reading_level", "ai_summary", "mood"
            ])
            writer.writerow([
                "9780743273565", "The Great Gatsby", "F. Scott Fitzgerald", "Scribner", 
                "Fiction,Classic", "american literature,jazz age", 
                10, "Intermediate", "High School", "A story of the fabulously wealthy Jay Gatsby and his love for the beautiful Daisy Buchanan.", "Melancholic;Reflective"
            ])
            writer.writerow([
                "9780446310789", "To Kill a Mockingbird", "Harper Lee", "Warner Books", 
                "Fiction,Classic", "coming of age,social justice", 
                15, "Intermediate", "Middle School", "Compassionate, dramatic, and deeply moving, taking readers to the roots of human behavior.", "Thoughtful;Serious"
            ])
            writer.writerow([
                "9780553213119", "Moby-Dick", "Herman Melville", "Bantam Classics", 
                "Fiction,Adventure", "whaling,obsession", 
                5, "Advanced", "College", "The epic tale of Captain Ahab's obsessive quest for the white whale.", "Dark;Adventurous"
            ])
            writer.writerow([
                "9780451524935", "1984", "George Orwell", "Signet Classic", 
                "Dystopian,Fiction", "totalitarianism,surveillance", 
                12, "Intermediate", "High School", "A chilling prophecy about the future.", "Bleak;Tense"
            ])
            writer.writerow([
                "9781400033416", "Beloved", "Toni Morrison", "Vintage", 
                "Fiction,Historical", "slavery,memory", 
                8, "Advanced", "College", "A powerfully imagined novel about slavery and its aftermath.", "Haunting;Powerful"
            ])
            
    def _import_row(self, row):
        # Publisher
        publisher, _ = Publisher.objects.get_or_create(name=row.get('publisher', 'Unknown Publisher').strip())
        
        # Book
        book, created = Book.objects.update_or_create(
            isbn=row['isbn'].strip(),
            defaults={
                'title': row['title'].strip(),
                'publisher': publisher,
                'publication_year': int(row.get('publication_year') or 2000),
                'total_copies': int(row.get('total_copies', 1)),
                'available_copies': int(row.get('total_copies', 1))
            }
        )
        
        # Authors
        if row.get('authors'):
            author_names = [a.strip() for a in row['authors'].split(',')]
            for name in author_names:
                parts = name.split()
                if len(parts) > 1:
                    first = " ".join(parts[:-1])
                    last = parts[-1]
                else:
                    first = name
                    last = ""
                author, _ = Author.objects.get_or_create(first_name=first, last_name=last)
                book.authors.add(author)
                
        # Categories
        if row.get('categories'):
            for cat_name in [c.strip() for c in row['categories'].split(',')]:
                cat, _ = Category.objects.get_or_create(name=cat_name, defaults={'slug': cat_name.lower().replace(' ', '-')})
                book.categories.add(cat)
                
        # Tags
        if row.get('tags'):
            for tag_name in [t.strip() for t in row['tags'].split(',')]:
                tag, _ = Tag.objects.get_or_create(name=tag_name, defaults={'slug': tag_name.lower().replace(' ', '-')})
                book.tags.add(tag)
                
        # Recommendation Metadata
        diff = row.get('difficulty_level', '')
        read = row.get('reading_level', '')
        mood = row.get('mood', '')
        if diff or read or mood:
            RecommendationMetadata.objects.update_or_create(
                book=book,
                defaults={
                    'difficulty_level': diff,
                    'reading_level': read,
                    'mood': mood
                }
            )
            
        # Chatbot Metadata
        ai_summary = row.get('ai_summary', '')
        if ai_summary:
            ChatbotMetadata.objects.update_or_create(
                book=book,
                defaults={
                    'short_ai_summary': ai_summary[:255],
                    'long_ai_summary': ai_summary
                }
            )
