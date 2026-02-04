"""Shared controller utilities."""

from __future__ import annotations

from uuid import UUID

from django_matt.core.errors import APIError, NotFoundAPIError

from ..models import Membership, MembershipRole
from ..schemas import MembershipSchema


async def get_membership(user, org_id: UUID, require_active: bool = True) -> Membership:
    """Get user's membership in an organization."""
    try:
        query = Membership.objects.select_related("organization")
        if require_active:
            query = query.filter(is_active=True)
        return await query.aget(user=user, organization_id=org_id)
    except Membership.DoesNotExist:
        raise NotFoundAPIError("Organization not found")


async def require_admin(user, org_id: UUID) -> Membership:
    """Require admin access to an organization."""
    membership = await get_membership(user, org_id)
    if not membership.is_admin:
        raise APIError(status_code=403, message="Admin access required")
    return membership


async def require_owner(user, org_id: UUID) -> Membership:
    """Require owner access to an organization."""
    membership = await get_membership(user, org_id)
    if not membership.is_owner:
        raise APIError(status_code=403, message="Owner access required")
    return membership


def build_membership_schema(membership: Membership) -> MembershipSchema:
    """Build a MembershipSchema from a Membership model."""
    return MembershipSchema(
        id=membership.id,
        user_id=membership.user_id,
        user_email=membership.user.email,
        user_name=membership.user.full_name,
        organization_id=membership.organization_id,
        organization_name=membership.organization.name,
        role=membership.role,
        job_title=membership.job_title,
        department=membership.department,
        is_active=membership.is_active,
        created_at=membership.created_at,
    )
