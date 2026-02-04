"""Pydantic schemas for organization endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# =============================================================================
# Organization schemas
# =============================================================================


class OrganizationSchema(BaseModel):
    """Organization response schema."""

    id: UUID
    name: str
    slug: str
    description: str = ""
    logo_url: str | None = None
    website: str | None = None
    plan: str
    member_count: int = 0
    team_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationCreateSchema(BaseModel):
    """Create organization schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str = ""
    logo_url: str | None = None
    website: str | None = None


class OrganizationUpdateSchema(BaseModel):
    """Update organization schema."""

    name: str | None = None
    description: str | None = None
    logo_url: str | None = None
    website: str | None = None


class OrganizationWithRoleSchema(BaseModel):
    """Organization with user's role."""

    id: UUID
    name: str
    slug: str
    description: str = ""
    logo_url: str | None = None
    plan: str
    role: str  # User's role in this org
    is_active: bool
    member_count: int = 0
    team_count: int = 0

    class Config:
        from_attributes = True


# =============================================================================
# Team schemas
# =============================================================================


class TeamSchema(BaseModel):
    """Team response schema."""

    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str
    member_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class TeamCreateSchema(BaseModel):
    """Create team schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str = ""


class TeamUpdateSchema(BaseModel):
    """Update team schema."""

    name: str | None = None
    description: str | None = None


class TeamDetailSchema(TeamSchema):
    """Team with member details."""

    members: list["MembershipSchema"] = []


# =============================================================================
# Membership schemas
# =============================================================================


class MembershipSchema(BaseModel):
    """Membership response schema."""

    id: UUID
    user_id: int
    user_email: str
    user_name: str = ""
    organization_id: UUID
    organization_name: str
    role: str
    job_title: str = ""
    department: str = ""
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MembershipCreateSchema(BaseModel):
    """Create membership (internal use)."""

    user_id: int
    organization_id: UUID
    role: str = "member"


class MembershipUpdateSchema(BaseModel):
    """Update membership schema."""

    role: str | None = None
    job_title: str | None = None
    department: str | None = None
    is_active: bool | None = None


class TeamMemberAddSchema(BaseModel):
    """Add member to team schema."""

    member_id: UUID


class TeamMemberRemoveSchema(BaseModel):
    """Remove member from team schema."""

    member_id: UUID


# =============================================================================
# Invitation schemas
# =============================================================================


class InvitationSchema(BaseModel):
    """Invitation response schema."""

    id: UUID
    organization_id: UUID
    organization_name: str
    email: EmailStr
    role: str
    status: str
    message: str = ""
    invited_by_email: str | None
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationCreateSchema(BaseModel):
    """Create invitation schema."""

    email: EmailStr
    role: str = "member"
    message: str = ""
    team_ids: list[UUID] = []


class InvitationAcceptSchema(BaseModel):
    """Accept invitation schema."""

    token: str


class BulkInviteSchema(BaseModel):
    """Bulk invite schema."""

    emails: list[EmailStr] = Field(..., min_length=1, max_length=50)
    role: str = "member"
    message: str = ""


class BulkInviteResultSchema(BaseModel):
    """Bulk invite result schema."""

    sent: int
    failed: int
    errors: list[str] = []


# =============================================================================
# Settings schemas
# =============================================================================


class OrganizationSettingsSchema(BaseModel):
    """Organization settings schema."""

    allow_member_invites: bool = False
    default_member_role: str = "member"
    require_2fa: bool = False
    allowed_email_domains: list[str] = []

    class Config:
        from_attributes = True


class OrganizationSettingsUpdateSchema(BaseModel):
    """Update organization settings schema."""

    allow_member_invites: bool | None = None
    default_member_role: str | None = None
    require_2fa: bool | None = None
    allowed_email_domains: list[str] | None = None


# Update forward references
TeamDetailSchema.model_rebuild()
