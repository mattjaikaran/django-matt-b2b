"""Tests for authentication endpoints."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAuthEndpoints:
    """Test authentication endpoints."""

    async def test_register(self, api_client):
        """Test user registration."""
        response = await api_client.post(
            "/api/auth/register",
            data={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepass123",
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"

    async def test_register_duplicate_email(self, api_client, user):
        """Test registration with duplicate email fails."""
        response = await api_client.post(
            "/api/auth/register",
            data={
                "email": "test@example.com",  # Same as fixture user
                "username": "newuser",
                "password": "securepass123",
            },
            content_type="application/json",
        )
        assert response.status_code == 422

    async def test_login(self, api_client, user):
        """Test user login."""
        response = await api_client.post(
            "/api/auth/login",
            data={
                "email": "test@example.com",
                "password": "testpass123",
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, api_client, user):
        """Test login with invalid credentials."""
        response = await api_client.post(
            "/api/auth/login",
            data={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
            content_type="application/json",
        )
        assert response.status_code == 401

    async def test_me_authenticated(self, authenticated_client, user):
        """Test getting current user when authenticated."""
        response = await authenticated_client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email

    async def test_me_unauthenticated(self, api_client):
        """Test getting current user when not authenticated."""
        response = await api_client.get("/api/auth/me")
        assert response.status_code == 401

    async def test_update_me(self, authenticated_client, user):
        """Test updating current user profile."""
        response = await authenticated_client.patch(
            "/api/auth/me",
            data={
                "first_name": "Updated",
                "last_name": "Name",
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"

    async def test_change_password(self, authenticated_client, user):
        """Test changing password."""
        response = await authenticated_client.post(
            "/api/auth/change-password",
            data={
                "current_password": "testpass123",
                "new_password": "newpass12345",
            },
            content_type="application/json",
        )
        assert response.status_code == 200

        # Verify can login with new password
        from django.test import AsyncClient

        client = AsyncClient()
        response = await client.post(
            "/api/auth/login",
            data={
                "email": "test@example.com",
                "password": "newpass12345",
            },
            content_type="application/json",
        )
        assert response.status_code == 200

    async def test_change_password_wrong_current(self, authenticated_client, user):
        """Test changing password with wrong current password."""
        response = await authenticated_client.post(
            "/api/auth/change-password",
            data={
                "current_password": "wrongpassword",
                "new_password": "newpass12345",
            },
            content_type="application/json",
        )
        assert response.status_code == 422

    async def test_refresh_token(self, api_client, user):
        """Test token refresh."""
        # First login
        login_response = await api_client.post(
            "/api/auth/login",
            data={
                "email": "test@example.com",
                "password": "testpass123",
            },
            content_type="application/json",
        )
        tokens = login_response.json()

        # Refresh
        response = await api_client.post(
            "/api/auth/refresh",
            data={"refresh_token": tokens["refresh_token"]},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
