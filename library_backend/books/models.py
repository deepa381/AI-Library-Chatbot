import datetime
import re
from typing import Any
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import BaseModel

def validate_isbn(value: str) -> None:
    """
    Validates that a string is a valid ISBN-10 or ISBN-13 format.
    Hyphens and spaces are stripped during validation.
    """
    clean_value = re.sub(r'[-\s]', '', value)
    if not re.match(r'^(?:\d{9}[\dX]|\d{13})$', clean_value, re.IGNORECASE):
        raise ValidationError("ISBN must be a valid 10 or 13-digit format (spaces and hyphens allowed).")

def validate_publication_year(value: int) -> None:
    """
    Validates that the publication year is not too far in the past or in the future.
    """
    current_year = datetime.date.today().year
    if value < 800:
        raise ValidationError("Publication year cannot be earlier than 800 AD.")
    if value > current_year + 1:
        raise ValidationError(f"Publication year cannot be in the future (maximum allowed: {current_year + 1}).")

def validate_past_date(value: datetime.date) -> None:
    """
    Validates that the date of birth is not in the future.
    """
    if value > datetime.date.today():
        raise ValidationError("Date of birth cannot be in the future.")


class Author(BaseModel):
    """
    Represents a book author.
    """
    first_name = models.CharField(
        max_length=150,
        verbose_name="First Name",
        help_text="Author's first name."
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name="Last Name",
        help_text="Author's last name."
    )
    biography = models.TextField(
        blank=True,
        verbose_name="Biography",
        help_text="Brief biography or history of the author."
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Country of Origin",
        help_text="Country where the author is from."
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        validators=[validate_past_date],
        verbose_name="Date of Birth",
        help_text="Author's date of birth."
    )
    website = models.URLField(
        null=True,
        blank=True,
        verbose_name="Website",
        help_text="Official website of the author."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Designates whether this author should be treated as active."
    )

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Publisher(BaseModel):
    """
    Represents a publishing house.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Publisher Name",
        help_text="Unique name of the publishing company."
    )
    address = models.TextField(
        blank=True,
        verbose_name="Address",
        help_text="Physical or billing address of the publisher."
    )
    website = models.URLField(
        null=True,
        blank=True,
        verbose_name="Website",
        help_text="Publisher's website."
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name="Email Address",
        help_text="Contact email of the publisher."
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Phone Number",
        help_text="Contact phone number."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Designates whether this publisher is active."
    )

    class Meta:
        verbose_name = "Publisher"
        verbose_name_plural = "Publishers"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.name


class Category(BaseModel):
    """
    Represents a classification category for books (e.g., Fiction, Science).
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Category Name",
        help_text="Unique name of the category."
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Detailed description of what this category encompasses."
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        verbose_name="Slug",
        help_text="URL-friendly slug for the category."
    )

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Tag(BaseModel):
    """
    Represents a descriptive label or tag for books (useful for granular indexing and AI logic).
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Tag Name",
        help_text="Unique tag word or phrase."
    )
    slug = models.SlugField(
        max_length=60,
        unique=True,
        verbose_name="Slug",
        help_text="URL-friendly slug for the tag."
    )

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class BookStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Available"
    OUT_OF_STOCK = "OUT_OF_STOCK", "Out of Stock"
    RESERVED = "RESERVED", "Reserved"
    MAINTENANCE = "MAINTENANCE", "Under Maintenance"


class BookLanguage(models.TextChoices):
    ENGLISH = "EN", "English"
    SPANISH = "ES", "Spanish"
    FRENCH = "FR", "French"
    GERMAN = "DE", "German"
    CHINESE = "ZH", "Chinese"
    JAPANESE = "JA", "Japanese"
    ARABIC = "AR", "Arabic"
    HINDI = "HI", "Hindi"
    OTHER = "OTHER", "Other"


class Book(BaseModel):
    """
    Represents a library book.
    Contains structural, metadata, availability, and localization information.
    """
    isbn = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_isbn],
        verbose_name="ISBN",
        help_text="Unique 10 or 13-digit International Standard Book Number."
    )
    title = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Title",
        help_text="Main title of the book."
    )
    subtitle = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Subtitle",
        help_text="Sub-title of the book (if any)."
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Detailed summary or synopsis of the book."
    )
    publication_year = models.IntegerField(
        validators=[validate_publication_year],
        verbose_name="Publication Year",
        help_text="Year the book was published."
    )
    edition = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Edition",
        help_text="Edition info (e.g. '1st Edition', 'Revised')."
    )
    language = models.CharField(
        max_length=10,
        choices=BookLanguage.choices,
        default=BookLanguage.ENGLISH,
        verbose_name="Language",
        help_text="Primary language of the book."
    )
    pages = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Pages",
        help_text="Total number of pages."
    )
    cover_image = models.ImageField(
        upload_to="book_covers/",
        null=True,
        blank=True,
        verbose_name="Cover Image",
        help_text="Uploaded cover artwork of the book."
    )
    total_copies = models.PositiveIntegerField(
        default=1,
        verbose_name="Total Copies",
        help_text="Total physical copies owned by the library."
    )
    available_copies = models.PositiveIntegerField(
        default=1,
        verbose_name="Available Copies",
        help_text="Copies currently on shelf and available for borrowing."
    )
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)],
        verbose_name="Average Rating",
        help_text="User rating score from 0.00 to 5.00."
    )
    status = models.CharField(
        max_length=20,
        choices=BookStatus.choices,
        default=BookStatus.AVAILABLE,
        verbose_name="Status",
        help_text="Current overall status of the book."
    )
    shelf_location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Shelf Location",
        help_text="Physical location coordinates in the library (e.g. 'Aisle 3, Shelf B')."
    )

    # Relationships
    authors = models.ManyToManyField(
        Author,
        related_name="books",
        verbose_name="Authors",
        help_text="Authors who wrote the book."
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name="books",
        verbose_name="Publisher",
        help_text="Company that published the book."
    )
    categories = models.ManyToManyField(
        Category,
        related_name="books",
        verbose_name="Categories",
        help_text="Categories under which this book is classified."
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="books",
        verbose_name="Tags",
        help_text="Descriptive tags used for recommendation engine indexing."
    )

    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["isbn"]),
            models.Index(fields=["title"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        """
        Validates model state coherence before saving.
        """
        super().clean()
        
        # Standardize ISBN: remove hyphens/spaces and uppercase X
        if self.isbn:
            self.isbn = re.sub(r'[-\s]', '', self.isbn).upper()

        if self.available_copies > self.total_copies:
            raise ValidationError({
                "available_copies": "Available copies cannot exceed total copies owned."
            })

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Ensure clean() validation is run on save.
        """
        self.full_clean()
        super().save(*args, **kwargs)
