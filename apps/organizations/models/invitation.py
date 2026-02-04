"""Invitation model for organization invites."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from .membership import MembershipRole
from .organization import Organization
from .team import Team


class InvitationStatus(models.TextChoices):
    """Invitation status."""

    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"


class Invitation(models.Model):
    """Invitation to join an organization."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=20, choices=MembershipRole.choices, default=MembershipRole.MEMBER
    )
    status = models.CharField(
        max_length=20, choices=InvitationStatus.choices, default=InvitationStatus.PENDING
    )

    # Inviter
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )

    # Token for accepting invitation
    token = models.CharField(max_length=64, unique=True)

    # Optional team assignment
    teams = models.ManyToManyField(Team, blank=True, related_name="invitations")

    # Personal message
    message = models.TextField(blank=True)

    # Expiration
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invitations"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Invitation for {self.email} to {self.organization.name}"

    @property
    def is_pending(self) -> bool:
        return self.status == InvitationStatus.PENDING

    @property
    def is_expired(self) -> bool:
        from django.utils import timezone

        if self.status == InvitationStatus.EXPIRED:
            return True
        return self.expires_at < timezone.now()

    def mark_expired(self) -> None:
        """Mark invitation as expired."""
        self.status = InvitationStatus.EXPIRED
        self.save(update_fields=["status"])

    def revoke(self) -> None:
        """Revoke the invitation."""
        self.status = InvitationStatus.REVOKED
        self.save(update_fields=["status"])
