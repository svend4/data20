"""
Unit Tests for Authentication Module
Phase 5.5.2: Unit tests for auth module
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from backend.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    SECRET_KEY,
    ALGORITHM,
)


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordHashing:
    """Test password hashing functions"""

    def test_password_hash_creates_different_hashes(self):
        """Test that same password creates different hashes (bcrypt salt)"""
        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2  # Different salts
        assert hash1.startswith("$2b$")  # bcrypt prefix
        assert hash2.startswith("$2b$")

    def test_password_verification_success(self):
        """Test successful password verification"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test failed password verification"""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_empty_password_hashing(self):
        """Test hashing empty password"""
        password = ""
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
        assert verify_password("nonempty", hashed) is False


@pytest.mark.unit
@pytest.mark.auth
class TestJWTTokens:
    """Test JWT token creation and verification"""

    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_access_token_custom_expiry(self):
        """Test access token with custom expiry"""
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=expires_delta)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        iat_time = datetime.utcfromtimestamp(payload["iat"])

        # Should be approximately 5 minutes
        delta = (exp_time - iat_time).total_seconds()
        assert 290 <= delta <= 310  # Allow 10 second margin

    def test_verify_token_success(self):
        """Test successful token verification"""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"

    def test_verify_token_invalid(self):
        """Test verification of invalid token"""
        invalid_token = "invalid.token.here"

        with pytest.raises(JWTError):
            verify_token(invalid_token)

    def test_verify_token_expired(self):
        """Test verification of expired token"""
        data = {"sub": "user123"}
        # Create token that expired 1 hour ago
        expired_delta = timedelta(hours=-1)

        # Manually create expired token
        expire = datetime.utcnow() + expired_delta
        to_encode = data.copy()
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(JWTError):
            verify_token(expired_token)

    def test_verify_token_wrong_signature(self):
        """Test verification of token with wrong signature"""
        data = {"sub": "user123"}
        # Create token with different secret
        wrong_token = jwt.encode(
            {"sub": "user123", "type": "access"},
            "wrong-secret-key",
            algorithm=ALGORITHM
        )

        with pytest.raises(JWTError):
            verify_token(wrong_token)

    def test_token_contains_all_required_fields(self):
        """Test that tokens contain all required fields"""
        data = {
            "sub": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "admin"
        }
        token = create_access_token(data)
        payload = verify_token(token)

        # All original data should be preserved
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "admin"

        # Plus token metadata
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "access"


@pytest.mark.unit
@pytest.mark.auth
class TestTokenTypes:
    """Test access vs refresh token differentiation"""

    def test_access_token_type(self):
        """Test access token has correct type"""
        token = create_access_token({"sub": "user123"})
        payload = verify_token(token)
        assert payload["type"] == "access"

    def test_refresh_token_type(self):
        """Test refresh token has correct type"""
        token = create_refresh_token({"sub": "user123"})
        payload = verify_token(token)
        assert payload["type"] == "refresh"

    def test_access_token_shorter_expiry(self):
        """Test that access tokens expire before refresh tokens"""
        access_token = create_access_token({"sub": "user123"})
        refresh_token = create_refresh_token({"sub": "user123"})

        access_payload = verify_token(access_token)
        refresh_payload = verify_token(refresh_token)

        access_exp = access_payload["exp"]
        refresh_exp = refresh_payload["exp"]

        # Refresh token should expire later than access token
        assert refresh_exp > access_exp


@pytest.mark.unit
@pytest.mark.auth
class TestEdgeCases:
    """Test edge cases and security scenarios"""

    def test_empty_data_token(self):
        """Test token creation with empty data"""
        token = create_access_token({})
        payload = verify_token(token)

        # Should still have metadata
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "access"

    def test_special_characters_in_data(self):
        """Test token with special characters"""
        data = {
            "sub": "user<script>alert('xss')</script>",
            "username": "user@#$%^&*()",
            "email": "test+alias@example.com"
        }
        token = create_access_token(data)
        payload = verify_token(token)

        # Data should be preserved exactly
        assert payload["sub"] == data["sub"]
        assert payload["username"] == data["username"]
        assert payload["email"] == data["email"]

    def test_large_payload(self):
        """Test token with large payload"""
        data = {
            "sub": "user123",
            "large_field": "x" * 1000  # 1000 characters
        }
        token = create_access_token(data)
        payload = verify_token(token)

        assert payload["large_field"] == "x" * 1000

    def test_unicode_in_token(self):
        """Test token with unicode characters"""
        data = {
            "sub": "user123",
            "username": "用户名",  # Chinese
            "full_name": "Пользователь"  # Russian
        }
        token = create_access_token(data)
        payload = verify_token(token)

        assert payload["username"] == "用户名"
        assert payload["full_name"] == "Пользователь"


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordStrength:
    """Test password hashing strength and performance"""

    def test_bcrypt_cost_factor(self):
        """Test that bcrypt uses appropriate cost factor"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        # bcrypt format: $2b$<cost>$<salt+hash>
        parts = hashed.split("$")
        cost = int(parts[2])

        # Should use cost factor >= 10 (12 is default)
        assert cost >= 10
        assert cost <= 14  # Not too slow

    def test_password_hashing_performance(self):
        """Test that password hashing completes in reasonable time"""
        import time

        password = "TestPassword123"
        start = time.time()
        get_password_hash(password)
        duration = time.time() - start

        # Should complete within 500ms (bcrypt is intentionally slow)
        assert duration < 0.5

    def test_same_password_different_users(self):
        """Test that same password for different users creates different hashes"""
        password = "CommonPassword123"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        hash3 = get_password_hash(password)

        # All should be different (different salts)
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3

        # But all should verify
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
        assert verify_password(password, hash3)
