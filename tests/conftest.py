"""
Pytest Configuration and Shared Fixtures
Phase 5.5: Testing Infrastructure
"""

import os
import sys
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.server import app
from backend.database import Base, get_db
from backend.models import User, UserRole
from backend.auth import get_password_hash


# ========================
# Database Fixtures
# ========================

@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create database session for testing"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create FastAPI test client with test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ========================
# User Fixtures
# ========================

@pytest.fixture
def admin_user(db_session) -> User:
    """Create admin user for testing"""
    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("AdminPass123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session) -> User:
    """Create regular user for testing"""
    user = User(
        username="user1",
        email="user1@test.com",
        hashed_password=get_password_hash("User1Pass123"),
        full_name="Regular User",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session) -> User:
    """Create inactive user for testing"""
    user = User(
        username="inactive",
        email="inactive@test.com",
        hashed_password=get_password_hash("InactivePass123"),
        full_name="Inactive User",
        role=UserRole.USER,
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ========================
# Authentication Fixtures
# ========================

@pytest.fixture
def admin_token(client, admin_user) -> str:
    """Get JWT token for admin user"""
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "AdminPass123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def user_token(client, regular_user) -> str:
    """Get JWT token for regular user"""
    response = client.post(
        "/auth/login",
        json={"username": "user1", "password": "User1Pass123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers_admin(admin_token) -> dict:
    """Get authorization headers for admin"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers_user(user_token) -> dict:
    """Get authorization headers for regular user"""
    return {"Authorization": f"Bearer {user_token}"}


# ========================
# Test Data Fixtures
# ========================

@pytest.fixture
def sample_tool_request():
    """Sample tool execution request"""
    return {
        "tool_name": "build_graph",
        "parameters": {}
    }


@pytest.fixture
def sample_user_data():
    """Sample user registration data"""
    return {
        "username": "newuser",
        "email": "newuser@test.com",
        "password": "NewUserPass123",
        "full_name": "New User"
    }


# ========================
# Environment Setup
# ========================

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "ERROR"  # Reduce log noise in tests
    yield
    # Cleanup after all tests
    pass


# ========================
# Markers for Test Organization
# ========================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests (>1s)")
    config.addinivalue_line("markers", "database: Tests requiring database")
    config.addinivalue_line("markers", "redis: Tests requiring Redis")
    config.addinivalue_line("markers", "celery: Tests requiring Celery")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "admin: Admin endpoint tests")
