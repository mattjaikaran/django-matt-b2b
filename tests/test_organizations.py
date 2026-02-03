"""Tests for organization endpoints."""

import pytest
from django.contrib.auth import get_user_model

from apps.organizations.models import Invitation, InvitationStatus, Membership, MembershipRole

User = get_user_model()


@pytest.mark.django_db
class TestOrganizationEndpoints:
    """Test organization endpoints."""

    async def test_list_organizations(self, authenticated_client, organization):
        """Test listing user's organizations."""
        response = await authenticated_client.get("/api/organizations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Organization"
        assert data[0]["role"] == "owner"

    async def test_create_organization(self, authenticated_client):
        """Test creating an organization."""
        response = await authenticated_client.post(
            "/api/organizations",
            data={
                "name": "New Organization",
                "slug": "new-org",
                "description": "A new test organization",
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Organization"
        assert data["slug"] == "new-org"

    async def test_create_organization_duplicate_slug(self, authenticated_client, organization):
        """Test creating organization with duplicate slug fails."""
        response = await authenticated_client.post(
            "/api/organizations",
            data={
                "name": "Another Organization",
                "slug": "test-org",  # Same as fixture
            },
            content_type="application/json",
        )
        assert response.status_code == 422

    async def test_get_organization(self, authenticated_client, organization):
        """Test getting organization details."""
        response = await authenticated_client.get(f"/api/organizations/{organization.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Organization"

    async def test_update_organization(self, authenticated_client, organization):
        """Test updating organization."""
        response = await authenticated_client.patch(
            f"/api/organizations/{organization.id}",
            data={"name": "Updated Organization"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Organization"

    async def test_update_organization_member_forbidden(self, member_client, organization):
        """Test that regular members cannot update organization."""
        response = await member_client.patch(
            f"/api/organizations/{organization.id}",
            data={"name": "Hacked Organization"},
            content_type="application/json",
        )
        assert response.status_code == 403

    async def test_delete_organization(self, authenticated_client, user):
        """Test deleting organization."""
        from apps.organizations.models import Organization

        # Create a new org to delete
        org = Organization.objects.create(name="To Delete", slug="to-delete")
        Membership.objects.create(user=user, organization=org, role=MembershipRole.OWNER)

        response = await authenticated_client.delete(f"/api/organizations/{org.id}")
        assert response.status_code == 200
        assert not Organization.objects.filter(id=org.id).exists()

    async def test_delete_organization_member_forbidden(self, member_client, organization):
        """Test that regular members cannot delete organization."""
        response = await member_client.delete(f"/api/organizations/{organization.id}")
        assert response.status_code == 403


@pytest.mark.django_db
class TestTeamEndpoints:
    """Test team endpoints."""

    async def test_list_teams(self, authenticated_client, organization, team):
        """Test listing teams."""
        response = await authenticated_client.get(f"/api/organizations/{organization.id}/teams")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Team"

    async def test_create_team(self, authenticated_client, organization):
        """Test creating a team."""
        response = await authenticated_client.post(
            f"/api/organizations/{organization.id}/teams",
            data={
                "name": "New Team",
                "slug": "new-team",
                "description": "A new team",
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Team"

    async def test_create_team_member_forbidden(self, member_client, organization):
        """Test that regular members cannot create teams."""
        response = await member_client.post(
            f"/api/organizations/{organization.id}/teams",
            data={"name": "Sneaky Team", "slug": "sneaky"},
            content_type="application/json",
        )
        assert response.status_code == 403

    async def test_get_team(self, authenticated_client, organization, team):
        """Test getting team details."""
        response = await authenticated_client.get(
            f"/api/organizations/{organization.id}/teams/{team.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Team"
        assert "members" in data

    async def test_update_team(self, authenticated_client, organization, team):
        """Test updating a team."""
        response = await authenticated_client.patch(
            f"/api/organizations/{organization.id}/teams/{team.id}",
            data={"name": "Updated Team"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Team"

    async def test_delete_team(self, authenticated_client, organization, team):
        """Test deleting a team."""
        response = await authenticated_client.delete(
            f"/api/organizations/{organization.id}/teams/{team.id}"
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestMemberEndpoints:
    """Test member endpoints."""

    async def test_list_members(self, authenticated_client, organization, member_user):
        """Test listing members."""
        response = await authenticated_client.get(f"/api/organizations/{organization.id}/members")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Owner + member

    async def test_update_member_role(self, authenticated_client, organization, member_user):
        """Test updating member role."""
        membership = Membership.objects.get(user=member_user, organization=organization)
        response = await authenticated_client.patch(
            f"/api/organizations/{organization.id}/members/{membership.id}",
            data={"role": "admin"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    async def test_remove_member(self, authenticated_client, organization, member_user):
        """Test removing a member."""
        membership = Membership.objects.get(user=member_user, organization=organization)
        response = await authenticated_client.delete(
            f"/api/organizations/{organization.id}/members/{membership.id}"
        )
        assert response.status_code == 200

    async def test_cannot_remove_owner(self, authenticated_client, organization, user):
        """Test that owner cannot be removed."""
        membership = Membership.objects.get(user=user, organization=organization)
        response = await authenticated_client.delete(
            f"/api/organizations/{organization.id}/members/{membership.id}"
        )
        assert response.status_code == 422

    async def test_leave_organization(self, member_client, organization, member_user):
        """Test leaving an organization."""
        response = await member_client.post(f"/api/organizations/{organization.id}/leave")
        assert response.status_code == 200
        assert not Membership.objects.filter(
            user=member_user, organization=organization
        ).exists()

    async def test_owner_cannot_leave_alone(self, authenticated_client, organization, user):
        """Test that sole owner cannot leave."""
        response = await authenticated_client.post(f"/api/organizations/{organization.id}/leave")
        assert response.status_code == 422


@pytest.mark.django_db
class TestInvitationEndpoints:
    """Test invitation endpoints."""

    async def test_create_invitation(self, authenticated_client, organization):
        """Test creating an invitation."""
        response = await authenticated_client.post(
            f"/api/organizations/{organization.id}/invitations",
            data={
                "email": "newmember@example.com",
                "role": "member",
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newmember@example.com"
        assert data["status"] == "pending"

    async def test_list_invitations(self, authenticated_client, organization):
        """Test listing invitations."""
        # Create an invitation first
        Invitation.objects.create(
            organization=organization,
            email="pending@example.com",
            role=MembershipRole.MEMBER,
            token="test-token-123",
            expires_at="2099-01-01T00:00:00Z",
        )

        response = await authenticated_client.get(
            f"/api/organizations/{organization.id}/invitations"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    async def test_accept_invitation(self, authenticated_client2, organization, user2):
        """Test accepting an invitation."""
        # Create invitation for user2
        invitation = Invitation.objects.create(
            organization=organization,
            email="test2@example.com",
            role=MembershipRole.MEMBER,
            token="accept-token-123",
            expires_at="2099-01-01T00:00:00Z",
        )

        response = await authenticated_client2.post(
            f"/api/invitations/{invitation.token}/accept"
        )
        assert response.status_code == 200
        assert Membership.objects.filter(
            user=user2, organization=organization
        ).exists()

    async def test_decline_invitation(self, authenticated_client2, organization, user2):
        """Test declining an invitation."""
        invitation = Invitation.objects.create(
            organization=organization,
            email="test2@example.com",
            role=MembershipRole.MEMBER,
            token="decline-token-123",
            expires_at="2099-01-01T00:00:00Z",
        )

        response = await authenticated_client2.post(
            f"/api/invitations/{invitation.token}/decline"
        )
        assert response.status_code == 200

        invitation.refresh_from_db()
        assert invitation.status == InvitationStatus.DECLINED

    async def test_cancel_invitation(self, authenticated_client, organization):
        """Test cancelling an invitation."""
        invitation = Invitation.objects.create(
            organization=organization,
            email="cancel@example.com",
            role=MembershipRole.MEMBER,
            token="cancel-token-123",
            expires_at="2099-01-01T00:00:00Z",
        )

        response = await authenticated_client.delete(
            f"/api/organizations/{organization.id}/invitations/{invitation.id}"
        )
        assert response.status_code == 200

        invitation.refresh_from_db()
        assert invitation.status == InvitationStatus.REVOKED

    async def test_cannot_invite_existing_member(self, authenticated_client, organization, member_user):
        """Test that existing members cannot be invited again."""
        response = await authenticated_client.post(
            f"/api/organizations/{organization.id}/invitations",
            data={"email": member_user.email, "role": "member"},
            content_type="application/json",
        )
        assert response.status_code == 422

    async def test_get_my_invitations(self, authenticated_client2, organization, user2):
        """Test getting user's pending invitations."""
        Invitation.objects.create(
            organization=organization,
            email="test2@example.com",
            role=MembershipRole.MEMBER,
            token="my-inv-token",
            expires_at="2099-01-01T00:00:00Z",
        )

        response = await authenticated_client2.get("/api/invitations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["organization_name"] == "Test Organization"
