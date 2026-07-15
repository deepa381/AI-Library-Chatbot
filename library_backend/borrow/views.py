from typing import Any
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import UserRole
from accounts.permissions import IsLibrarian
from .models import BorrowRecord, BorrowStatus, Fine, FineStatus
from .serializers import (
    BorrowRecordSerializer,
    BorrowCreateSerializer,
    BorrowReturnSerializer,
    BorrowRenewSerializer,
    FineSerializer
)
from .services import check_and_create_fine_on_return
from reservations.services import refresh_reservation_queue
from datetime import timedelta


class BorrowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving, creating, returning, and renewing borrow records.
    """
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'book__title',
        'member__user__username',
        'member__membership_id',
        'book__isbn'
    ]
    ordering_fields = ['borrow_date', 'due_date', 'return_date', 'status']
    ordering = ['-borrow_date']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        """
        Optimize using select_related.
        Librarians see all records, while members only see their own.
        """
        user = self.request.user
        qs = BorrowRecord.objects.select_related('member__user', 'book').all()

        is_librarian = (
            user.is_staff or user.is_superuser or
            (hasattr(user, 'profile') and user.profile.role == UserRole.LIBRARIAN)
        )

        if not is_librarian:
            if hasattr(user, 'profile'):
                qs = qs.filter(member=user.profile)
            else:
                qs = qs.none()

        # Filters
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status__iexact=status_param)

        borrow_date_param = self.request.query_params.get('borrow_date')
        if borrow_date_param:
            qs = qs.filter(borrow_date__date=borrow_date_param)

        due_date_param = self.request.query_params.get('due_date')
        if due_date_param:
            qs = qs.filter(due_date__date=due_date_param)

        return_date_param = self.request.query_params.get('return_date')
        if return_date_param:
            qs = qs.filter(return_date__date=return_date_param)

        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return BorrowCreateSerializer
        elif self.action == 'return_book':
            return BorrowReturnSerializer
        elif self.action == 'renew_book':
            return BorrowRenewSerializer
        return BorrowRecordSerializer

    def get_permissions(self):
        if self.action in ['destroy', 'partial_update', 'update']:
            return [IsLibrarian()]
        return [permissions.IsAuthenticated()]

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Creates a new BorrowRecord and atomic decrements Book available_copies.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = serializer.validated_data['book']
        remarks = serializer.validated_data.get('remarks', '')

        with transaction.atomic():
            # Refresh from database with locking
            book.refresh_from_db()
            if book.available_copies <= 0:
                return Response(
                    {"detail": "There are no available copies of this book currently."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create record
            record = BorrowRecord.objects.create(
                member=request.user.profile,
                book=book,
                remarks=remarks,
                status=BorrowStatus.BORROWED
            )

            # Decrement book availability
            book.available_copies -= 1
            book.save()

        response_serializer = BorrowRecordSerializer(record)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='return')
    def return_book(self, request: Any, pk: Any = None) -> Response:
        """
        Allows returning a book.
        Librarians can return any record, members can only return their own active records.
        """
        record = self.get_object()
        user = request.user
        is_librarian = (
            user.is_staff or user.is_superuser or
            (hasattr(user, 'profile') and user.profile.role == UserRole.LIBRARIAN)
        )

        if not is_librarian and record.member != getattr(user, 'profile', None):
            return Response(
                {"detail": "You do not have permission to return this book."},
                status=status.HTTP_403_FORBIDDEN
            )

        if record.status == BorrowStatus.RETURNED:
            return Response(
                {"detail": "This book has already been returned."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        remarks = serializer.validated_data.get('remarks', '')

        with transaction.atomic():
            record.status = BorrowStatus.RETURNED
            record.return_date = timezone.now()
            if remarks:
                record.remarks = f"{record.remarks} | Return remarks: {remarks}".strip(" | ")
            record.save()

            # Fine validation/creation on return if late
            check_and_create_fine_on_return(record)

            book = record.book
            book.available_copies += 1
            book.save()

            # Refresh the reservations queue for this book
            refresh_reservation_queue(book)

        return Response(
            {"detail": f"Book '{book.title}' successfully returned.", "record": BorrowRecordSerializer(record).data},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='renew')
    def renew_book(self, request: Any, pk: Any = None) -> Response:
        """
        Allows renewing a borrowed book.
        Librarians and matching members can perform this. Adds 14 days to due_date. Max 2 renewals.
        """
        record = self.get_object()
        user = request.user
        is_librarian = (
            user.is_staff or user.is_superuser or
            (hasattr(user, 'profile') and user.profile.role == UserRole.LIBRARIAN)
        )

        if not is_librarian and record.member != getattr(user, 'profile', None):
            return Response(
                {"detail": "You do not have permission to renew this book."},
                status=status.HTTP_403_FORBIDDEN
            )

        if record.status == BorrowStatus.RETURNED:
            return Response(
                {"detail": "Cannot renew a book that has already been returned."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if record.renew_count >= BorrowRecord.MAX_RENEWALS:
            return Response(
                {"detail": f"This book has already reached the maximum of {BorrowRecord.MAX_RENEWALS} renewals."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        remarks = serializer.validated_data.get('remarks', '')

        with transaction.atomic():
            record.renew_count += 1
            record.due_date = record.due_date + timedelta(days=BorrowRecord.BORROW_DURATION_DAYS)
            if remarks:
                record.remarks = f"{record.remarks} | Renewal {record.renew_count} remarks: {remarks}".strip(" | ")
            record.save()

        return Response(
            {"detail": "Book borrow successfully renewed.", "record": BorrowRecordSerializer(record).data},
            status=status.HTTP_200_OK
        )


class FineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving, paying, and waiving fines.
    """
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'member__user__username',
        'member__membership_id',
        'borrow_record__book__title'
    ]
    ordering_fields = ['amount', 'status', 'created_at', 'paid_at']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        qs = Fine.objects.select_related('member__user', 'borrow_record__book').all()

        is_librarian = (
            user.is_staff or user.is_superuser or
            (hasattr(user, 'profile') and user.profile.role == UserRole.LIBRARIAN)
        )

        if not is_librarian:
            if hasattr(user, 'profile'):
                qs = qs.filter(member=user.profile)
            else:
                qs = qs.none()

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status__iexact=status_param)

        return qs

    def get_serializer_class(self):
        return FineSerializer

    def get_permissions(self):
        if self.action in ['destroy', 'partial_update', 'update', 'waive']:
            return [IsLibrarian()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['post'], url_path='pay')
    def pay(self, request: Any, pk: Any = None) -> Response:
        """
        Marks a fine as PAID. Allowed for member (own fine) or librarian.
        """
        fine = self.get_object()
        user = request.user
        is_librarian = (
            user.is_staff or user.is_superuser or
            (hasattr(user, 'profile') and user.profile.role == UserRole.LIBRARIAN)
        )

        if not is_librarian and fine.member != getattr(user, 'profile', None):
            return Response(
                {"detail": "You do not have permission to pay this fine."},
                status=status.HTTP_403_FORBIDDEN
            )

        if fine.status != FineStatus.PENDING:
            return Response(
                {"detail": f"This fine cannot be paid as it is already {fine.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            fine.status = FineStatus.PAID
            fine.paid_at = timezone.now()
            fine.save()

        return Response(
            {"detail": f"Fine of ₹{fine.amount} has been successfully paid.", "fine": FineSerializer(fine).data},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='waive')
    def waive(self, request: Any, pk: Any = None) -> Response:
        """
        Marks a fine as WAIVED. Librarians only.
        """
        fine = self.get_object()
        if fine.status != FineStatus.PENDING:
            return Response(
                {"detail": f"This fine cannot be waived as it is already {fine.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            fine.status = FineStatus.WAIVED
            fine.paid_at = timezone.now()
            fine.save()

        return Response(
            {"detail": f"Fine of ₹{fine.amount} has been successfully waived.", "fine": FineSerializer(fine).data},
            status=status.HTTP_200_OK
        )

