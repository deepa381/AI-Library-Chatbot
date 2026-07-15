import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import MemberProfile, MembershipType, UserRole

@receiver(post_save, sender=User)
def create_member_profile(sender, instance, created, **kwargs):
    """
    Signal handler to automatically generate a MemberProfile
    whenever a new Django User is created.
    """
    if created:
        # Generate a unique membership ID
        unique_suffix = uuid.uuid4().hex[:8].upper()
        membership_id = f"MEM-{unique_suffix}"

        # Assign LIBRARIAN role automatically for staff/superuser accounts
        role = UserRole.MEMBER
        if instance.is_staff or instance.is_superuser:
            role = UserRole.LIBRARIAN

        MemberProfile.objects.create(
            user=instance,
            membership_id=membership_id,
            membership_type=MembershipType.STANDARD,
            borrow_limit=5,
            role=role,
            is_active=True
        )

@receiver(post_save, sender=User)
def save_member_profile(sender, instance, **kwargs):
    """
    Signal handler to save the associated MemberProfile when the User is saved.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
