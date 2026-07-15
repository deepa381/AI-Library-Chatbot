from django.db import models
from django.utils import timezone
from core.models import BaseModel
from accounts.models import MemberProfile
from books.models import Book


class ReservationStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    WAITING = "WAITING", "Waiting"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    EXPIRED = "EXPIRED", "Expired"


class Reservation(BaseModel):
    """
    Model representing a book reservation when no physical copies are available.
    """
    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="Member",
        help_text="The member making this reservation."
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="Book",
        help_text="The book being reserved."
    )
    reservation_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Reservation Date",
        help_text="Date and time when the reservation request was placed."
    )
    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expiry Date",
        help_text="48-hour pickup window once status transitions to ACTIVE."
    )
    status = models.CharField(
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.WAITING,
        verbose_name="Status",
        help_text="Current lifecycle state of the reservation."
    )
    queue_position = models.PositiveIntegerField(
        default=1,
        verbose_name="Queue Position",
        help_text="Queue position in waiting list for this book."
    )
    remarks = models.TextField(
        blank=True,
        verbose_name="Remarks",
        help_text="Optional comments or notes."
    )

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ["queue_position", "reservation_date"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["queue_position"]),
            models.Index(fields=["book", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.member.user.username} - {self.book.title} ({self.status} #{self.queue_position})"

    def save(self, *args, **kwargs):
        # Auto-assign queue position for new WAITING reservations
        if not self.pk and self.status == ReservationStatus.WAITING:
            existing = Reservation.objects.filter(
                book=self.book,
                status=ReservationStatus.WAITING
            ).aggregate(models.Max('queue_position'))['queue_position__max']
            self.queue_position = (existing or 0) + 1
        super().save(*args, **kwargs)
