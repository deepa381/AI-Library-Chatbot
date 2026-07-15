from typing import Any
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import UserRole
from accounts.permissions import IsLibrarian
from .models import Reservation, ReservationStatus
from .serializers import ReservationSerializer, ReservationCreateSerializer
from .services import refresh_reservation_queue
from borrow.models import BorrowRecord, BorrowStatus


class ReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving, creating, collecting, and cancelling reservations.
    """
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'book__title',
        'member__user__username',
        'member__membership_id',
        'book__isbn'
    ]
    ordering_fields = ['reservation_date', 'expiry_date', 'queue_position', 'status']
    ordering = ['queue_position', 'reservation_date']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        qs = Reservation.objects.select_related('member__user', 'book').all()

        is_librarian = (
            user.is_staff or user.is_superuser or
            (hasattr(user, 'profile') and user.profile.role == UserRole.LIBRARIAN)
        )

        if not is_librarian:
            if hasattr(user, 'profile'):
                qs = qs.filter(member=user.profile)
            else:
                qs = qs.none()

        # Apply filtering
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status__iexact=status_param)

        reservation_date = self.request.query_params.get('reservation_date')
        if reservation_date:
            qs = qs.filter(reservation_date__date=reservation_date)

        expiry_date = self.request.query_params.get('expiry_date')
        if expiry_date:
            qs = qs.filter(expiry_date__date=expiry_date)

        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        return ReservationSerializer

    def get_permissions(self):
        if self.action in ['destroy', 'partial_update', 'update']:
            return [IsLibrarian()]
        return [permissions.IsAuthenticated()]

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = serializer.validated_data['book']
        remarks = serializer.validated_data.get('remarks', '')

        with transaction.atomic():
            # Double check copies availability under transaction
            book.refresh_from_db()
            if book.available_copies > 0:
                return Response(
                    {"detail": "Reservations are only allowed when available copies are zero."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create reservation (starts as WAITING)
            reservation = Reservation.objects.create(
                member=request.user.profile,
                book=book,
                remarks=remarks,
                status=ReservationStatus.WAITING
            )

        response_serializer = ReservationSerializer(reservation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request: Any, pk: Any = None) -> Response:
        """
        Cancels a reservation. Members can cancel their own; Librarians can cancel any.
        """
        reservation = self.get_object()
        user = request.user
        is_librarian = (
            user.is_staff or user.is_superuser or
            (hasattr(user, 'profile') and user.profile.role == UserRole.LIBRARIAN)
        )

        if not is_librarian and reservation.member != getattr(user, 'profile', None):
            return Response(
                {"detail": "You do not have permission to cancel this reservation."},
                status=status.HTTP_403_FORBIDDEN
            )

        if reservation.status in [ReservationStatus.CANCELLED, ReservationStatus.COMPLETED, ReservationStatus.EXPIRED]:
            return Response(
                {"detail": f"Cannot cancel a reservation that is already {reservation.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = reservation.status
        book = reservation.book

        with transaction.atomic():
            reservation.status = ReservationStatus.CANCELLED
            reservation.queue_position = 0
            reservation.save()

            if old_status == ReservationStatus.ACTIVE:
                # Release the reserved book copy back to inventory
                book.available_copies += 1
                book.save()

            refresh_reservation_queue(book)

        return Response(
            {"detail": "Reservation successfully cancelled.", "reservation": ReservationSerializer(reservation).data},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='collect')
    def collect(self, request: Any, pk: Any = None) -> Response:
        """
        Collects the reserved book. This transitions Reservation to COMPLETED and creates a BorrowRecord.
        """
        reservation = self.get_object()
        user = request.user
        is_librarian = (
            user.is_staff or user.is_superuser or
            (hasattr(user, 'profile') and user.profile.role == UserRole.LIBRARIAN)
        )

        if not is_librarian and reservation.member != getattr(user, 'profile', None):
            return Response(
                {"detail": "You do not have permission to collect this reservation."},
                status=status.HTTP_403_FORBIDDEN
            )

        if reservation.status != ReservationStatus.ACTIVE:
            return Response(
                {"detail": "Only ACTIVE reservations can be collected."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check borrow limit before checkout
        member_profile = reservation.member
        active_borrows_count = BorrowRecord.objects.filter(
            member=member_profile,
            status=BorrowStatus.BORROWED
        ).count()
        if active_borrows_count >= member_profile.borrow_limit:
            return Response(
                {"detail": f"Cannot collect. You have reached your borrow limit of {member_profile.borrow_limit} books."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check duplicate active borrows
        active_borrow = BorrowRecord.objects.filter(
            member=member_profile,
            book=reservation.book,
            status=BorrowStatus.BORROWED
        ).exists()
        if active_borrow:
            return Response(
                {"detail": "Cannot collect. You already have an active borrow for this book."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Mark reservation as completed
            reservation.status = ReservationStatus.COMPLETED
            reservation.save()

            # Create the borrow record
            borrow_record = BorrowRecord.objects.create(
                member=member_profile,
                book=reservation.book,
                status=BorrowStatus.BORROWED,
                remarks=f"Collected from reservation ID: {reservation.id}."
            )

        return Response(
            {
                "detail": "Book collected successfully.",
                "reservation": ReservationSerializer(reservation).data,
                "borrow_record": {
                    "id": borrow_record.id,
                    "borrow_date": borrow_record.borrow_date,
                    "due_date": borrow_record.due_date,
                    "status": borrow_record.status
                }
            },
            status=status.HTTP_200_OK
        )
