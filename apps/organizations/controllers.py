"""Organization API controllers."""

import secrets
from datetime import timedelta
from uuid import UUID

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django_matt import MattAPI
from django_matt.auth import jwt_required
from django_matt.core import APIController
from django_matt.core.errors import APIError, NotFoundAPIError, ValidationAPIError

from .models import Invitation, InvitationStatus, Membership, MembershipRole, Organization, Team
from .schemas import (
    BulkInviteResultSchema,
    BulkInviteSchema,
    InvitationCreateSchema,
    InvitationSchema,
    MembershipSchema,
    MembershipUpdateSchema,
    OrganizationCreateSchema,
    OrganizationSchema,
    OrganizationSettingsSchema,
    OrganizationSettingsUpdateSchema,
    OrganizationUpdateSchema,
    OrganizationWithRoleSchema,
    TeamCreateSchema,
    TeamDetailSchema,
    TeamMemberAddSchema,
    TeamSchema,
    TeamUpdateSchema,
)

User = get_user_model()


# =============================================================================
# Helper functions
# =============================================================================


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


# =============================================================================
# Organization Controller
# =============================================================================


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


# =============================================================================
# Team Controller
# =============================================================================


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


# =============================================================================
# Member Controller
# =============================================================================


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


# =============================================================================
# Invitation Controller
# =============================================================================


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


# =============================================================================
# Route Registration
# =============================================================================


def register_org_routes(api: MattAPI) -> None:
    """Register organization routes on the API."""

    # Organizations
    api.get(
        "organizations", response_model=list[OrganizationWithRoleSchema], tags=["Organizations"]
    )(OrganizationController.list_organizations)
    api.post("organizations", response_model=OrganizationSchema, tags=["Organizations"])(
        OrganizationController.create_organization
    )
    api.get("organizations/{org_id}", response_model=OrganizationSchema, tags=["Organizations"])(
        OrganizationController.get_organization
    )
    api.patch("organizations/{org_id}", response_model=OrganizationSchema, tags=["Organizations"])(
        OrganizationController.update_organization
    )
    api.delete("organizations/{org_id}", tags=["Organizations"])(
        OrganizationController.delete_organization
    )

    # Organization settings
    api.get(
        "organizations/{org_id}/settings",
        response_model=OrganizationSettingsSchema,
        tags=["Organizations"],
    )(OrganizationController.get_settings)
    api.patch(
        "organizations/{org_id}/settings",
        response_model=OrganizationSettingsSchema,
        tags=["Organizations"],
    )(OrganizationController.update_settings)

    # Teams
    api.get("organizations/{org_id}/teams", response_model=list[TeamSchema], tags=["Teams"])(
        TeamController.list_teams
    )
    api.post("organizations/{org_id}/teams", response_model=TeamSchema, tags=["Teams"])(
        TeamController.create_team
    )
    api.get(
        "organizations/{org_id}/teams/{team_id}", response_model=TeamDetailSchema, tags=["Teams"]
    )(TeamController.get_team)
    api.patch("organizations/{org_id}/teams/{team_id}", response_model=TeamSchema, tags=["Teams"])(
        TeamController.update_team
    )
    api.delete("organizations/{org_id}/teams/{team_id}", tags=["Teams"])(TeamController.delete_team)
    api.post(
        "organizations/{org_id}/teams/{team_id}/members",
        response_model=TeamDetailSchema,
        tags=["Teams"],
    )(TeamController.add_member_to_team)
    api.delete(
        "organizations/{org_id}/teams/{team_id}/members/{member_id}",
        response_model=TeamDetailSchema,
        tags=["Teams"],
    )(TeamController.remove_member_from_team)

    # Members
    api.get(
        "organizations/{org_id}/members", response_model=list[MembershipSchema], tags=["Members"]
    )(MemberController.list_members)
    api.get(
        "organizations/{org_id}/members/{member_id}",
        response_model=MembershipSchema,
        tags=["Members"],
    )(MemberController.get_member)
    api.patch(
        "organizations/{org_id}/members/{member_id}",
        response_model=MembershipSchema,
        tags=["Members"],
    )(MemberController.update_member)
    api.delete("organizations/{org_id}/members/{member_id}", tags=["Members"])(
        MemberController.remove_member
    )
    api.post("organizations/{org_id}/leave", tags=["Members"])(MemberController.leave_organization)
    api.post(
        "organizations/{org_id}/transfer-ownership/{member_id}",
        response_model=MembershipSchema,
        tags=["Members"],
    )(MemberController.transfer_ownership)

    # Invitations
    api.get(
        "organizations/{org_id}/invitations",
        response_model=list[InvitationSchema],
        tags=["Invitations"],
    )(InvitationController.list_invitations)
    api.post(
        "organizations/{org_id}/invitations", response_model=InvitationSchema, tags=["Invitations"]
    )(InvitationController.create_invitation)
    api.post(
        "organizations/{org_id}/invitations/bulk",
        response_model=BulkInviteResultSchema,
        tags=["Invitations"],
    )(InvitationController.bulk_invite)
    api.delete("organizations/{org_id}/invitations/{invitation_id}", tags=["Invitations"])(
        InvitationController.cancel_invitation
    )
    api.post(
        "organizations/{org_id}/invitations/{invitation_id}/resend",
        response_model=InvitationSchema,
        tags=["Invitations"],
    )(InvitationController.resend_invitation)

    # User invitations
    api.get("invitations", response_model=list[InvitationSchema], tags=["Invitations"])(
        InvitationController.get_my_invitations
    )
    api.post("invitations/{token}/accept", response_model=MembershipSchema, tags=["Invitations"])(
        InvitationController.accept_invitation
    )
    api.post("invitations/{token}/decline", tags=["Invitations"])(
        InvitationController.decline_invitation
    )
