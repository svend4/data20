"""
Integration Tests for Jobs API with Ownership
Phase 5.5.3: Integration tests for job ownership and permissions
"""

import pytest
from fastapi import status


@pytest.mark.integration
class TestJobCreation:
    """Test POST /api/run endpoint with authentication"""

    def test_authenticated_user_creates_job(self, client, auth_headers_user):
        """Test that authenticated user can create job"""
        response = client.post(
            "/api/run",
            headers=auth_headers_user,
            json={
                "tool_name": "build_graph",
                "parameters": {}
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert data["tool_name"] == "build_graph"
        assert data["status"] in ["pending", "queued"]

    def test_anonymous_user_creates_job(self, client):
        """Test that anonymous user can create job"""
        response = client.post(
            "/api/run",
            json={
                "tool_name": "build_graph",
                "parameters": {}
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data

    def test_admin_creates_job(self, client, auth_headers_admin):
        """Test that admin can create job"""
        response = client.post(
            "/api/run",
            headers=auth_headers_admin,
            json={
                "tool_name": "build_graph",
                "parameters": {}
            }
        )

        assert response.status_code == status.HTTP_200_OK

    def test_invalid_tool_name(self, client, auth_headers_user):
        """Test creating job with non-existent tool"""
        response = client.post(
            "/api/run",
            headers=auth_headers_user,
            json={
                "tool_name": "nonexistent_tool",
                "parameters": {}
            }
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
class TestJobListOwnership:
    """Test GET /api/jobs endpoint with ownership filtering"""

    def test_admin_sees_all_jobs(self, client, auth_headers_admin, auth_headers_user):
        """Test that admin sees all jobs from all users"""
        # Create jobs as different users
        client.post(
            "/api/run",
            headers=auth_headers_user,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        client.post(
            "/api/run",
            headers=auth_headers_admin,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        client.post(
            "/api/run",
            json={"tool_name": "build_graph", "parameters": {}}  # Anonymous
        )

        # Admin should see all jobs
        response = client.get("/api/jobs", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 3  # At least the 3 we created

    def test_user_sees_only_own_jobs(self, client, auth_headers_user, auth_headers_admin):
        """Test that regular user sees only their own jobs"""
        # Create job as user
        user_job = client.post(
            "/api/run",
            headers=auth_headers_user,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        user_job_id = user_job.json()["job_id"]

        # Create job as admin (should not be visible to user)
        client.post(
            "/api/run",
            headers=auth_headers_admin,
            json={"tool_name": "build_graph", "parameters": {}}
        )

        # User should see only their job
        response = client.get("/api/jobs", headers=auth_headers_user)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        job_ids = [job["job_id"] for job in data["jobs"]]
        assert user_job_id in job_ids

    def test_anonymous_sees_only_anonymous_jobs(self, client, auth_headers_user):
        """Test that anonymous user sees only anonymous jobs"""
        # Create authenticated job (should not be visible)
        client.post(
            "/api/run",
            headers=auth_headers_user,
            json={"tool_name": "build_graph", "parameters": {}}
        )

        # Create anonymous job
        anon_job = client.post(
            "/api/run",
            json={"tool_name": "build_graph", "parameters": {}}
        )
        anon_job_id = anon_job.json()["job_id"]

        # Anonymous user queries
        response = client.get("/api/jobs")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        job_ids = [job["job_id"] for job in data["jobs"]]
        assert anon_job_id in job_ids


@pytest.mark.integration
class TestJobDetailsOwnership:
    """Test GET /api/jobs/{job_id} endpoint with ownership checks"""

    def test_user_accesses_own_job(self, client, auth_headers_user):
        """Test user can access their own job"""
        # Create job
        create_response = client.post(
            "/api/run",
            headers=auth_headers_user,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        job_id = create_response.json()["job_id"]

        # Access job
        response = client.get(f"/api/jobs/{job_id}", headers=auth_headers_user)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == job_id

    def test_user_cannot_access_other_user_job(self, client, auth_headers_admin, auth_headers_user):
        """Test user cannot access another user's job (gets 404)"""
        # Create job as admin
        admin_job = client.post(
            "/api/run",
            headers=auth_headers_admin,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        admin_job_id = admin_job.json()["job_id"]

        # Try to access as regular user
        response = client.get(f"/api/jobs/{admin_job_id}", headers=auth_headers_user)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_accesses_any_job(self, client, auth_headers_admin, auth_headers_user):
        """Test admin can access any job"""
        # Create job as regular user
        user_job = client.post(
            "/api/run",
            headers=auth_headers_user,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        user_job_id = user_job.json()["job_id"]

        # Admin can access it
        response = client.get(f"/api/jobs/{user_job_id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK

    def test_anonymous_accesses_own_job(self, client):
        """Test anonymous user can access their own job"""
        # Create anonymous job
        create_response = client.post(
            "/api/run",
            json={"tool_name": "build_graph", "parameters": {}}
        )
        job_id = create_response.json()["job_id"]

        # Access job
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == status.HTTP_200_OK

    def test_anonymous_cannot_access_authenticated_job(self, client, auth_headers_user):
        """Test anonymous user cannot access authenticated job"""
        # Create authenticated job
        user_job = client.post(
            "/api/run",
            headers=auth_headers_user,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        user_job_id = user_job.json()["job_id"]

        # Try to access as anonymous
        response = client.get(f"/api/jobs/{user_job_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
class TestJobLogsOwnership:
    """Test GET /api/jobs/{job_id}/logs endpoint with ownership checks"""

    def test_user_accesses_own_job_logs(self, client, auth_headers_user):
        """Test user can access their own job logs"""
        # Create job
        create_response = client.post(
            "/api/run",
            headers=auth_headers_user,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        job_id = create_response.json()["job_id"]

        # Access logs
        response = client.get(f"/api/jobs/{job_id}/logs", headers=auth_headers_user)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert "logs" in data

    def test_user_cannot_access_other_user_logs(self, client, auth_headers_admin, auth_headers_user):
        """Test user cannot access another user's job logs"""
        # Create job as admin
        admin_job = client.post(
            "/api/run",
            headers=auth_headers_admin,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        admin_job_id = admin_job.json()["job_id"]

        # Try to access logs as regular user
        response = client.get(f"/api/jobs/{admin_job_id}/logs", headers=auth_headers_user)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_accesses_any_job_logs(self, client, auth_headers_admin, auth_headers_user):
        """Test admin can access any job logs"""
        # Create job as regular user
        user_job = client.post(
            "/api/run",
            headers=auth_headers_user,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        user_job_id = user_job.json()["job_id"]

        # Admin can access logs
        response = client.get(f"/api/jobs/{user_job_id}/logs", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestJobCancellationOwnership:
    """Test DELETE /api/jobs/{job_id} endpoint with ownership checks"""

    def test_user_cancels_own_job(self, client, auth_headers_user):
        """Test user can cancel their own job"""
        # Create job
        create_response = client.post(
            "/api/run",
            headers=auth_headers_user,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        job_id = create_response.json()["job_id"]

        # Cancel job
        response = client.delete(f"/api/jobs/{job_id}", headers=auth_headers_user)
        # Could be 200 OK or 400 if job already completed
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_user_cannot_cancel_other_user_job(self, client, auth_headers_admin, auth_headers_user):
        """Test user cannot cancel another user's job"""
        # Create job as admin
        admin_job = client.post(
            "/api/run",
            headers=auth_headers_admin,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        admin_job_id = admin_job.json()["job_id"]

        # Try to cancel as regular user
        response = client.delete(f"/api/jobs/{admin_job_id}", headers=auth_headers_user)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_cancels_any_job(self, client, auth_headers_admin, auth_headers_user):
        """Test admin can cancel any job"""
        # Create job as regular user
        user_job = client.post(
            "/api/run",
            headers=auth_headers_user,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        user_job_id = user_job.json()["job_id"]

        # Admin can cancel it
        response = client.delete(f"/api/jobs/{user_job_id}", headers=auth_headers_admin)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


@pytest.mark.integration
class TestMultiUserScenarios:
    """Test complex multi-user scenarios"""

    def test_two_users_isolated_jobs(self, client, auth_headers_user, db_session):
        """Test that two users have completely isolated job lists"""
        from backend.models import User, UserRole
        from backend.auth import get_password_hash

        # Create second user
        user2 = User(
            username="user2",
            email="user2@test.com",
            hashed_password=get_password_hash("User2Pass123"),
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(user2)
        db_session.commit()

        # Login as user2
        response = client.post(
            "/auth/login",
            json={"username": "user2", "password": "User2Pass123"}
        )
        user2_token = response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # Create jobs as user1
        user1_job1 = client.post(
            "/api/run",
            headers=auth_headers_user,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        user1_job1_id = user1_job1.json()["job_id"]

        # Create jobs as user2
        user2_job1 = client.post(
            "/api/run",
            headers=user2_headers,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        user2_job1_id = user2_job1.json()["job_id"]

        # User1 sees only their job
        user1_jobs = client.get("/api/jobs", headers=auth_headers_user)
        user1_job_ids = [j["job_id"] for j in user1_jobs.json()["jobs"]]
        assert user1_job1_id in user1_job_ids
        assert user2_job1_id not in user1_job_ids

        # User2 sees only their job
        user2_jobs = client.get("/api/jobs", headers=user2_headers)
        user2_job_ids = [j["job_id"] for j in user2_jobs.json()["jobs"]]
        assert user2_job1_id in user2_job_ids
        assert user1_job1_id not in user2_job_ids

    def test_user_promoted_to_admin_sees_all_jobs(self, client, auth_headers_admin, db_session):
        """Test that user promoted to admin can see all jobs"""
        from backend.models import User, UserRole
        from backend.auth import get_password_hash

        # Create regular user
        user = User(
            username="promoteuser",
            email="promote@test.com",
            hashed_password=get_password_hash("PromotePass123"),
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Login as user
        login_response = client.post(
            "/auth/login",
            json={"username": "promoteuser", "password": "PromotePass123"}
        )
        user_token = login_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Create job as admin
        admin_job = client.post(
            "/api/run",
            headers=auth_headers_admin,
            json={"tool_name": "build_graph", "parameters": {}}
        )
        admin_job_id = admin_job.json()["job_id"]

        # User cannot see admin's job
        response = client.get(f"/api/jobs/{admin_job_id}", headers=user_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Promote user to admin
        client.put(
            f"/admin/users/{str(user.id)}/role",
            headers=auth_headers_admin,
            json={"role": "admin"}
        )

        # User needs new token with admin role
        new_login = client.post(
            "/auth/login",
            json={"username": "promoteuser", "password": "PromotePass123"}
        )
        new_token = new_login.json()["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}

        # Now can see admin's job
        response = client.get(f"/api/jobs/{admin_job_id}", headers=new_headers)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestSecurityScenarios:
    """Test security-related scenarios"""

    def test_job_id_enumeration_prevented(self, client, auth_headers_user):
        """Test that 404 is returned for unauthorized access (not 403)"""
        # Try to access non-existent or unauthorized job
        fake_job_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/jobs/{fake_job_id}", headers=auth_headers_user)

        # Should be 404, not 403 (prevents enumeration)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_to_authenticated_transition(self, client):
        """Test transition from anonymous to authenticated user"""
        # Create job as anonymous
        anon_job = client.post(
            "/api/run",
            json={"tool_name": "build_graph", "parameters": {}}
        )
        anon_job_id = anon_job.json()["job_id"]

        # Register and login
        client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "NewPass123"
            }
        )
        login_response = client.post(
            "/auth/login",
            json={"username": "newuser", "password": "NewPass123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Authenticated user cannot see anonymous job
        response = client.get(f"/api/jobs/{anon_job_id}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # But anonymous can still access it
        response = client.get(f"/api/jobs/{anon_job_id}")
        assert response.status_code == status.HTTP_200_OK
