from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import UserRole
from books.models import Book, Publisher
from borrow.models import BorrowRecord, BorrowStatus, Fine, FineStatus
from reservations.models import Reservation, ReservationStatus
from reservations.services import refresh_reservation_queue, expire_reservations
from borrow.services import calculate_overdue_fines
from datetime import timedelta
from decimal import Decimal


class LibraryOperationsAPITests(APITestCase):
    """
    Integration tests for Module 7: Reservation, Fine, Advanced Search, Dashboard, and Reports.
    """

    def setUp(self) -> None:
        # Create Publisher
        self.publisher = Publisher.objects.create(
            name="Operations Publisher",
            website="http://ops.example.com",
            email="ops@example.com"
        )

        # Create Books
        self.book_scarce = Book.objects.create(
            isbn="9780132350884",
            title="Clean Code",
            publication_year=2008,
            publisher=self.publisher,
            total_copies=1,
            available_copies=0, # Unavailable, so reservation can be made
            status="OUT_OF_STOCK"
        )
        self.book_available = Book.objects.create(
            isbn="9780201616224",
            title="Pragmatic Programmer",
            publication_year=1999,
            publisher=self.publisher,
            total_copies=5,
            available_copies=5,
            status="AVAILABLE"
        )

        # Users
        self.librarian = User.objects.create_user(
            username='lib_ops', email='lib_ops@library.org', password='LibPassword123!'
        )
        self.librarian.profile.role = UserRole.LIBRARIAN
        self.librarian.profile.save()

        self.member1 = User.objects.create_user(
            username='member_ops1', email='mem_ops1@library.org', password='MemberPassword123!'
        )
        self.member2 = User.objects.create_user(
            username='member_ops2', email='mem_ops2@library.org', password='MemberPassword123!'
        )

        self.reservation_list_url = '/api/reservations/'
        self.fine_list_url = '/api/fines/'
        self.dashboard_url = '/api/dashboard/'

    def _reservation_action_url(self, pk: int, action: str) -> str:
        return f'/api/reservations/{pk}/{action}/'

    def _fine_action_url(self, pk: int, action: str) -> str:
        return f'/api/fines/{pk}/{action}/'

    # ── PART 1: RESERVATION SYSTEM TESTS ──────────────────────────────────────

    def test_reservation_creation_rules(self) -> None:
        # Member cannot reserve available book
        self.client.force_authenticate(user=self.member1)
        response = self.client.post(self.reservation_list_url, {'book_id': self.book_available.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Member can reserve unavailable book (queue position 1)
        response = self.client.post(self.reservation_list_url, {'book_id': self.book_scarce.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], ReservationStatus.WAITING)
        self.assertEqual(response.data['queue_position'], 1)

        # Member cannot reserve the same book twice
        response = self.client.post(self.reservation_list_url, {'book_id': self.book_scarce.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reservation_queue_sequence(self) -> None:
        # Member 1 reserves
        self.client.force_authenticate(user=self.member1)
        self.client.post(self.reservation_list_url, {'book_id': self.book_scarce.pk}, format='json')

        # Member 2 reserves -> queue position should be 2
        self.client.force_authenticate(user=self.member2)
        response = self.client.post(self.reservation_list_url, {'book_id': self.book_scarce.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['queue_position'], 2)

    def test_book_return_promotes_reservation(self) -> None:
        # Create active borrow record for scarce book (total copies = 1, available copies = 0)
        borrow_record = BorrowRecord.objects.create(
            member=self.member2.profile,
            book=self.book_scarce,
            status=BorrowStatus.BORROWED
        )
        
        # Member 1 reserves (WAITING queue #1)
        res = Reservation.objects.create(
            member=self.member1.profile,
            book=self.book_scarce,
            status=ReservationStatus.WAITING
        )

        # Return the borrowed book
        self.client.force_authenticate(user=self.librarian)
        return_url = f'/api/borrow/{borrow_record.pk}/return/'
        response = self.client.post(return_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check queue promotion: the reservation should now be ACTIVE, with 48h expiry, and copies still 0
        res.refresh_from_db()
        self.assertEqual(res.status, ReservationStatus.ACTIVE)
        self.assertEqual(res.queue_position, 0)
        self.assertIsNotNone(res.expiry_date)
        
        self.book_scarce.refresh_from_db()
        self.assertEqual(self.book_scarce.available_copies, 0) # Kept at 0 as it's allocated for pickup

    def test_reservation_expiry_flow(self) -> None:
        res = Reservation.objects.create(
            member=self.member1.profile,
            book=self.book_scarce,
            status=ReservationStatus.ACTIVE,
            expiry_date=timezone.now() - timedelta(hours=1)
        )
        # Scan and expire
        expire_reservations()

        res.refresh_from_db()
        self.assertEqual(res.status, ReservationStatus.EXPIRED)
        self.book_scarce.refresh_from_db()
        self.assertEqual(self.book_scarce.available_copies, 1)

    def test_collect_reservation(self) -> None:
        res = Reservation.objects.create(
            member=self.member1.profile,
            book=self.book_scarce,
            status=ReservationStatus.ACTIVE,
            expiry_date=timezone.now() + timedelta(hours=40)
        )
        # Set available copies appropriately for collection (was decremented during activation)
        self.book_scarce.available_copies = 0
        self.book_scarce.save()

        self.client.force_authenticate(user=self.member1)
        response = self.client.post(self._reservation_action_url(res.pk, 'collect'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        res.refresh_from_db()
        self.assertEqual(res.status, ReservationStatus.COMPLETED)
        
        # Verify a borrow record was created
        self.assertTrue(BorrowRecord.objects.filter(member=self.member1.profile, book=self.book_scarce, status=BorrowStatus.BORROWED).exists())

    # ── PART 2: FINE MANAGEMENT TESTS ─────────────────────────────────────────

    def test_fine_calculation_and_overdue_return(self) -> None:
        # Create an overdue borrow record (due 5 days ago)
        due_date = timezone.now() - timedelta(days=5)
        record = BorrowRecord.objects.create(
            member=self.member1.profile,
            book=self.book_available,
            status=BorrowStatus.BORROWED,
        )
        record.due_date = due_date
        record.save()

        # Decrement available_copies to simulate a real borrow
        self.book_available.available_copies -= 1
        self.book_available.save()

        # Run periodic fine scanner
        calculate_overdue_fines()

        fine = Fine.objects.get(borrow_record=record)
        self.assertEqual(fine.status, FineStatus.PENDING)
        self.assertEqual(fine.amount, Decimal('25.00')) # 5 days * ₹5

        # Return book late -> updates/sets fine
        self.client.force_authenticate(user=self.member1)
        return_url = f'/api/borrow/{record.pk}/return/'
        self.client.post(return_url, {}, format='json')

        fine.refresh_from_db()
        self.assertEqual(fine.status, FineStatus.PENDING)

    def test_fine_payment_and_waive(self) -> None:
        record = BorrowRecord.objects.create(
            member=self.member1.profile, book=self.book_available, status=BorrowStatus.BORROWED
        )
        fine = Fine.objects.create(
            borrow_record=record, member=self.member1.profile, amount=Decimal('10.00'), status=FineStatus.PENDING
        )

        # Member can pay fine
        self.client.force_authenticate(user=self.member1)
        response = self.client.post(self._fine_action_url(fine.pk, 'pay'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fine.refresh_from_db()
        self.assertEqual(fine.status, FineStatus.PAID)
        self.assertIsNotNone(fine.paid_at)

        # Reset fine status to pending
        fine.status = FineStatus.PENDING
        fine.paid_at = None
        fine.save()

        # Member cannot waive fine
        response = self.client.post(self._fine_action_url(fine.pk, 'waive'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Librarian can waive fine
        self.client.force_authenticate(user=self.librarian)
        response = self.client.post(self._fine_action_url(fine.pk, 'waive'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fine.refresh_from_db()
        self.assertEqual(fine.status, FineStatus.WAIVED)

    # ── PART 3: ADVANCED SEARCH & FILTERING TESTS ─────────────────────────────

    def test_advanced_search_and_filter(self) -> None:
        self.client.force_authenticate(user=self.member1)
        
        # Filter by rating
        response = self.client.get('/api/books/?rating=4.0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Filter by availability
        response = self.client.get('/api/books/?available=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Clean Code has 0 available_copies, Pragmatic Programmer has 5
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Pragmatic Programmer")

        # Ordering by title
        response = self.client.get('/api/books/?ordering=title')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── PART 4 & 5: DASHBOARD & REPORTS TESTS ─────────────────────────────────

    def test_librarian_only_dashboard(self) -> None:
        self.client.force_authenticate(user=self.member1)
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.librarian)
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("statistics", response.data)

    def test_reports_endpoints(self) -> None:
        # Check permissions and date filtering
        self.client.force_authenticate(user=self.member1)
        
        report_urls = [
            '/api/reports/borrow/',
            '/api/reports/reservation/',
            '/api/reports/fine/',
            '/api/reports/member-activity/',
            '/api/reports/book-popularity/'
        ]
        
        for url in report_urls:
            response = self.client.get(url + '?date_from=2026-01-01&date_to=2026-12-31')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
