from django.contrib import admin
from .models import MemberProfile

@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "membership_id",
        "membership_type",
        "borrow_limit",
        "phone",
        "department",
        "role",
        "is_active",
        "created_at",
    )
    list_display_links = ("id", "user", "membership_id")
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "membership_id",
        "department",
    )
    list_filter = ("role", "membership_type", "is_active", "department")
    ordering = ("user__username",)
    date_hierarchy = "created_at"

    fieldsets = (
        ("Account Connection", {
            "fields": ("user",)
        }),
        ("Membership details", {
            "fields": ("membership_id", "membership_type", "borrow_limit")
        }),
        ("Contact & Department", {
            "fields": ("phone", "department")
        }),
        ("Status & Role", {
            "fields": ("role", "is_active",)
        }),
    )
