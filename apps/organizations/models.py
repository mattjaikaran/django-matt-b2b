"""Organization and team models for B2B multi-tenancy."""

import uuid

from django.conf import settings
from django.db import models


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

    def get_owners(self):
        """Get all owners of this organization."""
        return self.memberships.filter(role=MembershipRole.OWNER, is_active=True)

    def get_admins(self):
        """Get all admins (including owners) of this organization."""
        return self.memberships.filter(
            role__in=[MembershipRole.OWNER, MembershipRole.ADMIN], is_active=True
        )


class Team(models.Model):
    """Team within an organization."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="teams"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)

    # Team settings
    settings = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "teams"
        unique_together = ["organization", "slug"]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.organization.name} / {self.name}"

    @property
    def member_count(self) -> int:
        """Get total member count in this team."""
        return self.members.filter(is_active=True).count()


class MembershipRole(models.TextChoices):
    """Membership roles."""

    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class Membership(models.Model):
    """User membership in an organization."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        max_length=20, choices=MembershipRole.choices, default=MembershipRole.MEMBER
    )

    # Team assignments (optional)
    teams = models.ManyToManyField(Team, blank=True, related_name="members")

    # Status
    is_active = models.BooleanField(default=True)

    # Metadata
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "memberships"
        unique_together = ["user", "organization"]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.organization.name} ({self.role})"

    @property
    def is_owner(self) -> bool:
        return self.role == MembershipRole.OWNER

    @property
    def is_admin(self) -> bool:
        return self.role in [MembershipRole.OWNER, MembershipRole.ADMIN]

    @property
    def can_manage_members(self) -> bool:
        """Check if this member can manage other members."""
        return self.is_admin

    @property
    def can_manage_teams(self) -> bool:
        """Check if this member can manage teams."""
        return self.is_admin

    @property
    def can_manage_settings(self) -> bool:
        """Check if this member can manage org settings."""
        return self.is_admin

    @property
    def can_delete_organization(self) -> bool:
        """Check if this member can delete the organization."""
        return self.is_owner


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
