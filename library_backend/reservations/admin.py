from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['id', 'member', 'book', 'reservation_date', 'expiry_date', 'status', 'queue_position']
    list_filter = ['status', 'reservation_date', 'expiry_date']
    search_fields = ['book__title', 'member__user__username', 'member__membership_id']
    readonly_fields = ['created_at', 'updated_at']
