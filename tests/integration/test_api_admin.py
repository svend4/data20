"""
Integration Tests for Admin API
Phase 5.5.3: Integration tests for admin user management endpoints
"""

import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.admin
class TestAdminListUsers:
    """Test GET /admin/users endpoint"""

    def test_admin_can_list_users(self, client, auth_headers_admin, admin_user, regular_user):
        """Test that admin can list all users"""
        response = client.get("/admin/users", headers=auth_headers_admin)

        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 2  # At least admin and regular_user

        usernames = [u["username"] for u in users]
        assert "admin" in usernames
        assert "user1" in usernames

    def test_admin_list_users_pagination(self, client, auth_headers_admin, admin_user):
        """Test pagination parameters"""
        response = client.get(
            "/admin/users?skip=0&limit=1",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert len(users) == 1

    def test_regular_user_cannot_list_users(self, client, auth_headers_user):
        """Test that regular user gets 403 Forbidden"""
        response = client.get("/admin/users", headers=auth_headers_user)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_cannot_list_users(self, client):
        """Test that anonymous user gets 403 Forbidden"""
        response = client.get("/admin/users")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.admin
class TestAdminGetUser:
    """Test GET /admin/users/{user_id} endpoint"""

    def test_admin_can_get_user_details(self, client, auth_headers_admin, regular_user):
        """Test that admin can get user details"""
        user_id = str(regular_user.id)
        response = client.get(
            f"/admin/users/{user_id}",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "user1"
        assert data["email"] == "user1@test.com"
        assert data["role"] == "user"

    def test_admin_get_nonexistent_user(self, client, auth_headers_admin):
        """Test getting non-existent user"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/admin/users/{fake_id}",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_regular_user_cannot_get_user_details(self, client, auth_headers_user, admin_user):
        """Test that regular user cannot get user details"""
        user_id = str(admin_user.id)
        response = client.get(
            f"/admin/users/{user_id}",
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.admin
class TestAdminUpdateUserRole:
    """Test PUT /admin/users/{user_id}/role endpoint"""

    def test_admin_can_promote_user(self, client, auth_headers_admin, regular_user, db_session):
        """Test promoting user to admin"""
        user_id = str(regular_user.id)
        response = client.put(
            f"/admin/users/{user_id}/role",
            headers=auth_headers_admin,
            json={"role": "admin"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "admin"

        # Verify in database
        db_session.refresh(regular_user)
        assert regular_user.role.value == "admin"

    def test_admin_can_demote_user(self, client, auth_headers_admin, db_session):
        """Test demoting admin to user"""
        # First create another admin
        from backend.models import User, UserRole
        from backend.auth import get_password_hash

        second_admin = User(
            username="secondadmin",
            email="secondadmin@test.com",
            hashed_password=get_password_hash("Admin2Pass123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db_session.add(second_admin)
        db_session.commit()
        db_session.refresh(second_admin)

        user_id = str(second_admin.id)
        response = client.put(
            f"/admin/users/{user_id}/role",
            headers=auth_headers_admin,
            json={"role": "user"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "user"

    def test_admin_cannot_demote_self(self, client, auth_headers_admin, admin_user):
        """Test that admin cannot demote themselves"""
        user_id = str(admin_user.id)
        response = client.put(
            f"/admin/users/{user_id}/role",
            headers=auth_headers_admin,
            json={"role": "user"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot demote yourself" in response.json()["detail"]

    def test_invalid_role_rejected(self, client, auth_headers_admin, regular_user):
        """Test that invalid role is rejected"""
        user_id = str(regular_user.id)
        response = client.put(
            f"/admin/users/{user_id}/role",
            headers=auth_headers_admin,
            json={"role": "superuser"}  # Invalid role
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_regular_user_cannot_update_roles(self, client, auth_headers_user, admin_user):
        """Test that regular user cannot update roles"""
        user_id = str(admin_user.id)
        response = client.put(
            f"/admin/users/{user_id}/role",
            headers=auth_headers_user,
            json={"role": "user"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.admin
class TestAdminUpdateUserStatus:
    """Test PUT /admin/users/{user_id}/status endpoint"""

    def test_admin_can_deactivate_user(self, client, auth_headers_admin, regular_user, db_session):
        """Test deactivating user account"""
        user_id = str(regular_user.id)
        response = client.put(
            f"/admin/users/{user_id}/status",
            headers=auth_headers_admin,
            json={"is_active": False}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False

        # Verify in database
        db_session.refresh(regular_user)
        assert regular_user.is_active is False

    def test_admin_can_reactivate_user(self, client, auth_headers_admin, inactive_user, db_session):
        """Test reactivating inactive user"""
        user_id = str(inactive_user.id)
        response = client.put(
            f"/admin/users/{user_id}/status",
            headers=auth_headers_admin,
            json={"is_active": True}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is True

        # Verify in database
        db_session.refresh(inactive_user)
        assert inactive_user.is_active is True

    def test_admin_cannot_deactivate_self(self, client, auth_headers_admin, admin_user):
        """Test that admin cannot deactivate themselves"""
        user_id = str(admin_user.id)
        response = client.put(
            f"/admin/users/{user_id}/status",
            headers=auth_headers_admin,
            json={"is_active": False}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot deactivate yourself" in response.json()["detail"]

    def test_deactivated_user_cannot_login(self, client, auth_headers_admin, regular_user):
        """Test that deactivated user cannot login"""
        # Deactivate user
        user_id = str(regular_user.id)
        client.put(
            f"/admin/users/{user_id}/status",
            headers=auth_headers_admin,
            json={"is_active": False}
        )

        # Try to login
        response = client.post(
            "/auth/login",
            json={"username": "user1", "password": "User1Pass123"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_regular_user_cannot_update_status(self, client, auth_headers_user, admin_user):
        """Test that regular user cannot update user status"""
        user_id = str(admin_user.id)
        response = client.put(
            f"/admin/users/{user_id}/status",
            headers=auth_headers_user,
            json={"is_active": False}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.admin
class TestAdminDeleteUser:
    """Test DELETE /admin/users/{user_id} endpoint"""

    def test_admin_can_delete_user(self, client, auth_headers_admin, regular_user, db_session):
        """Test deleting user account"""
        user_id = str(regular_user.id)
        username = regular_user.username

        response = client.delete(
            f"/admin/users/{user_id}",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert username in data["message"]
        assert data["user_id"] == user_id

        # Verify user is deleted from database
        from backend.models import User
        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None

    def test_admin_cannot_delete_self(self, client, auth_headers_admin, admin_user):
        """Test that admin cannot delete themselves"""
        user_id = str(admin_user.id)
        response = client.delete(
            f"/admin/users/{user_id}",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot delete yourself" in response.json()["detail"]

    def test_delete_nonexistent_user(self, client, auth_headers_admin):
        """Test deleting non-existent user"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(
            f"/admin/users/{fake_id}",
            headers=auth_headers_admin
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_regular_user_cannot_delete_users(self, client, auth_headers_user, admin_user):
        """Test that regular user cannot delete users"""
        user_id = str(admin_user.id)
        response = client.delete(
            f"/admin/users/{user_id}",
            headers=auth_headers_user
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_deleted_user_cannot_login(self, client, auth_headers_admin, db_session):
        """Test that deleted user cannot login"""
        # Create and delete a user
        from backend.models import User, UserRole
        from backend.auth import get_password_hash

        temp_user = User(
            username="tempuser",
            email="temp@test.com",
            hashed_password=get_password_hash("TempPass123"),
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(temp_user)
        db_session.commit()
        db_session.refresh(temp_user)

        user_id = str(temp_user.id)

        # Delete user
        client.delete(f"/admin/users/{user_id}", headers=auth_headers_admin)

        # Try to login
        response = client.post(
            "/auth/login",
            json={"username": "tempuser", "password": "TempPass123"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.admin
class TestAdminWorkflow:
    """Test complete admin workflow scenarios"""

    def test_admin_manages_user_lifecycle(self, client, auth_headers_admin, db_session):
        """Test complete user lifecycle: create → promote → deactivate → reactivate → delete"""
        from backend.models import User, UserRole
        from backend.auth import get_password_hash

        # 1. Create user
        new_user = User(
            username="lifecycle",
            email="lifecycle@test.com",
            hashed_password=get_password_hash("LifecyclePass123"),
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)
        user_id = str(new_user.id)

        # 2. Promote to admin
        response = client.put(
            f"/admin/users/{user_id}/role",
            headers=auth_headers_admin,
            json={"role": "admin"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "admin"

        # 3. Deactivate
        response = client.put(
            f"/admin/users/{user_id}/status",
            headers=auth_headers_admin,
            json={"is_active": False}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_active"] is False

        # 4. Reactivate
        response = client.put(
            f"/admin/users/{user_id}/status",
            headers=auth_headers_admin,
            json={"is_active": True}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_active"] is True

        # 5. Demote back to user
        response = client.put(
            f"/admin/users/{user_id}/role",
            headers=auth_headers_admin,
            json={"role": "user"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "user"

        # 6. Delete
        response = client.delete(
            f"/admin/users/{user_id}",
            headers=auth_headers_admin
        )
        assert response.status_code == status.HTTP_200_OK

    def test_multiple_admins_scenario(self, client, auth_headers_admin, db_session):
        """Test scenario with multiple admins"""
        from backend.models import User, UserRole
        from backend.auth import get_password_hash

        # Create second admin
        admin2 = User(
            username="admin2",
            email="admin2@test.com",
            hashed_password=get_password_hash("Admin2Pass123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db_session.add(admin2)
        db_session.commit()
        db_session.refresh(admin2)

        # Login as second admin
        response = client.post(
            "/auth/login",
            json={"username": "admin2", "password": "Admin2Pass123"}
        )
        admin2_token = response.json()["access_token"]
        admin2_headers = {"Authorization": f"Bearer {admin2_token}"}

        # Both admins can list users
        response1 = client.get("/admin/users", headers=auth_headers_admin)
        response2 = client.get("/admin/users", headers=admin2_headers)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        # admin1 can demote admin2 (not self)
        response = client.put(
            f"/admin/users/{str(admin2.id)}/role",
            headers=auth_headers_admin,
            json={"role": "user"}
        )
        assert response.status_code == status.HTTP_200_OK
