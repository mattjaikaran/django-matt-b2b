"""Pytest configuration and fixtures."""

from django.contrib.auth import get_user_model

import pytest
from django_matt.testing import APITestClient

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
def member_user(db, organization):
    """Create a user who is a member (not owner) of an organization."""
    from apps.organizations.models import Membership, MembershipRole

    member = User.objects.create_user(
        email="member@example.com",
        username="memberuser",
        password="testpass123",
    )
    Membership.objects.create(
        user=member,
        organization=organization,
        role=MembershipRole.MEMBER,
    )
    return member


@pytest.fixture
def api_client():
    """Create an API test client."""
    return APITestClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Create an authenticated API client."""
    api_client.force_authenticate(user)
    return api_client


@pytest.fixture
def authenticated_client2(user2):
    """Create an authenticated API client for user2."""
    client = APITestClient()
    client.force_authenticate(user2)
    return client


@pytest.fixture
def member_client(member_user):
    """Create an authenticated API client for a member user."""
    client = APITestClient()
    client.force_authenticate(member_user)
    return client


@pytest.fixture
def organization(db, user):
    """Create a test organization with user as owner."""
    from apps.organizations.models import Membership, MembershipRole, Organization

    org = Organization.objects.create(
        name="Test Organization",
        slug="test-org",
        description="A test organization",
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
    """Create a test team in the organization."""
    from apps.organizations.models import Team

    return Team.objects.create(
        organization=organization,
        name="Test Team",
        slug="test-team",
        description="A test team",
    )
