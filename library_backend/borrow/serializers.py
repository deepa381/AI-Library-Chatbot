from rest_framework import serializers
from accounts.serializers import MemberProfileSerializer
from books.serializers import BookSerializer
from .models import BorrowRecord, BorrowStatus, Fine, FineStatus
from books.models import Book
from accounts.models import MemberProfile


class BorrowRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for representing a detailed BorrowRecord.
    Includes nested member profile details and book details.
    """
    member = MemberProfileSerializer(read_only=True)
    book = BookSerializer(read_only=True)

    class Meta:
        model = BorrowRecord
        fields = [
            'id', 'member', 'book', 'borrow_date', 'due_date',
            'return_date', 'status', 'renew_count', 'remarks',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class BorrowCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new BorrowRecord.
    Enforces business rules on initialization and validation.
    """
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source='book',
        help_text="The ID of the book to borrow."
    )
    remarks = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = BorrowRecord
        fields = ['book_id', 'remarks']

    def validate(self, attrs):
        user = self.context['request'].user
        
        # Ensure the user has a profile
        if not hasattr(user, 'profile'):
            raise serializers.ValidationError("This user does not have a member profile.")
        
        member_profile = user.profile

        # Rule: Member must be active
        if not member_profile.is_active:
            raise serializers.ValidationError("Inactive members cannot borrow books.")

        book = attrs['book']

        # Rule: A member cannot borrow the same book twice before returning it
        active_borrow = BorrowRecord.objects.filter(
            member=member_profile,
            book=book,
            status=BorrowStatus.BORROWED
        ).exists()
        if active_borrow:
            raise serializers.ValidationError("You have already borrowed this book and have not returned it yet.")

        # Rule: Book must have available copies
        if book.available_copies <= 0:
            raise serializers.ValidationError("There are no available copies of this book currently.")

        # Rule: A member cannot borrow more than their borrow_limit
        active_borrows_count = BorrowRecord.objects.filter(
            member=member_profile,
            status=BorrowStatus.BORROWED
        ).count()
        if active_borrows_count >= member_profile.borrow_limit:
            raise serializers.ValidationError(
                f"You have reached your borrow limit of {member_profile.borrow_limit} books."
            )

        return attrs


class BorrowReturnSerializer(serializers.Serializer):
    """
    Serializer for returning a book.
    """
    remarks = serializers.CharField(required=False, allow_blank=True)


class BorrowRenewSerializer(serializers.Serializer):
    """
    Serializer for renewing a book.
    """
    remarks = serializers.CharField(required=False, allow_blank=True)


class FineSerializer(serializers.ModelSerializer):
    """
    Serializer representing detailed Fine records.
    """
    member = MemberProfileSerializer(read_only=True)
    borrow_record = BorrowRecordSerializer(read_only=True)

    class Meta:
        model = Fine
        fields = [
            'id', 'borrow_record', 'member', 'amount', 'reason',
            'status', 'created_at', 'paid_at'
        ]
        read_only_fields = fields

