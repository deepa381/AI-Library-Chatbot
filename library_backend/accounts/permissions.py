from rest_framework import permissions
from .models import UserRole

class IsLibrarian(permissions.BasePermission):
    """
    Allows access only to authenticated users with LIBRARIAN role,
    or Django superusers/staff.
    """
    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
            
        # Support Django staff/superusers directly
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Check role in MemberProfile
        return hasattr(request.user, 'profile') and request.user.profile.role == UserRole.LIBRARIAN


class IsMember(permissions.BasePermission):
    """
    Allows access only to authenticated users with MEMBER role.
    """
    def has_permission(self, request, view) -> bool:
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'profile') and 
            request.user.profile.role == UserRole.MEMBER
        )
