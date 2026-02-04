"""Invitation Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


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
