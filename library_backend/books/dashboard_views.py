from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Sum, Count
from accounts.permissions import IsLibrarian
from accounts.models import MemberProfile, UserRole
from books.models import Book
from borrow.models import BorrowRecord, Fine, FineStatus, BorrowStatus
from reservations.models import Reservation, ReservationStatus


class DashboardView(APIView):
    """
    API view providing high-level operational statistics.
    Librarians only.
    """
    permission_classes = [IsLibrarian]

    def get(self, request, *args, **kwargs):
        # Book counts
        total_book_titles = Book.objects.count()
        total_physical_copies = Book.objects.aggregate(total=Sum('total_copies'))['total'] or 0
        available_physical_copies = Book.objects.aggregate(total=Sum('available_copies'))['total'] or 0
        
        # Borrow & Reservation counts
        borrowed_books_count = BorrowRecord.objects.filter(status=BorrowStatus.BORROWED).count()
        reserved_books_count = Reservation.objects.filter(
            status__in=[ReservationStatus.ACTIVE, ReservationStatus.WAITING]
        ).count()

        # Member counts
        total_members = MemberProfile.objects.filter(role=UserRole.MEMBER).count()
        active_members = MemberProfile.objects.filter(role=UserRole.MEMBER, is_active=True).count()

        # Fines
        pending_fines = Fine.objects.filter(status=FineStatus.PENDING).aggregate(total=Sum('amount'))['total'] or 0.00
        collected_fines = Fine.objects.filter(status=FineStatus.PAID).aggregate(total=Sum('amount'))['total'] or 0.00

        # Most borrowed books
        most_borrowed = Book.objects.annotate(
            borrow_count=Count('borrow_records')
        ).order_by('-borrow_count')[:5]
        
        most_borrowed_serialized = [
            {
                "id": book.id,
                "title": book.title,
                "isbn": book.isbn,
                "borrow_count": book.borrow_count
            }
            for book in most_borrowed
        ]

        # Recently added books
        recently_added = Book.objects.order_by('-created_at')[:5]
        recently_added_serialized = [
            {
                "id": book.id,
                "title": book.title,
                "isbn": book.isbn,
                "created_at": book.created_at
            }
            for book in recently_added
        ]

        data = {
            "statistics": {
                "total_book_titles": total_book_titles,
                "total_physical_copies": total_physical_copies,
                "available_physical_copies": available_physical_copies,
                "borrowed_books": borrowed_books_count,
                "reserved_books": reserved_books_count,
                "total_members": total_members,
                "active_members": active_members,
                "pending_fines": float(pending_fines),
                "collected_fines": float(collected_fines),
            },
            "most_borrowed_books": most_borrowed_serialized,
            "recently_added_books": recently_added_serialized
        }

        return Response(data, status=status.HTTP_200_OK)
