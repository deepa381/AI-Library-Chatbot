from typing import Any
import logging
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import generics, status, permissions, viewsets, filters
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserRole

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    MemberListSerializer,
    MemberDetailSerializer,
    MemberUpdateSerializer,
    MembershipUpdateSerializer,
    BorrowLimitSerializer,
)

logger = logging.getLogger(__name__)
from .permissions import IsLibrarian

class RegisterView(generics.GenericAPIView):
    """
    Enables registration for new library members.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Return registered user profile details
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """
    Handles logging in and returns JWT access and refresh tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """
    Logs out the authenticated user by blacklisting their refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response(
                {"detail": "Invalid or expired token provided."},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieves or updates the authenticated user's profile details.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self) -> User:
        return self.request.user

    def update(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        user = self.get_object()
        
        # Extract and update user model fields
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.save()

        # Extract and update associated profile fields
        if hasattr(user, 'profile'):
            profile = user.profile
            profile.phone = request.data.get('phone', profile.phone)
            profile.department = request.data.get('department', profile.department)
            profile.save()

        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(generics.GenericAPIView):
    """
    Allows authenticated users to change their account password.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response(
            {"detail": "Password has been successfully updated."},
            status=status.HTTP_200_OK
        )


class ForgotPasswordView(generics.GenericAPIView):
    """
    Initiates password recovery.
    Generates a recovery token, prints it to log/console, and returns it.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ForgotPasswordSerializer

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email__iexact=email)

        # Generate reset token and uid payload
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # Output to system log to simulate SMTP email transmission
        logger.info(f"[PASSWORD RESET DETECTED] User: {user.username} | Email: {user.email}")
        logger.info(f"Reset Link variables: uidb64={uidb64} | token={token}")

        return Response({
            "detail": "Password reset token successfully generated.",
            "uidb64": uidb64,
            "token": token
        }, status=status.HTTP_200_OK)


class ResetPasswordView(generics.GenericAPIView):
    """
    Completes password recovery by validating the generated reset token.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.context['user']
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response(
            {"detail": "Password has been successfully reset."},
            status=status.HTTP_200_OK
        )


# ============================================================
# Member Management ViewSet (Module 5)
# ============================================================

class MemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet providing full member management capabilities.

    Librarians have full read/write access to all members.
    Members can only read and update their own profile (phone/department only).
    Anonymous users are denied all access.
    """
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'username', 'email',
        'profile__membership_id',
        'profile__department',
        'profile__phone',
    ]
    ordering_fields = ['username', 'profile__membership_id', 'date_joined']
    ordering = ['username']
    http_method_names = ['get', 'patch', 'delete', 'post', 'head', 'options']

    def get_queryset(self):
        """
        Optimized queryset with select_related and dynamic filtering.
        Librarians see all members; standard members see only themselves.
        """
        qs = User.objects.select_related('profile').all()

        user = self.request.user
        is_librarian = (
            user.is_staff or user.is_superuser or
            (hasattr(user, 'profile') and user.profile.role == UserRole.LIBRARIAN)
        )
        if not is_librarian:
            qs = qs.filter(pk=user.pk)

        # Apply query param filters
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(profile__role__iexact=role)

        membership_type = self.request.query_params.get('membership_type')
        if membership_type:
            qs = qs.filter(profile__membership_type__iexact=membership_type)

        department = self.request.query_params.get('department')
        if department:
            qs = qs.filter(profile__department__iexact=department)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            active_bool = is_active.lower() in ('true', '1', 'yes')
            qs = qs.filter(profile__is_active=active_bool)

        return qs.distinct()

    def get_serializer_class(self):
        """
        Dynamically select the appropriate serializer based on action.
        """
        if self.action == 'list':
            return MemberListSerializer
        if self.action in ['update', 'partial_update']:
            return MemberUpdateSerializer
        return MemberDetailSerializer

    def get_permissions(self):
        """
        Permission mapping:
        - Authenticated users can retrieve/update (members restricted to own data).
        - Only librarians can list all, delete, or use custom admin actions.
        """
        if self.action in [
            'activate', 'deactivate', 'change_membership',
            'change_borrow_limit', 'list', 'destroy'
        ]:
            return [IsLibrarian()]
        return [permissions.IsAuthenticated()]

    def update(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Override update to enforce field-level permissions.
        Members can only update phone and department on their own profile.
        """
        instance = self.get_object()
        user = request.user
        is_librarian = (
            user.is_staff or user.is_superuser or
            (hasattr(user, 'profile') and user.profile.role == UserRole.LIBRARIAN)
        )

        # Members can only edit their own profile
        if not is_librarian and instance.pk != user.pk:
            return Response(
                {'detail': 'You do not have permission to edit other members.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Members are restricted from updating privileged fields
        if not is_librarian:
            restricted_fields = {'email', 'first_name', 'last_name'}
            rejected = restricted_fields.intersection(set(request.data.keys()))
            if rejected:
                return Response(
                    {'detail': (
                        f'Members cannot modify: {", ".join(sorted(rejected))}. '
                        'Only phone and department are editable.'
                    )},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MemberDetailSerializer(instance).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request: Any, pk: Any = None) -> Response:
        """
        Activate a deactivated member profile. Librarians only.
        """
        member = self.get_object()
        if not hasattr(member, 'profile'):
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        member.profile.is_active = True
        member.profile.save()
        return Response(
            {'detail': f'Member "{member.username}" has been activated.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request: Any, pk: Any = None) -> Response:
        """
        Deactivate an active member profile. Librarians only.
        """
        member = self.get_object()
        if not hasattr(member, 'profile'):
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        member.profile.is_active = False
        member.profile.save()
        return Response(
            {'detail': f'Member "{member.username}" has been deactivated.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='change-membership')
    def change_membership(self, request: Any, pk: Any = None) -> Response:
        """
        Change the membership type of a member. Librarians only.
        """
        member = self.get_object()
        serializer = MembershipUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member.profile.membership_type = serializer.validated_data['membership_type']
        member.profile.save()
        return Response(
            {'detail': f'Membership type updated to "{member.profile.membership_type}" for "{member.username}".'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='change-borrow-limit')
    def change_borrow_limit(self, request: Any, pk: Any = None) -> Response:
        """
        Update the borrow limit for a member. Librarians only.
        """
        member = self.get_object()
        serializer = BorrowLimitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member.profile.borrow_limit = serializer.validated_data['borrow_limit']
        member.profile.save()
        return Response(
            {'detail': f'Borrow limit updated to {member.profile.borrow_limit} for "{member.username}".'},
            status=status.HTTP_200_OK
        )
