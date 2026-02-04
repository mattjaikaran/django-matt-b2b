"""Organization Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
