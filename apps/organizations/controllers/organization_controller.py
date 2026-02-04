"""Organization API controller."""

from __future__ import annotations

from uuid import UUID

from django.conf import settings as django_settings
from django.db import transaction
from django_matt.auth import jwt_required
from django_matt.core import APIController
from django_matt.core.errors import ValidationAPIError

from ..models import Membership, MembershipRole, Organization
from ..schemas import (
    OrganizationCreateSchema,
    OrganizationSchema,
    OrganizationSettingsSchema,
    OrganizationSettingsUpdateSchema,
    OrganizationUpdateSchema,
    OrganizationWithRoleSchema,
)
from .utils import get_membership, require_admin


class OrganizationController(APIController):
    """Organization management controller."""

    tags = ["Organizations"]

    @staticmethod
    @jwt_required
    async def list_organizations(request) -> list[OrganizationWithRoleSchema]:
        """List organizations the current user belongs to."""
        memberships = Membership.objects.filter(user=request.user, is_active=True).select_related(
            "organization"
        )

        result = []
        async for membership in memberships:
            org = membership.organization
            result.append(
                OrganizationWithRoleSchema(
                    id=org.id,
                    name=org.name,
                    slug=org.slug,
                    description=org.description,
                    logo_url=org.logo_url,
                    plan=org.plan,
                    role=membership.role,
                    is_active=membership.is_active,
                    member_count=org.member_count,
                    team_count=org.team_count,
                )
            )
        return result

    @staticmethod
    @jwt_required
    async def create_organization(request, body: OrganizationCreateSchema) -> OrganizationSchema:
        """Create a new organization."""
        # Check if slug is taken
        if await Organization.objects.filter(slug=body.slug).aexists():
            raise ValidationAPIError("Organization slug already taken")

        async with transaction.atomic():
            # Create organization
            org = await Organization.objects.acreate(
                name=body.name,
                slug=body.slug,
                description=body.description,
                logo_url=body.logo_url,
                website=body.website,
                plan=getattr(django_settings, "DEFAULT_ORG_PLAN", "free"),
            )

            # Add creator as owner
            await Membership.objects.acreate(
                user=request.user,
                organization=org,
                role=MembershipRole.OWNER,
            )

        return OrganizationSchema(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            logo_url=org.logo_url,
            website=org.website,
            plan=org.plan,
            member_count=1,
            team_count=0,
            created_at=org.created_at,
        )

    @staticmethod
    @jwt_required
    async def get_organization(request, org_id: UUID) -> OrganizationSchema:
        """Get organization details."""
        membership = await get_membership(request.user, org_id)
        org = membership.organization

        return OrganizationSchema(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            logo_url=org.logo_url,
            website=org.website,
            plan=org.plan,
            member_count=org.member_count,
            team_count=org.team_count,
            created_at=org.created_at,
        )

    @staticmethod
    @jwt_required
    async def update_organization(
        request, org_id: UUID, body: OrganizationUpdateSchema
    ) -> OrganizationSchema:
        """Update organization (admin only)."""
        membership = await require_admin(request.user, org_id)
        org = membership.organization

        update_data = body.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(org, field, value)

        await org.asave()

        return OrganizationSchema(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            logo_url=org.logo_url,
            website=org.website,
            plan=org.plan,
            member_count=org.member_count,
            team_count=org.team_count,
            created_at=org.created_at,
        )

    @staticmethod
    @jwt_required
    async def delete_organization(request, org_id: UUID) -> dict:
        """Delete organization (owner only)."""
        from .utils import require_owner

        membership = await require_owner(request.user, org_id)
        await membership.organization.adelete()
        return {"message": "Organization deleted"}

    @staticmethod
    @jwt_required
    async def get_settings(request, org_id: UUID) -> OrganizationSettingsSchema:
        """Get organization settings (admin only)."""
        membership = await require_admin(request.user, org_id)
        org = membership.organization

        # Get settings from JSON field with defaults
        settings = org.settings or {}
        return OrganizationSettingsSchema(
            allow_member_invites=settings.get("allow_member_invites", False),
            default_member_role=settings.get("default_member_role", "member"),
            require_2fa=settings.get("require_2fa", False),
            allowed_email_domains=settings.get("allowed_email_domains", []),
        )

    @staticmethod
    @jwt_required
    async def update_settings(
        request, org_id: UUID, body: OrganizationSettingsUpdateSchema
    ) -> OrganizationSettingsSchema:
        """Update organization settings (admin only)."""
        membership = await require_admin(request.user, org_id)
        org = membership.organization

        # Merge new settings with existing
        settings = org.settings or {}
        update_data = body.model_dump(exclude_unset=True)
        settings.update(update_data)
        org.settings = settings
        await org.asave()

        return OrganizationSettingsSchema(
            allow_member_invites=settings.get("allow_member_invites", False),
            default_member_role=settings.get("default_member_role", "member"),
            require_2fa=settings.get("require_2fa", False),
            allowed_email_domains=settings.get("allowed_email_domains", []),
        )
