"""Membership Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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
