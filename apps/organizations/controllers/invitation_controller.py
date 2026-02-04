"""Invitation API controller."""

from __future__ import annotations

import secrets
from datetime import timedelta
from uuid import UUID

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from django_matt.auth import jwt_required
from django_matt.core import APIController
from django_matt.core.errors import APIError, NotFoundAPIError, ValidationAPIError

from ..models import Invitation, InvitationStatus, Membership, Team
from ..schemas import (
    BulkInviteResultSchema,
    BulkInviteSchema,
    InvitationCreateSchema,
    InvitationSchema,
    MembershipSchema,
)
from .utils import build_membership_schema, require_admin

User = get_user_model()


class InvitationController(APIController):
    """Invitation management controller."""

    tags = ["Invitations"]

    @staticmethod
    @jwt_required
    async def list_invitations(request, org_id: UUID) -> list[InvitationSchema]:
        """List pending invitations (admin only)."""
        await require_admin(request.user, org_id)

        invitations = Invitation.objects.filter(
            organization_id=org_id, status=InvitationStatus.PENDING
        ).select_related("organization", "invited_by")

        result = []
        async for inv in invitations:
            result.append(
                InvitationSchema(
                    id=inv.id,
                    organization_id=inv.organization_id,
                    organization_name=inv.organization.name,
                    email=inv.email,
                    role=inv.role,
                    status=inv.status,
                    message=inv.message,
                    invited_by_email=inv.invited_by.email if inv.invited_by else None,
                    expires_at=inv.expires_at,
                    created_at=inv.created_at,
                )
            )
        return result

    @staticmethod
    @jwt_required
    async def create_invitation(
        request, org_id: UUID, body: InvitationCreateSchema
    ) -> InvitationSchema:
        """Invite a user to organization (admin only)."""
        membership = await require_admin(request.user, org_id)
        org = membership.organization

        # Check if user already a member
        if await User.objects.filter(
            email=body.email, memberships__organization_id=org_id
        ).aexists():
            raise ValidationAPIError("User is already a member")

        # Check for existing pending invitation
        if await Invitation.objects.filter(
            email=body.email, organization_id=org_id, status=InvitationStatus.PENDING
        ).aexists():
            raise ValidationAPIError("Invitation already pending for this email")

        # Check email domain restrictions
        settings = org.settings or {}
        allowed_domains = settings.get("allowed_email_domains", [])
        if allowed_domains:
            email_domain = body.email.split("@")[1]
            if email_domain not in allowed_domains:
                raise ValidationAPIError(
                    f"Email domain not allowed. Allowed domains: {', '.join(allowed_domains)}"
                )

        expiry_days = getattr(django_settings, "INVITATION_EXPIRY_DAYS", 7)
        invitation = await Invitation.objects.acreate(
            organization_id=org_id,
            email=body.email,
            role=body.role,
            message=body.message,
            invited_by=request.user,
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(days=expiry_days),
        )

        # Add teams if specified
        if body.team_ids:
            teams = Team.objects.filter(id__in=body.team_ids, organization_id=org_id)
            async for team in teams:
                await invitation.teams.aadd(team)

        # TODO: Send invitation email

        return InvitationSchema(
            id=invitation.id,
            organization_id=invitation.organization_id,
            organization_name=org.name,
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            message=invitation.message,
            invited_by_email=request.user.email,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )

    @staticmethod
    @jwt_required
    async def bulk_invite(request, org_id: UUID, body: BulkInviteSchema) -> BulkInviteResultSchema:
        """Bulk invite users (admin only)."""
        await require_admin(request.user, org_id)

        sent = 0
        failed = 0
        errors = []

        expiry_days = getattr(django_settings, "INVITATION_EXPIRY_DAYS", 7)

        for email in body.emails:
            try:
                # Check if user already a member
                if await User.objects.filter(
                    email=email, memberships__organization_id=org_id
                ).aexists():
                    errors.append(f"{email}: Already a member")
                    failed += 1
                    continue

                # Check for existing pending invitation
                if await Invitation.objects.filter(
                    email=email, organization_id=org_id, status=InvitationStatus.PENDING
                ).aexists():
                    errors.append(f"{email}: Invitation already pending")
                    failed += 1
                    continue

                await Invitation.objects.acreate(
                    organization_id=org_id,
                    email=email,
                    role=body.role,
                    message=body.message,
                    invited_by=request.user,
                    token=secrets.token_urlsafe(32),
                    expires_at=timezone.now() + timedelta(days=expiry_days),
                )
                sent += 1

            except Exception as e:
                errors.append(f"{email}: {str(e)}")
                failed += 1

        # TODO: Send invitation emails

        return BulkInviteResultSchema(sent=sent, failed=failed, errors=errors)

    @staticmethod
    @jwt_required
    async def get_my_invitations(request) -> list[InvitationSchema]:
        """Get invitations for the current user."""
        invitations = Invitation.objects.filter(
            email=request.user.email, status=InvitationStatus.PENDING
        ).select_related("organization", "invited_by")

        result = []
        async for inv in invitations:
            # Check if expired
            if inv.is_expired:
                inv.mark_expired()
                continue

            result.append(
                InvitationSchema(
                    id=inv.id,
                    organization_id=inv.organization_id,
                    organization_name=inv.organization.name,
                    email=inv.email,
                    role=inv.role,
                    status=inv.status,
                    message=inv.message,
                    invited_by_email=inv.invited_by.email if inv.invited_by else None,
                    expires_at=inv.expires_at,
                    created_at=inv.created_at,
                )
            )
        return result

    @staticmethod
    @jwt_required
    async def accept_invitation(request, token: str) -> MembershipSchema:
        """Accept an invitation."""
        try:
            invitation = await Invitation.objects.select_related("organization").aget(
                token=token, status=InvitationStatus.PENDING
            )
        except Invitation.DoesNotExist:
            raise NotFoundAPIError("Invalid or expired invitation")

        if invitation.is_expired:
            invitation.mark_expired()
            raise APIError(status_code=400, message="Invitation has expired")

        if invitation.email != request.user.email:
            raise APIError(status_code=403, message="Invitation is for a different email")

        async with transaction.atomic():
            # Create membership
            membership = await Membership.objects.acreate(
                user=request.user,
                organization=invitation.organization,
                role=invitation.role,
            )

            # Add to teams if specified
            async for team in invitation.teams.all():
                await membership.teams.aadd(team)

            # Mark invitation as accepted
            invitation.status = InvitationStatus.ACCEPTED
            await invitation.asave()

        # Reload with related objects
        membership = await Membership.objects.select_related("user", "organization").aget(
            id=membership.id
        )

        return build_membership_schema(membership)

    @staticmethod
    @jwt_required
    async def decline_invitation(request, token: str) -> dict:
        """Decline an invitation."""
        try:
            invitation = await Invitation.objects.aget(token=token, status=InvitationStatus.PENDING)
        except Invitation.DoesNotExist:
            raise NotFoundAPIError("Invalid or expired invitation")

        if invitation.email != request.user.email:
            raise APIError(status_code=403, message="Invitation is for a different email")

        invitation.status = InvitationStatus.DECLINED
        await invitation.asave()

        return {"message": "Invitation declined"}

    @staticmethod
    @jwt_required
    async def cancel_invitation(request, org_id: UUID, invitation_id: UUID) -> dict:
        """Cancel/revoke an invitation (admin only)."""
        await require_admin(request.user, org_id)

        try:
            invitation = await Invitation.objects.aget(
                id=invitation_id, organization_id=org_id, status=InvitationStatus.PENDING
            )
        except Invitation.DoesNotExist:
            raise NotFoundAPIError("Invitation not found")

        invitation.revoke()
        return {"message": "Invitation cancelled"}

    @staticmethod
    @jwt_required
    async def resend_invitation(request, org_id: UUID, invitation_id: UUID) -> InvitationSchema:
        """Resend an invitation (admin only)."""
        await require_admin(request.user, org_id)

        try:
            invitation = await Invitation.objects.select_related("organization").aget(
                id=invitation_id, organization_id=org_id, status=InvitationStatus.PENDING
            )
        except Invitation.DoesNotExist:
            raise NotFoundAPIError("Invitation not found")

        # Extend expiration
        expiry_days = getattr(django_settings, "INVITATION_EXPIRY_DAYS", 7)
        invitation.expires_at = timezone.now() + timedelta(days=expiry_days)
        await invitation.asave()

        # TODO: Resend invitation email

        return InvitationSchema(
            id=invitation.id,
            organization_id=invitation.organization_id,
            organization_name=invitation.organization.name,
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            message=invitation.message,
            invited_by_email=invitation.invited_by.email if invitation.invited_by else None,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )
