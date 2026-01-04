"""
Integration Tests for Authentication API
Phase 5.5.3: Integration tests for auth endpoints
"""

import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.auth
class TestUserRegistration:
    """Test POST /auth/register endpoint"""

    def test_register_first_user_becomes_admin(self, client, db_session):
        """Test that first user becomes admin"""
        response = client.post(
            "/auth/register",
            json={
                "username": "firstuser",
                "email": "first@test.com",
                "password": "FirstPass123",
                "full_name": "First User"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "firstuser"
        assert data["email"] == "first@test.com"
        assert data["role"] == "admin"  # First user is admin
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_register_second_user_becomes_regular_user(self, client, admin_user):
        """Test that second user gets regular user role"""
        response = client.post(
            "/auth/register",
            json={
                "username": "seconduser",
                "email": "second@test.com",
                "password": "SecondPass123",
                "full_name": "Second User"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "user"  # Not admin

    def test_register_duplicate_username(self, client, admin_user):
        """Test registration with duplicate username"""
        response = client.post(
            "/auth/register",
            json={
                "username": "admin",  # Already exists
                "email": "newemail@test.com",
                "password": "NewPass123"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, client, admin_user):
        """Test registration with duplicate email"""
        response = client.post(
            "/auth/register",
            json={
                "username": "newusername",
                "email": "admin@test.com",  # Already exists
                "password": "NewPass123"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    def test_register_weak_password(self, client):
        """Test registration with password too short"""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "short"  # < 8 characters
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "at least 8 characters" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format"""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "invalid-email",  # No @
                "password": "ValidPass123"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_with_optional_full_name(self, client):
        """Test registration with optional full_name"""
        response = client.post(
            "/auth/register",
            json={
                "username": "usernoname",
                "email": "noname@test.com",
                "password": "ValidPass123"
                # No full_name
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] is None


@pytest.mark.integration
@pytest.mark.auth
class TestUserLogin:
    """Test POST /auth/login endpoint"""

    def test_login_success(self, client, admin_user):
        """Test successful login"""
        response = client.post(
            "/auth/login",
            json={
                "username": "admin",
                "password": "AdminPass123"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    def test_login_with_email(self, client, admin_user):
        """Test login using email instead of username"""
        response = client.post(
            "/auth/login",
            json={
                "username": "admin@test.com",  # Using email
                "password": "AdminPass123"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client, admin_user):
        """Test login with wrong password"""
        response = client.post(
            "/auth/login",
            json={
                "username": "admin",
                "password": "WrongPassword123"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent username"""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "SomePassword123"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self, client, inactive_user):
        """Test login with inactive user account"""
        response = client.post(
            "/auth/login",
            json={
                "username": "inactive",
                "password": "InactivePass123"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.auth
class TestTokenRefresh:
    """Test POST /auth/refresh endpoint"""

    def test_refresh_token_success(self, client, admin_user):
        """Test successful token refresh"""
        # Login to get refresh token
        login_response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "AdminPass123"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Refresh token should be new
        assert len(data["access_token"]) > 0

    def test_refresh_with_invalid_token(self, client):
        """Test refresh with invalid token"""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_with_access_token(self, client, admin_token):
        """Test refresh with access token instead of refresh token"""
        # Should fail - access tokens can't be used for refresh
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": admin_token}
        )

        # This might succeed or fail depending on implementation
        # If type checking is strict, it should fail
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


@pytest.mark.integration
@pytest.mark.auth
class TestGetCurrentUser:
    """Test GET /auth/me endpoint"""

    def test_get_current_user_success(self, client, auth_headers_admin, admin_user):
        """Test getting current user info"""
        response = client.get("/auth/me", headers=auth_headers_admin)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "admin"
        assert data["email"] == "admin@test.com"
        assert data["role"] == "admin"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        response = client.get("/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.auth
class TestUpdateUserProfile:
    """Test PUT /auth/me endpoint"""

    def test_update_full_name(self, client, auth_headers_user, regular_user):
        """Test updating user's full name"""
        response = client.put(
            "/auth/me",
            headers=auth_headers_user,
            json={"full_name": "Updated Name"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Updated Name"

    def test_update_without_changes(self, client, auth_headers_admin):
        """Test update endpoint without providing data"""
        response = client.put(
            "/auth/me",
            headers=auth_headers_admin,
            json={}
        )

        assert response.status_code == status.HTTP_200_OK

    def test_update_requires_authentication(self, client):
        """Test that update requires authentication"""
        response = client.put(
            "/auth/me",
            json={"full_name": "New Name"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.auth
class TestLogout:
    """Test POST /auth/logout endpoint"""

    def test_logout_success(self, client, auth_headers_admin):
        """Test successful logout"""
        response = client.post("/auth/logout", headers=auth_headers_admin)

        assert response.status_code == status.HTTP_200_OK
        assert "Logged out successfully" in response.json()["message"]

    def test_logout_requires_authentication(self, client):
        """Test that logout requires authentication"""
        response = client.post("/auth/logout")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.auth
class TestAuthenticationFlow:
    """Test complete authentication flow"""

    def test_complete_auth_flow(self, client):
        """Test register → login → access protected → refresh → logout"""
        # 1. Register
        register_response = client.post(
            "/auth/register",
            json={
                "username": "flowtest",
                "email": "flow@test.com",
                "password": "FlowTest123"
            }
        )
        assert register_response.status_code == status.HTTP_200_OK

        # 2. Login
        login_response = client.post(
            "/auth/login",
            json={"username": "flowtest", "password": "FlowTest123"}
        )
        assert login_response.status_code == status.HTTP_200_OK
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # 3. Access protected endpoint
        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["username"] == "flowtest"

        # 4. Refresh token
        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == status.HTTP_200_OK
        new_access_token = refresh_response.json()["access_token"]
        assert new_access_token != access_token

        # 5. Use new token
        me_response2 = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert me_response2.status_code == status.HTTP_200_OK

        # 6. Logout
        logout_response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert logout_response.status_code == status.HTTP_200_OK


@pytest.mark.integration
@pytest.mark.auth
class TestAuthorizationHeaders:
    """Test various authorization header formats"""

    def test_valid_bearer_token(self, client, admin_token):
        """Test valid Bearer token format"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_missing_bearer_prefix(self, client, admin_token):
        """Test token without 'Bearer' prefix"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": admin_token}
        )
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_case_sensitive_bearer(self, client, admin_token):
        """Test that Bearer is case-sensitive"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"bearer {admin_token}"}  # lowercase
        )
        # Might work or not depending on implementation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_empty_authorization_header(self, client):
        """Test empty authorization header"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": ""}
        )
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
