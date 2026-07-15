from typing import Any
from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel

class MembershipType(models.TextChoices):
    STUDENT = "STUDENT", "Student"
    FACULTY = "FACULTY", "Faculty"
    STAFF = "STAFF", "Staff"
    STANDARD = "STANDARD", "Standard"
    PREMIUM = "PREMIUM", "Premium"


class UserRole(models.TextChoices):
    MEMBER = "MEMBER", "Member"
    LIBRARIAN = "LIBRARIAN", "Librarian"



class MemberProfile(BaseModel):
    """
    Extends the standard Django User model to store library-specific profile details.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="User Account",
        help_text="The associated Django User account."
    )
    membership_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Membership ID",
        help_text="Unique library membership identification code."
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Phone Number",
        help_text="Contact phone number."
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Department",
        help_text="Academic or administrative department (e.g. Computer Science)."
    )
    membership_type = models.CharField(
        max_length=20,
        choices=MembershipType.choices,
        default=MembershipType.STANDARD,
        verbose_name="Membership Type",
        help_text="The tier/type of library membership."
    )
    borrow_limit = models.PositiveIntegerField(
        default=5,
        verbose_name="Borrow Limit",
        help_text="Maximum number of books this user can borrow concurrently."
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.MEMBER,
        verbose_name="User Role",
        help_text="The role of this user (Member or Librarian)."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Designates whether this member profile is active."
    )

    class Meta:
        verbose_name = "Member Profile"
        verbose_name_plural = "Member Profiles"
        ordering = ["user__username"]

    def __str__(self) -> str:
        return f"{self.user.username} ({self.membership_id})"
