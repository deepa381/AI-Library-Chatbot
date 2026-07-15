from rest_framework import serializers
from .models import Reservation, ReservationStatus
from accounts.serializers import MemberProfileSerializer
from books.serializers import BookSerializer
from books.models import Book


class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed Reservation details.
    """
    member = MemberProfileSerializer(read_only=True)
    book = BookSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'member', 'book', 'reservation_date', 'expiry_date',
            'status', 'queue_position', 'remarks', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class ReservationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for placing a reservation.
    """
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source='book',
        help_text="The ID of the book to reserve."
    )
    remarks = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Reservation
        fields = ['book_id', 'remarks']

    def validate(self, attrs):
        user = self.context['request'].user
        if not hasattr(user, 'profile'):
            raise serializers.ValidationError("This user does not have a member profile.")
        
        member_profile = user.profile
        if not member_profile.is_active:
            raise serializers.ValidationError("Inactive members cannot make reservations.")

        book = attrs['book']

        # Rule: A reservation is only allowed when available_copies == 0
        if book.available_copies > 0:
            raise serializers.ValidationError(
                "Reservations are only allowed when there are no available physical copies of the book."
            )

        # Rule: A member cannot reserve the same book twice (active/waiting state)
        duplicate = Reservation.objects.filter(
            member=member_profile,
            book=book,
            status__in=[ReservationStatus.WAITING, ReservationStatus.ACTIVE]
        ).exists()
        if duplicate:
            raise serializers.ValidationError("You already have an active or waiting reservation for this book.")

        return attrs
