"""Route registration for organization controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..schemas import (
    BulkInviteResultSchema,
    InvitationSchema,
    MembershipSchema,
    OrganizationSchema,
    OrganizationSettingsSchema,
    OrganizationWithRoleSchema,
    TeamDetailSchema,
    TeamSchema,
)
from .invitation_controller import InvitationController
from .member_controller import MemberController
from .organization_controller import OrganizationController
from .team_controller import TeamController

if TYPE_CHECKING:
    from django_matt import MattAPI


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
