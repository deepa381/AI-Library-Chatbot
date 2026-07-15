from django.contrib import admin
from .models import Author, Publisher, Category, Tag, Book

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "country",
        "date_of_birth",
        "is_active",
        "created_at",
    )
    list_display_links = ("id", "first_name", "last_name")
    search_fields = ("first_name", "last_name", "country")
    list_filter = ("is_active", "country")
    ordering = ("last_name", "first_name")
    date_hierarchy = "created_at"


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "email",
        "phone",
        "website",
        "is_active",
        "created_at",
    )
    list_display_links = ("id", "name")
    search_fields = ("name", "email", "phone")
    list_filter = ("is_active",)
    ordering = ("name",)
    date_hierarchy = "created_at"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "created_at")
    list_display_links = ("id", "name")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    date_hierarchy = "created_at"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "created_at")
    list_display_links = ("id", "name")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    date_hierarchy = "created_at"


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "isbn",
        "title",
        "publisher",
        "language",
        "total_copies",
        "available_copies",
        "average_rating",
        "status",
        "created_at",
    )
    list_display_links = ("isbn", "title")
    search_fields = ("isbn", "title", "subtitle", "description", "publisher__name")
    list_filter = ("status", "language", "publisher", "categories")
    ordering = ("-created_at",)
    filter_horizontal = ("authors", "categories", "tags")
    date_hierarchy = "created_at"
    readonly_fields = ("average_rating",)  # Typically managed via reviews/ratings later

    fieldsets = (
        ("Basic Information", {
            "fields": ("isbn", "title", "subtitle", "description", "language", "pages")
        }),
        ("Authors & Classifications", {
            "fields": ("authors", "publisher", "categories", "tags")
        }),
        ("Inventory & Location", {
            "fields": ("total_copies", "available_copies", "status", "shelf_location")
        }),
        ("Media & Metrics", {
            "fields": ("cover_image", "average_rating")
        }),
    )
