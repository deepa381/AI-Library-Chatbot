from django.utils import timezone
from .models import BorrowRecord, BorrowStatus, Fine, FineStatus
from decimal import Decimal

DAILY_FINE_RATE = Decimal('5.00')

def calculate_overdue_fines():
    """
    Scans all BORROWED records that are past their due_date.
    Calculates the overdue fine amount (₹5/day) up to the current date and creates/updates Fine records.
    """
    now = timezone.now()
    overdue_borrows = BorrowRecord.objects.filter(
        status=BorrowStatus.BORROWED,
        due_date__lt=now
    )
    
    for record in overdue_borrows:
        delta = now - record.due_date
        days_overdue = delta.days
        if days_overdue > 0:
            amount = days_overdue * DAILY_FINE_RATE
            fine, created = Fine.objects.get_or_create(
                borrow_record=record,
                member=record.member,
                defaults={
                    'amount': amount,
                    'reason': f"Overdue borrow (Active for {days_overdue} days overdue).",
                    'status': FineStatus.PENDING
                }
            )
            if not created and fine.status == FineStatus.PENDING:
                fine.amount = amount
                fine.reason = f"Overdue borrow (Active for {days_overdue} days overdue)."
                fine.save()


def check_and_create_fine_on_return(record):
    """
    Helper function triggered during return_book.
    If the return date is past the due date, create/update a Fine.
    """
    if record.return_date and record.return_date > record.due_date:
        delta = record.return_date - record.due_date
        days_overdue = delta.days
        if days_overdue > 0:
            amount = days_overdue * DAILY_FINE_RATE
            fine, created = Fine.objects.get_or_create(
                borrow_record=record,
                member=record.member,
                defaults={
                    'amount': amount,
                    'reason': f"Returned overdue by {days_overdue} days.",
                    'status': FineStatus.PENDING
                }
            )
            if not created and fine.status == FineStatus.PENDING:
                fine.amount = amount
                fine.reason = f"Returned overdue by {days_overdue} days."
                fine.save()
