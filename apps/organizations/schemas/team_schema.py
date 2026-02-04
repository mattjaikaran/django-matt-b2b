"""Team Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .membership_schema import MembershipSchema


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

    members: list[MembershipSchema] = []


# Update forward references
TeamDetailSchema.model_rebuild()
