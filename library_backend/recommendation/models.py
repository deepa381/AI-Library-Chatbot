from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel
from books.models import Book

class RecommendationMetadata(BaseModel):
    book = models.OneToOneField(
        Book,
        on_delete=models.CASCADE,
        related_name="recommendation_metadata",
        verbose_name="Book"
    )
    mood = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Mood",
        help_text="Mood tags separated by semicolons."
    )
    writing_style = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Writing Style",
        help_text="Writing styles separated by semicolons."
    )
    difficulty_level = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Difficulty Level"
    )
    reading_level = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Reading Level"
    )
    target_audience = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Target Audience"
    )
    learning_outcomes = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Learning Outcomes"
    )
    skills_covered = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Skills Covered"
    )
    recommendation_keywords = models.TextField(
        blank=True,
        verbose_name="Recommendation Keywords"
    )
    fantasy_elements = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Fantasy Elements"
    )
    scifi_elements = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Sci-Fi Elements"
    )
    themes = models.TextField(
        blank=True,
        verbose_name="Themes"
    )
    keywords = models.TextField(
        blank=True,
        verbose_name="Keywords"
    )
    tags = models.TextField(
        blank=True,
        verbose_name="Tags"
    )
    subjects = models.TextField(
        blank=True,
        verbose_name="Subjects"
    )

    class Meta:
        verbose_name = "Recommendation Metadata"
        verbose_name_plural = "Recommendation Metadata"

    def __str__(self) -> str:
        return f"Recommendation Metadata for {self.book.title}"


class SimilarBook(BaseModel):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="similar_books_source",
        verbose_name="Source Book"
    )
    similar_book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="similar_books_target",
        verbose_name="Similar Book"
    )
    similarity_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        verbose_name="Similarity Score"
    )
    rank = models.PositiveIntegerField(
        verbose_name="Rank"
    )

    class Meta:
        verbose_name = "Similar Book"
        verbose_name_plural = "Similar Books"
        ordering = ["book", "rank"]
        unique_together = (("book", "similar_book"),)

    def __str__(self) -> str:
        return f"{self.book.title} -> {self.similar_book.title} ({self.similarity_score})"


class RecommendationHistory(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recommendation_histories",
        verbose_name="User"
    )
    query = models.TextField(
        verbose_name="Query"
    )
    recommended_books = models.ManyToManyField(
        Book,
        related_name="recommendation_histories",
        verbose_name="Recommended Books"
    )
    response = models.TextField(
        verbose_name="Response"
    )

    class Meta:
        verbose_name = "Recommendation History"
        verbose_name_plural = "Recommendation Histories"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.query[:50]}"

