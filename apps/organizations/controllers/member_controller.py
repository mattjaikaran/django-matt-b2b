"""Member API controller."""

from __future__ import annotations

from uuid import UUID

from django.db import transaction

from django_matt.auth import jwt_required
from django_matt.core import APIController
from django_matt.core.errors import NotFoundAPIError, ValidationAPIError

from ..models import Membership, MembershipRole
from ..schemas import MembershipSchema, MembershipUpdateSchema
from .utils import build_membership_schema, get_membership, require_admin, require_owner


class MemberController(APIController):
    """Member management controller."""

    tags = ["Members"]

    @staticmethod
    @jwt_required
    async def list_members(request, org_id: UUID) -> list[MembershipSchema]:
        """List members of an organization."""
        await get_membership(request.user, org_id)

        memberships = Membership.objects.filter(organization_id=org_id).select_related(
            "user", "organization"
        )

        return [build_membership_schema(m) async for m in memberships]

    @staticmethod
    @jwt_required
    async def get_member(request, org_id: UUID, member_id: UUID) -> MembershipSchema:
        """Get member details."""
        await get_membership(request.user, org_id)

        try:
            membership = await Membership.objects.select_related("user", "organization").aget(
                id=member_id, organization_id=org_id
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Member not found")

        return build_membership_schema(membership)

    @staticmethod
    @jwt_required
    async def update_member(
        request, org_id: UUID, member_id: UUID, body: MembershipUpdateSchema
    ) -> MembershipSchema:
        """Update a member's role/info (admin only)."""
        admin_membership = await require_admin(request.user, org_id)

        try:
            membership = await Membership.objects.select_related("user", "organization").aget(
                id=member_id, organization_id=org_id
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Member not found")

        # Can't change owner's role unless you're also an owner
        if membership.is_owner and body.role and body.role != MembershipRole.OWNER:
            if not admin_membership.is_owner:
                raise ValidationAPIError("Only owners can change another owner's role")

        update_data = body.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(membership, field, value)

        await membership.asave()
        return build_membership_schema(membership)

    @staticmethod
    @jwt_required
    async def remove_member(request, org_id: UUID, member_id: UUID) -> dict:
        """Remove a member from organization (admin only)."""
        await require_admin(request.user, org_id)

        try:
            membership = await Membership.objects.aget(id=member_id, organization_id=org_id)
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Member not found")

        # Can't remove owner
        if membership.is_owner:
            raise ValidationAPIError("Cannot remove organization owner")

        # Can't remove yourself (use leave endpoint instead)
        if membership.user_id == request.user.id:
            raise ValidationAPIError("Cannot remove yourself. Use leave endpoint instead.")

        await membership.adelete()
        return {"message": "Member removed"}

    @staticmethod
    @jwt_required
    async def leave_organization(request, org_id: UUID) -> dict:
        """Leave an organization."""
        membership = await get_membership(request.user, org_id)

        # Owner can't leave unless they transfer ownership
        if membership.is_owner:
            # Check if there are other owners
            owner_count = await Membership.objects.filter(
                organization_id=org_id, role=MembershipRole.OWNER, is_active=True
            ).acount()
            if owner_count <= 1:
                raise ValidationAPIError(
                    "Cannot leave: you are the only owner. "
                    "Transfer ownership first or delete the organization."
                )

        await membership.adelete()
        return {"message": "You have left the organization"}

    @staticmethod
    @jwt_required
    async def transfer_ownership(request, org_id: UUID, member_id: UUID) -> MembershipSchema:
        """Transfer ownership to another member (owner only)."""
        current_membership = await require_owner(request.user, org_id)

        if current_membership.id == member_id:
            raise ValidationAPIError("Cannot transfer ownership to yourself")

        try:
            new_owner = await Membership.objects.select_related("user", "organization").aget(
                id=member_id, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Member not found")

        async with transaction.atomic():
            # Make new member owner
            new_owner.role = MembershipRole.OWNER
            await new_owner.asave()

            # Demote current owner to admin
            current_membership.role = MembershipRole.ADMIN
            await current_membership.asave()

        return build_membership_schema(new_owner)
