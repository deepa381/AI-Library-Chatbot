from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count, Sum, Q
from django.utils.dateparse import parse_date
from accounts.models import UserRole, MemberProfile
from books.models import Book
from borrow.models import BorrowRecord, Fine, BorrowStatus
from reservations.models import Reservation


class BaseReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_date_range(self, request):
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')
        
        date_from = parse_date(date_from_str) if date_from_str else None
        date_to = parse_date(date_to_str) if date_to_str else None
        
        return date_from, date_to

    def is_librarian(self, user):
        return (
            user.is_staff or user.is_superuser or
            (hasattr(user, 'profile') and user.profile.role == UserRole.LIBRARIAN)
        )


class BorrowReportView(BaseReportView):
    """
    Report of borrow activities within a date range.
    """
    def get(self, request, *args, **kwargs):
        date_from, date_to = self.get_date_range(request)
        qs = BorrowRecord.objects.select_related('member__user', 'book').all()

        if not self.is_librarian(request.user):
            if hasattr(request.user, 'profile'):
                qs = qs.filter(member=request.user.profile)
            else:
                qs = qs.none()

        if date_from:
            qs = qs.filter(borrow_date__date__gte=date_from)
        if date_to:
            qs = qs.filter(borrow_date__date__lte=date_to)

        data = [
            {
                "id": record.id,
                "book_title": record.book.title,
                "member_username": record.member.user.username,
                "membership_id": record.member.membership_id,
                "borrow_date": record.borrow_date,
                "due_date": record.due_date,
                "return_date": record.return_date,
                "status": record.status,
                "renew_count": record.renew_count
            }
            for record in qs
        ]
        return Response(data, status=status.HTTP_200_OK)


class ReservationReportView(BaseReportView):
    """
    Report of reservations placed within a date range.
    """
    def get(self, request, *args, **kwargs):
        date_from, date_to = self.get_date_range(request)
        qs = Reservation.objects.select_related('member__user', 'book').all()

        if not self.is_librarian(request.user):
            if hasattr(request.user, 'profile'):
                qs = qs.filter(member=request.user.profile)
            else:
                qs = qs.none()

        if date_from:
            qs = qs.filter(reservation_date__date__gte=date_from)
        if date_to:
            qs = qs.filter(reservation_date__date__lte=date_to)

        data = [
            {
                "id": res.id,
                "book_title": res.book.title,
                "member_username": res.member.user.username,
                "membership_id": res.member.membership_id,
                "reservation_date": res.reservation_date,
                "expiry_date": res.expiry_date,
                "status": res.status,
                "queue_position": res.queue_position
            }
            for res in qs
        ]
        return Response(data, status=status.HTTP_200_OK)


class FineReportView(BaseReportView):
    """
    Report of overdue fines incurred within a date range.
    """
    def get(self, request, *args, **kwargs):
        date_from, date_to = self.get_date_range(request)
        qs = Fine.objects.select_related('member__user', 'borrow_record__book').all()

        if not self.is_librarian(request.user):
            if hasattr(request.user, 'profile'):
                qs = qs.filter(member=request.user.profile)
            else:
                qs = qs.none()

        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        data = [
            {
                "id": fine.id,
                "book_title": fine.borrow_record.book.title,
                "member_username": fine.member.user.username,
                "amount": float(fine.amount),
                "reason": fine.reason,
                "status": fine.status,
                "created_at": fine.created_at,
                "paid_at": fine.paid_at
            }
            for fine in qs
        ]
        return Response(data, status=status.HTTP_200_OK)


class MemberActivityReportView(BaseReportView):
    """
    Summary of activity per member.
    """
    def get(self, request, *args, **kwargs):
        date_from, date_to = self.get_date_range(request)
        qs = MemberProfile.objects.select_related('user').filter(role=UserRole.MEMBER)

        if not self.is_librarian(request.user):
            if hasattr(request.user, 'profile'):
                qs = qs.filter(id=request.user.profile.id)
            else:
                qs = qs.none()

        # Build custom querysets or annotations
        data = []
        for profile in qs:
            # Query filters based on dates
            borrows_qs = BorrowRecord.objects.filter(member=profile)
            res_qs = Reservation.objects.filter(member=profile)
            fines_qs = Fine.objects.filter(member=profile)

            if date_from:
                borrows_qs = borrows_qs.filter(borrow_date__date__gte=date_from)
                res_qs = res_qs.filter(reservation_date__date__gte=date_from)
                fines_qs = fines_qs.filter(created_at__date__gte=date_from)
            if date_to:
                borrows_qs = borrows_qs.filter(borrow_date__date__lte=date_to)
                res_qs = res_qs.filter(reservation_date__date__lte=date_to)
                fines_qs = fines_qs.filter(created_at__date__lte=date_to)

            total_borrows = borrows_qs.count()
            active_borrows = borrows_qs.filter(status=BorrowStatus.BORROWED).count()
            total_reservations = res_qs.count()
            total_unpaid_fines = fines_qs.filter(status='PENDING').aggregate(total=Sum('amount'))['total'] or 0.00
            total_paid_fines = fines_qs.filter(status='PAID').aggregate(total=Sum('amount'))['total'] or 0.00

            data.append({
                "username": profile.user.username,
                "membership_id": profile.membership_id,
                "total_borrows": total_borrows,
                "active_borrows": active_borrows,
                "total_reservations": total_reservations,
                "total_unpaid_fines": float(total_unpaid_fines),
                "total_paid_fines": float(total_paid_fines)
            })

        return Response(data, status=status.HTTP_200_OK)


class BookPopularityReportView(BaseReportView):
    """
    Listing books ranked by popularity (total borrows) during the date range.
    """
    def get(self, request, *args, **kwargs):
        date_from, date_to = self.get_date_range(request)

        # Filters popular books
        borrow_filter = Q()
        if date_from:
            borrow_filter &= Q(borrow_records__borrow_date__date__gte=date_from)
        if date_to:
            borrow_filter &= Q(borrow_records__borrow_date__date__lte=date_to)

        books = Book.objects.annotate(
            borrow_count=Count('borrow_records', filter=borrow_filter)
        ).order_by('-borrow_count')

        data = [
            {
                "id": book.id,
                "title": book.title,
                "isbn": book.isbn,
                "borrow_count": book.borrow_count
            }
            for book in books
        ]
        return Response(data, status=status.HTTP_200_OK)
