from django.db import models
from django.utils import timezone
from core.models import BaseModel
from accounts.models import MemberProfile
from books.models import Book


class BorrowStatus(models.TextChoices):
    BORROWED = "BORROWED", "Borrowed"
    RETURNED = "RETURNED", "Returned"
    OVERDUE = "OVERDUE", "Overdue"


class BorrowRecord(BaseModel):
    """
    Tracks the lifecycle of a book borrowing transaction.
    Each record represents a single borrow-return cycle for one member and one book.
    """
    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="borrow_records",
        verbose_name="Member",
        help_text="The library member who borrowed the book."
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="borrow_records",
        verbose_name="Book",
        help_text="The book that was borrowed."
    )
    borrow_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Borrow Date",
        help_text="Date and time when the book was borrowed."
    )
    due_date = models.DateTimeField(
        verbose_name="Due Date",
        help_text="Date and time by which the book must be returned."
    )
    return_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Return Date",
        help_text="Date and time when the book was actually returned."
    )
    status = models.CharField(
        max_length=20,
        choices=BorrowStatus.choices,
        default=BorrowStatus.BORROWED,
        verbose_name="Status",
        help_text="Current status of this borrow record."
    )
    renew_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Renewal Count",
        help_text="Number of times this borrow has been renewed (max 2)."
    )
    remarks = models.TextField(
        blank=True,
        verbose_name="Remarks",
        help_text="Optional notes about this borrow transaction."
    )

    BORROW_DURATION_DAYS = 14
    MAX_RENEWALS = 2

    class Meta:
        verbose_name = "Borrow Record"
        verbose_name_plural = "Borrow Records"
        ordering = ["-borrow_date"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["member", "book", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.member.user.username} → {self.book.title} ({self.status})"

    def save(self, *args, **kwargs):
        """
        Auto-compute due_date on first save if not explicitly set.
        """
        if not self.due_date:
            from datetime import timedelta
            self.due_date = self.borrow_date + timedelta(days=self.BORROW_DURATION_DAYS)
        super().save(*args, **kwargs)


class FineStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PAID = "PAID", "Paid"
    WAIVED = "WAIVED", "Waived"


class Fine(BaseModel):
    """
    Tracks overdue fines associated with a specific BorrowRecord.
    """
    borrow_record = models.OneToOneField(
        BorrowRecord,
        on_delete=models.CASCADE,
        related_name="fine",
        verbose_name="Borrow Record",
        help_text="The associated borrow transaction."
    )
    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="fines",
        verbose_name="Member",
        help_text="The member who incurred the fine."
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name="Fine Amount",
        help_text="Calculated fine amount in ₹."
    )
    reason = models.CharField(
        max_length=255,
        default="Overdue book return fine.",
        verbose_name="Reason",
        help_text="Reason for the fine."
    )
    status = models.CharField(
        max_length=20,
        choices=FineStatus.choices,
        default=FineStatus.PENDING,
        verbose_name="Status",
        help_text="Fine status (Pending, Paid, Waived)."
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Paid/Waived At",
        help_text="Date and time when the fine was paid or waived."
    )

    class Meta:
        verbose_name = "Fine"
        verbose_name_plural = "Fines"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.member.user.username} - ₹{self.amount} ({self.status})"

