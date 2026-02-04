"""Tests for organization models and schemas."""

from django.contrib.auth import get_user_model

import pytest

from apps.organizations.models import (
    Invitation,
    InvitationStatus,
    Membership,
    MembershipRole,
    Organization,
    Team,
)

User = get_user_model()


@pytest.mark.django_db
class TestOrganizationModel:
    """Test organization model functionality."""

    def test_create_organization(self, user):
        """Test creating an organization."""
        org = Organization.objects.create(
            name="Test Org",
            slug="test-org-model",
            description="A test organization",
        )
        assert org.name == "Test Org"
        assert org.slug == "test-org-model"
        assert str(org) == "Test Org"

    def test_organization_member_count(self, organization, user, member_user):
        """Test organization member count property."""
        # Organization fixture creates owner, member_user fixture creates member
        assert organization.member_count == 2

    def test_organization_team_count(self, organization, team):
        """Test organization team count property."""
        assert organization.team_count == 1

    def test_organization_get_owners(self, organization, user):
        """Test getting organization owners."""
        owners = organization.get_owners()
        assert owners.count() == 1
        assert owners.first().user == user

    def test_organization_get_admins(self, organization, user, member_user):
        """Test getting organization admins (includes owners)."""
        # Make member_user an admin
        membership = Membership.objects.get(user=member_user, organization=organization)
        membership.role = MembershipRole.ADMIN
        membership.save()

        admins = organization.get_admins()
        assert admins.count() == 2  # owner + admin


@pytest.mark.django_db
class TestTeamModel:
    """Test team model functionality."""

    def test_create_team(self, organization):
        """Test creating a team."""
        team = Team.objects.create(
            organization=organization,
            name="Engineering",
            slug="engineering",
            description="Engineering team",
        )
        assert team.name == "Engineering"
        assert team.organization == organization
        assert "Engineering" in str(team)

    def test_team_member_count(self, organization, team, user):
        """Test team member count property."""
        membership = Membership.objects.get(user=user, organization=organization)
        team.members.add(membership)
        assert team.member_count == 1


@pytest.mark.django_db
class TestMembershipModel:
    """Test membership model functionality."""

    def test_membership_roles(self, user, organization):
        """Test membership role properties."""
        membership = Membership.objects.get(user=user, organization=organization)
        assert membership.is_owner
        assert membership.is_admin
        assert membership.can_manage_members
        assert membership.can_delete_organization

    def test_member_role_permissions(self, member_user, organization):
        """Test member role has limited permissions."""
        membership = Membership.objects.get(user=member_user, organization=organization)
        assert not membership.is_owner
        assert not membership.is_admin
        assert not membership.can_manage_members
        assert not membership.can_delete_organization

    def test_admin_role_permissions(self, organization, user2):
        """Test admin role permissions."""
        membership = Membership.objects.create(
            user=user2,
            organization=organization,
            role=MembershipRole.ADMIN,
        )
        assert not membership.is_owner
        assert membership.is_admin
        assert membership.can_manage_members
        assert not membership.can_delete_organization

    def test_viewer_role_permissions(self, organization, user2):
        """Test viewer role has minimal permissions."""
        membership = Membership.objects.create(
            user=user2,
            organization=organization,
            role=MembershipRole.VIEWER,
        )
        assert not membership.is_owner
        assert not membership.is_admin
        assert not membership.can_manage_members
        assert not membership.can_delete_organization

    def test_membership_str(self, user, organization):
        """Test membership string representation."""
        membership = Membership.objects.get(user=user, organization=organization)
        assert user.email in str(membership)
        assert organization.name in str(membership)


@pytest.mark.django_db
class TestInvitationModel:
    """Test invitation model functionality."""

    def test_create_invitation(self, organization, user):
        """Test creating an invitation."""
        from datetime import timedelta

        from django.utils import timezone

        invitation = Invitation.objects.create(
            organization=organization,
            email="invite@example.com",
            role=MembershipRole.MEMBER,
            token="test-token-12345",
            invited_by=user,
            expires_at=timezone.now() + timedelta(days=7),
        )
        assert invitation.email == "invite@example.com"
        assert invitation.role == MembershipRole.MEMBER
        assert invitation.is_pending
        assert not invitation.is_expired
        assert "invite@example.com" in str(invitation)

    def test_invitation_expired(self, organization, user):
        """Test expired invitation."""
        from datetime import timedelta

        from django.utils import timezone

        invitation = Invitation.objects.create(
            organization=organization,
            email="expired@example.com",
            role=MembershipRole.MEMBER,
            token="expired-token",
            invited_by=user,
            expires_at=timezone.now() - timedelta(days=1),  # Expired
        )
        assert invitation.is_expired

    def test_invitation_revoke(self, organization, user):
        """Test revoking an invitation."""
        from datetime import timedelta

        from django.utils import timezone

        invitation = Invitation.objects.create(
            organization=organization,
            email="revoke@example.com",
            role=MembershipRole.MEMBER,
            token="revoke-token",
            invited_by=user,
            expires_at=timezone.now() + timedelta(days=7),
        )
        invitation.revoke()
        assert invitation.status == InvitationStatus.REVOKED


@pytest.mark.django_db
class TestOrganizationSchemas:
    """Test organization Pydantic schemas."""

    def test_organization_create_schema(self):
        """Test OrganizationCreateSchema validation."""
        from apps.organizations.schemas import OrganizationCreateSchema

        data = OrganizationCreateSchema(
            name="Test Org",
            slug="test-org",
            description="A test organization",
        )
        assert data.name == "Test Org"
        assert data.slug == "test-org"

    def test_organization_update_schema(self):
        """Test OrganizationUpdateSchema validation."""
        from apps.organizations.schemas import OrganizationUpdateSchema

        data = OrganizationUpdateSchema(name="Updated Name")
        assert data.name == "Updated Name"
        assert data.description is None

    def test_team_create_schema(self):
        """Test TeamCreateSchema validation."""
        from apps.organizations.schemas import TeamCreateSchema

        data = TeamCreateSchema(
            name="New Team",
            slug="new-team",
            description="A new team",
        )
        assert data.name == "New Team"
        assert data.slug == "new-team"

    def test_invitation_create_schema(self):
        """Test InvitationCreateSchema validation."""
        from apps.organizations.schemas import InvitationCreateSchema

        data = InvitationCreateSchema(
            email="newmember@example.com",
            role="member",
            message="Welcome!",
        )
        assert data.email == "newmember@example.com"
        assert data.role == "member"
        assert data.message == "Welcome!"

    def test_membership_update_schema(self):
        """Test MembershipUpdateSchema validation."""
        from apps.organizations.schemas import MembershipUpdateSchema

        data = MembershipUpdateSchema(
            role="admin",
            job_title="Engineer",
            department="Engineering",
        )
        assert data.role == "admin"
        assert data.job_title == "Engineer"
