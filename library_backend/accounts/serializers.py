import re
from typing import Any
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import MemberProfile, UserRole, MembershipType

class MemberProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for library MemberProfile attributes.
    """
    class Meta:
        model = MemberProfile
        fields = [
            'membership_id', 'phone', 'department', 
            'membership_type', 'borrow_limit', 'role', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['membership_id', 'borrow_limit', 'role', 'is_active']


class UserSerializer(serializers.ModelSerializer):
    """
    Detailed User representation including nested profile details.
    """
    profile = MemberProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends standard JWT token claims and login response payloads with user roles.
    """
    @classmethod
    def get_token(cls, user: User) -> Any:
        token = super().get_token(user)
        # Add custom claims for frontends & decoders
        token['username'] = user.username
        token['email'] = user.email
        if hasattr(user, 'profile'):
            token['role'] = user.profile.role
            token['membership_id'] = user.profile.membership_id
        return token

    def validate(self, attrs: dict) -> dict:
        data = super().validate(attrs)
        # Add extra properties directly to JSON response body
        data['username'] = self.user.username
        data['email'] = self.user.email
        if hasattr(self.user, 'profile'):
            data['role'] = self.user.profile.role
            data['membership_id'] = self.user.profile.membership_id
        return data


class RegisterSerializer(serializers.Serializer):
    """
    Validates user registration and instantiates User & MemberProfile details.
    """
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email address already exists.")
        return value

    def validate(self, attrs: dict) -> dict:
        # Confirm password matching
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        # Run Django's robust built-in password policy validators
        try:
            # We mock-create a temporary User to pass to validator for contextual checks
            temp_user = User(username=attrs.get('username'), email=attrs.get('email'))
            validate_password(attrs['password'], user=temp_user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data: dict) -> User:
        # Extract profile fields
        phone = validated_data.pop('phone', '')
        department = validated_data.pop('department', '')
        password = validated_data.pop('password')
        validated_data.pop('password_confirm') # Discard

        with transaction.atomic():
            # Create user (this automatically fires the post_save signal creating the profile)
            user = User.objects.create_user(
                password=password,
                **validated_data
            )
            # Update the automatically created profile with specific registration details
            profile = user.profile
            profile.phone = phone
            profile.department = department
            profile.save()

        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    Validates password change request parameters.
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs: dict) -> dict:
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "New passwords do not match."})

        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({"old_password": "Wrong current password."})

        try:
            validate_password(attrs['new_password'], user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    """
    Validates user email exists before triggering reset tokens.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value: str) -> str:
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("No user is registered with this email address.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """
    Resolves password recovery via token verification.
    """
    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs: dict) -> dict:
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})

        try:
            uid = force_str(urlsafe_base64_decode(attrs['uidb64']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"token": "Invalid or expired link details."})

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({"token": "The reset token is invalid or has expired."})

        try:
            validate_password(attrs['new_password'], user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        self.context['user'] = user
        return attrs


# ============================================================
# Member Management Serializers (Module 5)
# ============================================================

class MemberListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing all members.
    Used in the list endpoint by librarians.
    """
    membership_id = serializers.CharField(source='profile.membership_id', read_only=True)
    membership_type = serializers.CharField(source='profile.membership_type', read_only=True)
    role = serializers.CharField(source='profile.role', read_only=True)
    is_active = serializers.BooleanField(source='profile.is_active', read_only=True)
    department = serializers.CharField(source='profile.department', read_only=True)
    phone = serializers.CharField(source='profile.phone', read_only=True)
    borrow_limit = serializers.IntegerField(source='profile.borrow_limit', read_only=True)
    member_since = serializers.DateTimeField(source='profile.created_at', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'membership_id', 'membership_type', 'role',
            'department', 'phone', 'borrow_limit',
            'is_active', 'member_since',
        ]


class MemberDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for retrieving detailed member information.
    """
    profile = MemberProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'date_joined', 'last_login', 'profile',
        ]


class MemberUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating member profile information.
    Librarians can update any editable field; members can only update their own phone and department.
    """
    phone = serializers.CharField(
        source='profile.phone',
        required=False,
        allow_blank=True,
        max_length=20,
        help_text="Contact phone number."
    )
    department = serializers.CharField(
        source='profile.department',
        required=False,
        allow_blank=True,
        max_length=100,
        help_text="Department of the member."
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'department']

    def validate_email(self, value: str) -> str:
        user = self.instance
        if User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone(self, value: str) -> str:
        """
        Validate phone has only digits, spaces, +, -, and parentheses.
        """
        if value and not all(c in '0123456789 +()-' for c in value):
            raise serializers.ValidationError(
                "Phone number may only contain digits, spaces, +, -, and parentheses."
            )
        return value

    def update(self, instance: User, validated_data: dict) -> User:
        profile_data = validated_data.pop('profile', {})

        # Update User model fields
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()

        # Update linked MemberProfile fields
        if profile_data and hasattr(instance, 'profile'):
            profile = instance.profile
            profile.phone = profile_data.get('phone', profile.phone)
            profile.department = profile_data.get('department', profile.department)
            profile.save()

        return instance


class MembershipUpdateSerializer(serializers.Serializer):
    """
    Validates and applies a membership type change. Librarians only.
    """
    membership_type = serializers.ChoiceField(
        choices=MembershipType.choices,
        help_text=f"Valid options: {', '.join([c[0] for c in MembershipType.choices])}"
    )


class BorrowLimitSerializer(serializers.Serializer):
    """
    Validates and applies a borrow limit change. Librarians only.
    """
    borrow_limit = serializers.IntegerField(
        min_value=1,
        max_value=50,
        help_text="The maximum number of books the member can borrow concurrently (1-50)."
    )

