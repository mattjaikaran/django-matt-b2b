"""Team API controller."""

from __future__ import annotations

from uuid import UUID

from django_matt.auth import jwt_required
from django_matt.core import APIController
from django_matt.core.errors import NotFoundAPIError, ValidationAPIError

from ..models import Membership, Team
from ..schemas import (
    TeamCreateSchema,
    TeamDetailSchema,
    TeamMemberAddSchema,
    TeamSchema,
    TeamUpdateSchema,
)
from .utils import build_membership_schema, get_membership, require_admin


class TeamController(APIController):
    """Team management controller."""

    tags = ["Teams"]

    @staticmethod
    @jwt_required
    async def list_teams(request, org_id: UUID) -> list[TeamSchema]:
        """List teams in an organization."""
        await get_membership(request.user, org_id)

        teams = Team.objects.filter(organization_id=org_id)
        return [
            TeamSchema(
                id=team.id,
                organization_id=team.organization_id,
                name=team.name,
                slug=team.slug,
                description=team.description,
                member_count=team.member_count,
                created_at=team.created_at,
            )
            async for team in teams
        ]

    @staticmethod
    @jwt_required
    async def create_team(request, org_id: UUID, body: TeamCreateSchema) -> TeamSchema:
        """Create a new team (admin only)."""
        await require_admin(request.user, org_id)

        # Check if slug is taken in this org
        if await Team.objects.filter(organization_id=org_id, slug=body.slug).aexists():
            raise ValidationAPIError("Team slug already taken in this organization")

        team = await Team.objects.acreate(
            organization_id=org_id,
            name=body.name,
            slug=body.slug,
            description=body.description,
        )

        return TeamSchema(
            id=team.id,
            organization_id=team.organization_id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            member_count=0,
            created_at=team.created_at,
        )

    @staticmethod
    @jwt_required
    async def get_team(request, org_id: UUID, team_id: UUID) -> TeamDetailSchema:
        """Get team details with members."""
        await get_membership(request.user, org_id)

        try:
            team = await Team.objects.aget(id=team_id, organization_id=org_id)
        except Team.DoesNotExist:
            raise NotFoundAPIError("Team not found")

        # Get team members
        members = []
        async for m in team.members.filter(is_active=True).select_related("user", "organization"):
            members.append(build_membership_schema(m))

        return TeamDetailSchema(
            id=team.id,
            organization_id=team.organization_id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            member_count=len(members),
            created_at=team.created_at,
            members=members,
        )

    @staticmethod
    @jwt_required
    async def update_team(
        request, org_id: UUID, team_id: UUID, body: TeamUpdateSchema
    ) -> TeamSchema:
        """Update a team (admin only)."""
        await require_admin(request.user, org_id)

        try:
            team = await Team.objects.aget(id=team_id, organization_id=org_id)
        except Team.DoesNotExist:
            raise NotFoundAPIError("Team not found")

        update_data = body.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(team, field, value)

        await team.asave()

        return TeamSchema(
            id=team.id,
            organization_id=team.organization_id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            member_count=team.member_count,
            created_at=team.created_at,
        )

    @staticmethod
    @jwt_required
    async def delete_team(request, org_id: UUID, team_id: UUID) -> dict:
        """Delete a team (admin only)."""
        await require_admin(request.user, org_id)

        try:
            team = await Team.objects.aget(id=team_id, organization_id=org_id)
        except Team.DoesNotExist:
            raise NotFoundAPIError("Team not found")

        await team.adelete()
        return {"message": "Team deleted"}

    @staticmethod
    @jwt_required
    async def add_member_to_team(
        request, org_id: UUID, team_id: UUID, body: TeamMemberAddSchema
    ) -> TeamDetailSchema:
        """Add a member to a team (admin only)."""
        await require_admin(request.user, org_id)

        try:
            team = await Team.objects.aget(id=team_id, organization_id=org_id)
        except Team.DoesNotExist:
            raise NotFoundAPIError("Team not found")

        try:
            membership = await Membership.objects.select_related("user", "organization").aget(
                id=body.member_id, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Member not found")

        await team.members.aadd(membership)

        # Return updated team
        return await TeamController.get_team(request, org_id, team_id)

    @staticmethod
    @jwt_required
    async def remove_member_from_team(
        request, org_id: UUID, team_id: UUID, member_id: UUID
    ) -> TeamDetailSchema:
        """Remove a member from a team (admin only)."""
        await require_admin(request.user, org_id)

        try:
            team = await Team.objects.aget(id=team_id, organization_id=org_id)
        except Team.DoesNotExist:
            raise NotFoundAPIError("Team not found")

        try:
            membership = await Membership.objects.aget(id=member_id, organization_id=org_id)
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Member not found")

        await team.members.aremove(membership)

        # Return updated team
        return await TeamController.get_team(request, org_id, team_id)
