from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import MemberProfile, MembershipType, UserRole

class MemberProfileModelTests(TestCase):
    def test_member_profile_automatically_created_on_user_creation(self) -> None:
        # Create user; signals should automatically generate MemberProfile
        user = User.objects.create_user(
            username="auto_member",
            email="auto@library.org",
            password="securepassword123"
        )
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsNotNone(user.profile.membership_id)
        self.assertTrue(user.profile.membership_id.startswith("MEM-"))
        self.assertEqual(user.profile.role, UserRole.MEMBER)
        self.assertEqual(str(user.profile), f"auto_member ({user.profile.membership_id})")


class AuthAPITests(APITestCase):
    def setUp(self) -> None:
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.profile_url = reverse('accounts:profile')
        self.change_password_url = reverse('accounts:change_password')
        self.forgot_password_url = reverse('accounts:forgot_password')
        self.reset_password_url = reverse('accounts:reset_password')

        # Create standard member
        self.member_user = User.objects.create_user(
            username="jane_member",
            email="jane@library.org",
            password="StrongPassword123!"
        )
        # Create librarian
        self.librarian_user = User.objects.create_user(
            username="john_librarian",
            email="john@library.org",
            password="StrongPassword123!",
            is_staff=True
        )

    def test_registration_success(self) -> None:
        data = {
            "username": "new_user",
            "email": "new@library.org",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "New",
            "last_name": "User",
            "phone": "1234567890",
            "department": "Engineering"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], "new_user")
        self.assertEqual(response.data['profile']['phone'], "1234567890")

    def test_registration_duplicate_username_fails(self) -> None:
        data = {
            "username": "jane_member", # Duplicate
            "email": "another@library.org",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_registration_duplicate_email_fails(self) -> None:
        data = {
            "username": "unique_username",
            "email": "jane@library.org", # Duplicate
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_login_success_jwt_generation(self) -> None:
        data = {
            "username": "jane_member",
            "password": "StrongPassword123!"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['role'], UserRole.MEMBER)

    def test_login_invalid_password_fails(self) -> None:
        data = {
            "username": "jane_member",
            "password": "WrongPassword"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_retrieval_requires_jwt(self) -> None:
        # Request profile without auth token
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticate
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], "jane_member")

    def test_profile_update_success(self) -> None:
        self.client.force_authenticate(user=self.member_user)
        data = {
            "first_name": "Jane Updated",
            "phone": "555-555-5555",
            "department": "Mathematics"
        }
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], "Jane Updated")
        self.assertEqual(response.data['profile']['phone'], "555-555-5555")
        self.assertEqual(response.data['profile']['department'], "Mathematics")

    def test_password_change_success(self) -> None:
        self.client.force_authenticate(user=self.member_user)
        data = {
            "old_password": "StrongPassword123!",
            "new_password": "NewStrongPassword123!",
            "new_password_confirm": "NewStrongPassword123!"
        }
        response = self.client.post(self.change_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test login with new password
        self.client.logout()
        login_data = {
            "username": "jane_member",
            "password": "NewStrongPassword123!"
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_password_reset_flow_simulated(self) -> None:
        # 1. Forgot password request
        forgot_data = {"email": "jane@library.org"}
        forgot_response = self.client.post(self.forgot_password_url, forgot_data, format='json')
        self.assertEqual(forgot_response.status_code, status.HTTP_200_OK)
        self.assertIn('uidb64', forgot_response.data)
        self.assertIn('token', forgot_response.data)

        # 2. Reset password using generated token
        reset_data = {
            "uidb64": forgot_response.data['uidb64'],
            "token": forgot_response.data['token'],
            "new_password": "RecoveredPassword123!",
            "new_password_confirm": "RecoveredPassword123!"
        }
        reset_response = self.client.post(self.reset_password_url, reset_data, format='json')
        self.assertEqual(reset_response.status_code, status.HTTP_200_OK)

        # 3. Verify new password allows login
        login_data = {
            "username": "jane_member",
            "password": "RecoveredPassword123!"
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_unauthorized_access_to_librarian_book_management_fails(self) -> None:
        # Standard member trying to create a book
        self.client.force_authenticate(user=self.member_user)
        book_list_url = reverse('books:book-list')
        data = {
            "isbn": "9781111111111",
            "title": "Hack the Library",
            "publication_year": 2026,
            "publisher": 1 # dummy
        }
        response = self.client.post(book_list_url, data, format='json')
        # Standard member has role MEMBER, not LIBRARIAN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ============================================================
# Module 5 – Member Management API Tests
# ============================================================

class MemberManagementAPITests(APITestCase):
    """
    Integration tests for the MemberViewSet.
    Covers librarian full access, member self-only access, and all custom actions.
    """

    def setUp(self) -> None:
        # Librarian user
        self.librarian = User.objects.create_user(
            username='librarian_test', email='librarian@library.org',
            password='LibPass123!'
        )
        self.librarian.profile.role = UserRole.LIBRARIAN
        self.librarian.profile.save()

        # Regular member user
        self.member = User.objects.create_user(
            username='member_test', email='member@library.org',
            password='MemberPass123!'
        )

        # Second member to test isolation
        self.other_member = User.objects.create_user(
            username='other_member', email='other@library.org',
            password='OtherPass123!'
        )

        self.members_list_url = '/api/members/'

    def _member_detail_url(self, pk: int) -> str:
        return f'/api/members/{pk}/'

    def _member_action_url(self, pk: int, action: str) -> str:
        return f'/api/members/{pk}/{action}/'

    # ── List Endpoint ──────────────────────────────────────────────────────────

    def test_librarian_can_list_all_members(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        response = self.client.get(self.members_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All 3 users should be visible (librarian + 2 members)
        self.assertGreaterEqual(len(response.data), 3)

    def test_member_cannot_access_list(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.members_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_access_list(self) -> None:
        response = self.client.get(self.members_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Retrieve Endpoint ─────────────────────────────────────────────────────

    def test_librarian_can_retrieve_any_member(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        response = self.client.get(self._member_detail_url(self.member.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'member_test')

    def test_member_can_retrieve_own_profile(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self._member_detail_url(self.member.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'member_test')

    def test_member_cannot_retrieve_other_member_profile(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self._member_detail_url(self.other_member.pk))
        # other_member not in queryset for member → 404, not 403
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── Update Endpoint ───────────────────────────────────────────────────────

    def test_member_can_update_own_phone_and_department(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.patch(
            self._member_detail_url(self.member.pk),
            {'phone': '+1-555-0100', 'department': 'Engineering'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member.profile.refresh_from_db()
        self.assertEqual(self.member.profile.phone, '+1-555-0100')
        self.assertEqual(self.member.profile.department, 'Engineering')

    def test_member_cannot_update_email(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.patch(
            self._member_detail_url(self.member.pk),
            {'email': 'hacker@evil.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_cannot_update_first_last_name(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.patch(
            self._member_detail_url(self.member.pk),
            {'first_name': 'Hacked', 'last_name': 'Name'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_cannot_update_other_member(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.patch(
            self._member_detail_url(self.other_member.pk),
            {'phone': '+1-000-0000'},
            format='json'
        )
        # other_member not in queryset → 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_librarian_can_update_any_member_field(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        response = self.client.patch(
            self._member_detail_url(self.member.pk),
            {'first_name': 'Updated', 'email': 'updated@library.org'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member.refresh_from_db()
        self.assertEqual(self.member.first_name, 'Updated')
        self.assertEqual(self.member.email, 'updated@library.org')

    def test_phone_validation_rejects_invalid_format(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        response = self.client.patch(
            self._member_detail_url(self.member.pk),
            {'phone': 'not@valid!'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Delete Endpoint ───────────────────────────────────────────────────────

    def test_librarian_can_delete_member(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        temp = User.objects.create_user(
            username='temp_user', email='temp@library.org', password='Temp1234!'
        )
        response = self.client.delete(self._member_detail_url(temp.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=temp.pk).exists())

    def test_member_cannot_delete_any_user(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(self._member_detail_url(self.member.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── Custom Action: Activate/Deactivate ───────────────────────────────────

    def test_librarian_can_deactivate_member(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        self.member.profile.is_active = True
        self.member.profile.save()
        response = self.client.post(self._member_action_url(self.member.pk, 'deactivate'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member.profile.refresh_from_db()
        self.assertFalse(self.member.profile.is_active)

    def test_librarian_can_activate_member(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        self.member.profile.is_active = False
        self.member.profile.save()
        response = self.client.post(self._member_action_url(self.member.pk, 'activate'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member.profile.refresh_from_db()
        self.assertTrue(self.member.profile.is_active)

    def test_member_cannot_deactivate_account(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.post(self._member_action_url(self.member.pk, 'deactivate'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── Custom Action: Change Membership ─────────────────────────────────────

    def test_librarian_can_change_membership_type(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        response = self.client.post(
            self._member_action_url(self.member.pk, 'change-membership'),
            {'membership_type': MembershipType.PREMIUM},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member.profile.refresh_from_db()
        self.assertEqual(self.member.profile.membership_type, MembershipType.PREMIUM)

    def test_change_membership_rejects_invalid_type(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        response = self.client.post(
            self._member_action_url(self.member.pk, 'change-membership'),
            {'membership_type': 'INVALID_TYPE'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_member_cannot_change_own_membership_type(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            self._member_action_url(self.member.pk, 'change-membership'),
            {'membership_type': MembershipType.PREMIUM},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── Custom Action: Change Borrow Limit ───────────────────────────────────

    def test_librarian_can_change_borrow_limit(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        response = self.client.post(
            self._member_action_url(self.member.pk, 'change-borrow-limit'),
            {'borrow_limit': 10},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member.profile.refresh_from_db()
        self.assertEqual(self.member.profile.borrow_limit, 10)

    def test_borrow_limit_rejects_zero_value(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        response = self.client.post(
            self._member_action_url(self.member.pk, 'change-borrow-limit'),
            {'borrow_limit': 0},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_borrow_limit_rejects_above_max(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        response = self.client.post(
            self._member_action_url(self.member.pk, 'change-borrow-limit'),
            {'borrow_limit': 51},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_member_cannot_change_own_borrow_limit(self) -> None:
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            self._member_action_url(self.member.pk, 'change-borrow-limit'),
            {'borrow_limit': 20},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── Search & Filtering ────────────────────────────────────────────────────

    def test_librarian_can_search_members_by_username(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        response = self.client.get(self.members_list_url + '?search=member_test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [m['username'] for m in response.data]
        self.assertIn('member_test', usernames)

    def test_librarian_can_filter_by_role(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        response = self.client.get(self.members_list_url + f'?role={UserRole.LIBRARIAN}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for m in response.data:
            self.assertEqual(m['role'], UserRole.LIBRARIAN)

    def test_librarian_can_filter_by_is_active(self) -> None:
        self.client.force_authenticate(user=self.librarian)
        self.member.profile.is_active = False
        self.member.profile.save()
        response = self.client.get(self.members_list_url + '?is_active=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for m in response.data:
            self.assertFalse(m['is_active'])
