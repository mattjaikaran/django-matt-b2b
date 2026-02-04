"""Tests for authentication endpoints."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test user model functionality."""

    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(
            email="newtest@example.com",
            username="newtestuser",
            password="testpass123",
        )
        assert user.email == "newtest@example.com"
        assert user.username == "newtestuser"
        assert user.check_password("testpass123")

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            email="newadmin@example.com",
            username="newadmin",
            password="adminpass123",
        )
        assert admin.email == "newadmin@example.com"
        assert admin.is_staff
        assert admin.is_superuser

    def test_user_full_name(self):
        """Test user full_name property."""
        user = User.objects.create_user(
            email="fullname@example.com",
            username="fullnameuser",
            password="testpass123",
            first_name="John",
            last_name="Doe",
        )
        assert user.full_name == "John Doe"

    def test_user_full_name_fallback(self):
        """Test user full_name fallback to username."""
        user = User.objects.create_user(
            email="fallback@example.com",
            username="fallbackuser",
            password="testpass123",
        )
        assert user.full_name == "fallbackuser"


@pytest.mark.django_db
class TestAuthSchemas:
    """Test auth schemas."""

    def test_user_schema(self):
        """Test UserSchema validation."""
        from apps.users.schemas import UserSchema

        user = User.objects.create_user(
            email="schema@example.com",
            username="schemauser",
            password="testpass123",
        )
        schema = UserSchema.model_validate(user)
        assert schema.email == "schema@example.com"
        assert schema.username == "schemauser"

    def test_login_schema(self):
        """Test LoginSchema validation."""
        from apps.users.schemas import LoginSchema

        data = LoginSchema(email="test@example.com", password="password123")
        assert data.email == "test@example.com"
        assert data.password == "password123"

    def test_token_schema(self):
        """Test TokenSchema validation."""
        from apps.users.schemas import TokenSchema

        data = TokenSchema(
            access_token="access123",
            refresh_token="refresh123",
            token_type="bearer",
        )
        assert data.access_token == "access123"
        assert data.refresh_token == "refresh123"

    def test_user_create_schema(self):
        """Test UserCreateSchema validation."""
        from apps.users.schemas import UserCreateSchema

        data = UserCreateSchema(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        assert data.email == "test@example.com"
        assert data.username == "testuser"


@pytest.mark.django_db
class TestAuthEndpoints:
    """Test authentication API endpoints."""

    def test_health_endpoint(self, api_client):
        """Test health check endpoint."""
        response = api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_me_unauthenticated(self, api_client):
        """Test /me endpoint without auth."""
        response = api_client.get("/api/auth/me")
        assert response.status_code == 401


@pytest.mark.django_db
class TestJWTAuth:
    """Test JWT authentication functionality."""

    def test_create_token_pair(self, user):
        """Test creating JWT token pair."""
        from django_matt.auth import create_token_pair

        tokens = create_token_pair(user)
        assert hasattr(tokens, "access_token")
        assert hasattr(tokens, "refresh_token")
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None

    def test_token_pair_has_expiry(self, user):
        """Test that token pair includes expiry information."""
        from django_matt.auth import create_token_pair

        tokens = create_token_pair(user)
        # Tokens should be non-empty strings
        assert len(tokens.access_token) > 0
        assert len(tokens.refresh_token) > 0
        # Both should be different tokens
        assert tokens.access_token != tokens.refresh_token
