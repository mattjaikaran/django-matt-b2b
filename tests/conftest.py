"""Pytest configuration and fixtures."""

import os

# Set environment variables before Django settings are loaded
os.environ.setdefault("USE_SQLITE", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email="test@example.com",
        username="testuser",
        password="testpass123",
    )


@pytest.fixture
def user2(db):
    """Create a second test user."""
    return User.objects.create_user(
        email="test2@example.com",
        username="testuser2",
        password="testpass123",
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        email="admin@example.com",
        username="admin",
        password="adminpass123",
    )


@pytest.fixture
def api_client():
    """Create an API test client."""
    from django.test import AsyncClient

    return AsyncClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Create an authenticated API client."""
    from django_matt.auth import create_token_pair

    tokens = create_token_pair(user)
    api_client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {tokens['access_token']}"
    return api_client


@pytest.fixture
def authenticated_client2(api_client, user2):
    """Create an authenticated API client for second user."""
    from django_matt.auth import create_token_pair

    tokens = create_token_pair(user2)
    # Create a new client to avoid header conflicts
    from django.test import AsyncClient

    client = AsyncClient()
    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {tokens['access_token']}"
    return client


@pytest.fixture
def organization(db, user):
    """Create a test organization with user as owner."""
    from apps.organizations.models import Membership, MembershipRole, Organization

    org = Organization.objects.create(
        name="Test Organization",
        slug="test-org",
        plan="free",
    )
    Membership.objects.create(
        user=user,
        organization=org,
        role=MembershipRole.OWNER,
    )
    return org


@pytest.fixture
def team(db, organization):
    """Create a test team."""
    from apps.organizations.models import Team

    return Team.objects.create(
        organization=organization,
        name="Test Team",
        slug="test-team",
    )


@pytest.fixture
def membership(db, user, organization):
    """Get the user's membership in the organization."""
    from apps.organizations.models import Membership

    return Membership.objects.get(user=user, organization=organization)


@pytest.fixture
def member_user(db, organization):
    """Create a user who is a member of the organization."""
    from apps.organizations.models import Membership, MembershipRole

    member = User.objects.create_user(
        email="member@example.com",
        username="memberuser",
        password="memberpass123",
    )
    Membership.objects.create(
        user=member,
        organization=organization,
        role=MembershipRole.MEMBER,
    )
    return member


@pytest.fixture
def member_client(db, member_user):
    """Create an authenticated client for the member user."""
    from django.test import AsyncClient
    from django_matt.auth import create_token_pair

    client = AsyncClient()
    tokens = create_token_pair(member_user)
    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {tokens['access_token']}"
    return client
