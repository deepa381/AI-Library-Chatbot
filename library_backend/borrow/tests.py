from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import UserRole, MembershipType
from books.models import Book, Publisher
from borrow.models import BorrowRecord, BorrowStatus
from datetime import timedelta


class BorrowManagementAPITests(APITestCase):
    """
    Integration tests for BorrowRecord lifecycle endpoints.
    """

    def setUp(self) -> None:
        # Create a publisher for books
        self.publisher = Publisher.objects.create(
            name="Library Publisher",
            website="http://pub.example.com",
            email="pub@example.com"
        )

        # Create books
        self.book1 = Book.objects.create(
            isbn="9780132350884",
            title="Clean Code",
            publication_year=2008,
            publisher=self.publisher,
            total_copies=5,
            available_copies=5
        )
        self.book_scarce = Book.objects.create(
            isbn="9780201616224",
            title="Pragmatic Programmer",
            publication_year=1999,
            publisher=self.publisher,
            total_copies=1,
            available_copies=1
        )
        self.book_unavailable = Book.objects.create(
            isbn="9780134494166",
            title="Clean Architecture",
            publication_year=2017,
            publisher=self.publisher,
            total_copies=1,
            available_copies=0
        )

        # Librarian User
        self.librarian = User.objects.create_user(
            username='librarian_borrow', email='lib_b@library.org', password='LibPassword123!'
        )
        self.librarian.profile.role = UserRole.LIBRARIAN
        self.librarian.profile.save()

        # Member User
        self.member = User.objects.create_user(
            username='member_borrow', email='mem_b@library.org', password='MemberPassword123!'
        )

        # Other Member User
        self.other_member = User.objects.create_user(
            username='other_borrow', email='other_b@library.org', password='OtherPassword123!'
        )

        self.list_url = '/api/borrow/'

    def _detail_url(self, pk: int) -> str:
        return f'/api/borrow/{pk}/'

    def _action_url(self, pk: int, action: str) -> str:
        return f'/api/borrow/{pk}/{action}/'

    # ── Borrow (Create) Tests ──────────────────────────────────────────────────

    def test_member_can_borrow_available_book(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.post(self.list_url, {'book_id': self.book1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.available_copies, 4)
        
        record = BorrowRecord.objects.get(pk=response.data['id'])
        self.assertEqual(record.status, BorrowStatus.BORROWED)
        self.assertEqual(record.member, self.member.profile)

    def test_cannot_borrow_unavailable_book(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.post(self.list_url, {'book_id': self.book_unavailable.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_borrow_duplicate_active_book(self) -> None:
        self.client.force_authenticate(user=self.member)
        # First borrow
        self.client.post(self.list_url, {'book_id': self.book_scarce.pk}, format='json')
        # Second borrow same book
        response = self.client.post(self.list_url, {'book_id': self.book_scarce.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_borrow_beyond_limit(self) -> None:
        # Set member's borrow limit to 1
        self.member.profile.borrow_limit = 1
        self.member.profile.save()

        self.client.force_authenticate(user=self.member)
        # Borrow first
        self.client.post(self.list_url, {'book_id': self.book1.pk}, format='json')
        # Borrow second
        response = self.client.post(self.list_url, {'book_id': self.book_scarce.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Return Tests ──────────────────────────────────────────────────────────

    def test_member_can_return_own_borrowed_book(self) -> None:
        # Create borrow record
        record = BorrowRecord.objects.create(
            member=self.member.profile, book=self.book_scarce, status=BorrowStatus.BORROWED
        )
        self.book_scarce.available_copies = 0
        self.book_scarce.save()

        self.client.force_authenticate(user=self.member)
        response = self.client.post(self._action_url(record.pk, 'return'), {'remarks': 'good condition'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        record.refresh_from_db()
        self.assertEqual(record.status, BorrowStatus.RETURNED)
        self.assertIsNotNone(record.return_date)
        self.assertIn("good condition", record.remarks)

        self.book_scarce.refresh_from_db()
        self.assertEqual(self.book_scarce.available_copies, 1)

    def test_member_cannot_return_other_member_borrowed_book(self) -> None:
        record = BorrowRecord.objects.create(
            member=self.other_member.profile, book=self.book_scarce, status=BorrowStatus.BORROWED
        )
        self.client.force_authenticate(user=self.member)
        response = self.client.post(self._action_url(record.pk, 'return'), {}, format='json')
        # Since it filters querysets based on member, standard user gets a 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_librarian_can_force_return_any_borrowed_book(self) -> None:
        record = BorrowRecord.objects.create(
            member=self.member.profile, book=self.book_scarce, status=BorrowStatus.BORROWED
        )
        self.book_scarce.available_copies = 0
        self.book_scarce.save()
        self.client.force_authenticate(user=self.librarian)
        response = self.client.post(self._action_url(record.pk, 'return'), {'remarks': 'Returned by admin'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        record.refresh_from_db()
        self.assertEqual(record.status, BorrowStatus.RETURNED)

    # ── Renew Tests ───────────────────────────────────────────────────────────

    def test_member_can_renew_own_borrowed_book(self) -> None:
        record = BorrowRecord.objects.create(
            member=self.member.profile, book=self.book1, status=BorrowStatus.BORROWED
        )
        original_due_date = record.due_date

        self.client.force_authenticate(user=self.member)
        response = self.client.post(self._action_url(record.pk, 'renew'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        record.refresh_from_db()
        self.assertEqual(record.renew_count, 1)
        self.assertEqual(record.due_date, original_due_date + timedelta(days=14))

    def test_cannot_renew_returned_book(self) -> None:
        record = BorrowRecord.objects.create(
            member=self.member.profile, book=self.book1, status=BorrowStatus.RETURNED
        )
        self.client.force_authenticate(user=self.member)
        response = self.client.post(self._action_url(record.pk, 'renew'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_renew_more_than_twice(self) -> None:
        record = BorrowRecord.objects.create(
            member=self.member.profile, book=self.book1, status=BorrowStatus.BORROWED, renew_count=2
        )
        self.client.force_authenticate(user=self.member)
        response = self.client.post(self._action_url(record.pk, 'renew'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Permission, Filtering & Searching Tests ─────────────────────────────────

    def test_librarian_can_list_all_records(self) -> None:
        BorrowRecord.objects.create(member=self.member.profile, book=self.book1, status=BorrowStatus.BORROWED)
        BorrowRecord.objects.create(member=self.other_member.profile, book=self.book_scarce, status=BorrowStatus.BORROWED)

        self.client.force_authenticate(user=self.librarian)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_member_can_only_list_own_records(self) -> None:
        BorrowRecord.objects.create(member=self.member.profile, book=self.book1, status=BorrowStatus.BORROWED)
        BorrowRecord.objects.create(member=self.other_member.profile, book=self.book_scarce, status=BorrowStatus.BORROWED)

        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return the 1 record for self.member
        self.assertEqual(len(response.data), 1)

    def test_search_by_book_title(self) -> None:
        BorrowRecord.objects.create(member=self.member.profile, book=self.book1, status=BorrowStatus.BORROWED)
        self.client.force_authenticate(user=self.librarian)
        response = self.client.get(self.list_url + '?search=Clean')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_status(self) -> None:
        BorrowRecord.objects.create(member=self.member.profile, book=self.book1, status=BorrowStatus.BORROWED)
        self.client.force_authenticate(user=self.librarian)
        response = self.client.get(self.list_url + '?status=RETURNED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
