import datetime
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import Author, Publisher, Category, Tag, Book, BookLanguage, BookStatus

class BookValidationTests(TestCase):
    def setUp(self) -> None:
        self.publisher = Publisher.objects.create(
            name="O'Reilly Media",
            email="contact@oreilly.com"
        )
        self.category = Category.objects.create(
            name="Technology",
            slug="technology"
        )
        self.tag = Tag.objects.create(
            name="Python",
            slug="python"
        )
        self.author = Author.objects.create(
            first_name="Guido",
            last_name="van Rossum"
        )

    def test_valid_isbn_13_saved_and_normalized(self) -> None:
        book = Book.objects.create(
            isbn="978-0-596-51774-8",
            title="Programming Python",
            publication_year=2010,
            publisher=self.publisher,
            total_copies=5,
            available_copies=5
        )
        # Should be normalized: hyphens stripped, uppercase
        self.assertEqual(book.isbn, "9780596517748")

    def test_invalid_isbn_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            Book.objects.create(
                isbn="invalid-isbn",
                title="Bad ISBN Book",
                publication_year=2020,
                publisher=self.publisher
            )

    def test_future_publication_year_raises_error(self) -> None:
        future_year = datetime.date.today().year + 2
        with self.assertRaises(ValidationError):
            Book.objects.create(
                isbn="9780596517748",
                title="Future Tech",
                publication_year=future_year,
                publisher=self.publisher
            )

    def test_available_copies_cannot_exceed_total_copies(self) -> None:
        with self.assertRaises(ValidationError):
            Book.objects.create(
                isbn="9780596517748",
                title="Overallocated Book",
                publication_year=2020,
                publisher=self.publisher,
                total_copies=2,
                available_copies=3
            )


class BookAPITests(APITestCase):
    def setUp(self) -> None:
        # Create core lookup relations
        self.publisher = Publisher.objects.create(
            name="Packt Publishing",
            email="contact@packt.com"
        )
        self.category = Category.objects.create(
            name="Computer Science",
            slug="computer-science"
        )
        self.tag = Tag.objects.create(
            name="Django",
            slug="django"
        )
        self.author = Author.objects.create(
            first_name="William",
            last_name="Vincent"
        )
        
        # Create standard book to test read/update/delete
        self.book = Book.objects.create(
            isbn="9781788292429",
            title="Django for Beginners",
            publication_year=2018,
            publisher=self.publisher,
            total_copies=3,
            available_copies=3,
            language=BookLanguage.ENGLISH,
            status=BookStatus.AVAILABLE
        )
        self.book.authors.add(self.author)
        self.book.categories.add(self.category)
        self.book.tags.add(self.tag)

        self.list_url = reverse('books:book-list')
        self.detail_url = reverse('books:book-detail', kwargs={'pk': self.book.pk})

        # Create a librarian user and authenticate client
        self.librarian_user = User.objects.create_user(
            username="lib_admin",
            email="admin@library.org",
            password="securepassword123",
            is_staff=True
        )
        self.client.force_authenticate(user=self.librarian_user)

    def test_create_book_success(self) -> None:
        data = {
            "isbn": "978-1-492-06029-1",
            "title": "Fluent Python",
            "publication_year": 2021,
            "publisher": self.publisher.id,
            "authors": [self.author.id],
            "categories": [self.category.id],
            "tags": [self.tag.id],
            "total_copies": 5,
            "available_copies": 5,
            "language": "EN",
            "status": "AVAILABLE"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "Fluent Python")
        # ISBN should be normalized in DB and returned formatted
        self.assertEqual(response.data['isbn'], "9781492060291")
        # Read representation should be nested
        self.assertEqual(len(response.data['authors']), 1)
        self.assertEqual(response.data['authors'][0]['first_name'], "William")
        self.assertEqual(response.data['publisher']['name'], "Packt Publishing")

    def test_retrieve_book_detail_nested_representation(self) -> None:
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify read operations return full nested serialization
        self.assertEqual(response.data['title'], "Django for Beginners")
        self.assertIsInstance(response.data['publisher'], dict)
        self.assertEqual(response.data['publisher']['name'], "Packt Publishing")
        self.assertIsInstance(response.data['authors'][0], dict)
        self.assertEqual(response.data['authors'][0]['last_name'], "Vincent")

    def test_update_book_success(self) -> None:
        # Use PUT to perform complete update
        data = {
            "isbn": "9781788292429",
            "title": "Django for Beginners (Updated Edition)",
            "publication_year": 2020,
            "publisher": self.publisher.id,
            "authors": [self.author.id],
            "categories": [self.category.id],
            "tags": [self.tag.id],
            "total_copies": 10,
            "available_copies": 8,
            "language": "EN",
            "status": "AVAILABLE"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Django for Beginners (Updated Edition)")
        self.assertEqual(response.data['total_copies'], 10)
        self.assertEqual(response.data['available_copies'], 8)

    def test_partial_update_patch_success(self) -> None:
        # Patch available copies
        data = {"available_copies": 2}
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['available_copies'], 2)

    def test_delete_book_success(self) -> None:
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())

    def test_search_books_by_title_and_author(self) -> None:
        # Create another book to test search separation
        other_author = Author.objects.create(first_name="Martin", last_name="Fowler")
        other_book = Book.objects.create(
            isbn="9780134757599",
            title="Refactoring",
            publication_year=2018,
            publisher=self.publisher,
            total_copies=2,
            available_copies=2
        )
        other_book.authors.add(other_author)

        # Search for 'Beginners'
        response = self.client.get(f"{self.list_url}?search=Beginners")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], "Django for Beginners")

        # Search for author 'Martin'
        response = self.client.get(f"{self.list_url}?search=Martin")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], "Refactoring")

    def test_filtering_books_by_status_and_language(self) -> None:
        # Query by status
        response = self.client.get(f"{self.list_url}?status=AVAILABLE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Query by publication year
        response = self.client.get(f"{self.list_url}?publication_year=2018")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Query by incorrect year
        response = self.client.get(f"{self.list_url}?publication_year=2000")
        self.assertEqual(response.data['count'], 0)

    def test_pagination_returns_ten_items_limit(self) -> None:
        # Create 11 books to trigger pagination
        for i in range(12):
            Book.objects.create(
                isbn=f"97800000000{i:02d}",
                title=f"Book number {i}",
                publication_year=2022,
                publisher=self.publisher,
                total_copies=1,
                available_copies=1
            )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check standard default page size is 10
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])

    def test_validation_available_copies_cannot_exceed_total(self) -> None:
        data = {
            "isbn": "9780596517748",
            "title": "Invalid Copies Book",
            "publication_year": 2020,
            "publisher": self.publisher.id,
            "total_copies": 2,
            "available_copies": 3  # Invalid
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('available_copies', response.data)

    def test_validation_negative_total_copies_rejected(self) -> None:
        data = {
            "isbn": "9780596517748",
            "title": "Negative Copies Book",
            "publication_year": 2020,
            "publisher": self.publisher.id,
            "total_copies": -1, # Invalid
            "available_copies": 0
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('total_copies', response.data)
