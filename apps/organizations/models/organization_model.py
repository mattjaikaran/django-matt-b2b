"""Organization model for B2B multi-tenancy."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from .membership_model import Membership


class Organization(models.Model):
    """Organization model for multi-tenancy."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # Billing
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    plan = models.CharField(max_length=50, default="free")

    # Settings (JSON field for flexible configuration)
    settings = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organizations"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    @property
    def member_count(self) -> int:
        """Get total member count."""
        return self.memberships.filter(is_active=True).count()

    @property
    def team_count(self) -> int:
        """Get total team count."""
        return self.teams.count()

    def get_owners(self) -> QuerySet[Membership]:
        """Get all owners of this organization."""
        from .membership_model import MembershipRole

        return self.memberships.filter(role=MembershipRole.OWNER, is_active=True)

    def get_admins(self) -> QuerySet[Membership]:
        """Get all admins (including owners) of this organization."""
        from .membership_model import MembershipRole

        return self.memberships.filter(
            role__in=[MembershipRole.OWNER, MembershipRole.ADMIN], is_active=True
        )
