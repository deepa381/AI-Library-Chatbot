from django.contrib import admin
from .models import BorrowRecord

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'member', 'book', 'borrow_date', 'due_date', 'return_date', 'status', 'renew_count']
    list_filter = ['status', 'borrow_date', 'due_date', 'return_date']
    search_fields = ['book__title', 'member__user__username', 'member__membership_id']
    readonly_fields = ['created_at', 'updated_at']
