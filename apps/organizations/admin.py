"""Admin configuration for organizations."""

from django.contrib import admin

from .models import Invitation, Membership, Organization, Team


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Organization admin."""

    list_display = ("name", "slug", "plan", "member_count", "team_count", "created_at")
    list_filter = ("plan", "created_at")
    search_fields = ("name", "slug")
    readonly_fields = ("id", "member_count", "team_count", "created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("id", "name", "slug", "description")}),
        ("Branding", {"fields": ("logo_url", "website")}),
        ("Billing", {"fields": ("stripe_customer_id", "plan")}),
        ("Settings", {"fields": ("settings",)}),
        (
            "Metadata",
            {
                "fields": ("member_count", "team_count", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def member_count(self, obj):
        """Display member count."""
        return obj.member_count

    member_count.short_description = "Members"

    def team_count(self, obj):
        """Display team count."""
        return obj.team_count

    team_count.short_description = "Teams"


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Team admin."""

    list_display = ("name", "organization", "slug", "member_count", "created_at")
    list_filter = ("organization", "created_at")
    search_fields = ("name", "slug", "organization__name")
    readonly_fields = ("id", "member_count", "created_at", "updated_at")
    ordering = ("organization", "name")

    fieldsets = (
        (None, {"fields": ("id", "organization", "name", "slug", "description")}),
        ("Settings", {"fields": ("settings",)}),
        (
            "Metadata",
            {
                "fields": ("member_count", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def member_count(self, obj):
        """Display member count."""
        return obj.member_count

    member_count.short_description = "Members"


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """Membership admin."""

    list_display = ("user", "organization", "role", "is_active", "created_at")
    list_filter = ("role", "is_active", "organization")
    search_fields = ("user__email", "organization__name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("user", "organization")
    filter_horizontal = ("teams",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("id", "user", "organization", "role", "is_active")}),
        ("Teams", {"fields": ("teams",)}),
        ("Details", {"fields": ("job_title", "department")}),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    """Invitation admin."""

    list_display = ("email", "organization", "role", "status", "expires_at", "created_at")
    list_filter = ("status", "role", "organization")
    search_fields = ("email", "organization__name")
    readonly_fields = ("id", "token", "created_at")
    raw_id_fields = ("organization", "invited_by")
    filter_horizontal = ("teams",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("id", "organization", "email", "role", "status")}),
        ("Details", {"fields": ("message", "teams")}),
        ("Inviter", {"fields": ("invited_by",)}),
        ("Token & Expiry", {"fields": ("token", "expires_at")}),
        (
            "Metadata",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["revoke_invitations", "resend_invitations"]

    @admin.action(description="Revoke selected invitations")
    def revoke_invitations(self, request, queryset):
        """Revoke selected invitations."""
        count = queryset.filter(status="pending").update(status="revoked")
        self.message_user(request, f"Revoked {count} invitation(s).")

    @admin.action(description="Resend selected invitations")
    def resend_invitations(self, request, queryset):
        """Resend selected invitations (extend expiry)."""
        from datetime import timedelta

        from django.conf import settings
        from django.utils import timezone

        expiry_days = getattr(settings, "INVITATION_EXPIRY_DAYS", 7)
        count = 0
        for invitation in queryset.filter(status="pending"):
            invitation.expires_at = timezone.now() + timedelta(days=expiry_days)
            invitation.save()
            count += 1
            # TODO: Send email

        self.message_user(request, f"Resent {count} invitation(s).")
