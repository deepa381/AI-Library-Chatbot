from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from .models import Reservation, ReservationStatus
from borrow.models import BorrowRecord, BorrowStatus


def refresh_reservation_queue(book):
    """
    Recalculates queue positions for all non-completed/non-cancelled/non-expired reservations for a book.
    If copies become available and the top WAITING reservation is next, transition it to ACTIVE.
    """
    with transaction.atomic():
        # Get active or waiting reservations for this book
        reservations = Reservation.objects.filter(
            book=book,
            status__in=[ReservationStatus.WAITING, ReservationStatus.ACTIVE]
        ).order_by('reservation_date')

        # Compact queue positions
        pos = 1
        for res in reservations:
            # If it's WAITING, assign its compacted queue position
            if res.status == ReservationStatus.WAITING:
                res.queue_position = pos
                pos += 1
                res.save()
            elif res.status == ReservationStatus.ACTIVE:
                # ACTIVE reservations don't hold a queue position count for the waiting queue
                res.queue_position = 0
                res.save()

        # If copies are available and there's a waiting queue, activate the first one
        book.refresh_from_db()
        if book.available_copies > 0:
            next_waiting = Reservation.objects.filter(
                book=book,
                status=ReservationStatus.WAITING
            ).order_by('reservation_date').first()

            if next_waiting:
                next_waiting.status = ReservationStatus.ACTIVE
                next_waiting.queue_position = 0
                next_waiting.expiry_date = timezone.now() + timedelta(hours=48)
                next_waiting.save()
                
                # Decrement available copies as it is now locked/reserved for this user
                book.available_copies -= 1
                book.save()


def expire_reservations():
    """
    Finds ACTIVE reservations that have passed their expiry_date, cancels them,
    releases the book, and refreshes the queue for the book.
    """
    now = timezone.now()
    expired_reservations = Reservation.objects.filter(
        status=ReservationStatus.ACTIVE,
        expiry_date__lt=now
    )

    books_to_refresh = set()
    for res in expired_reservations:
        with transaction.atomic():
            res.status = ReservationStatus.EXPIRED
            res.save()
            
            # Release book copy back to the pool
            book = res.book
            book.available_copies += 1
            book.save()
            books_to_refresh.add(book)

    for book in books_to_refresh:
        refresh_reservation_queue(book)
