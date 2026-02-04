"""Custom user model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import AbstractUser
from django.db import models

if TYPE_CHECKING:
    from django.db.models import QuerySet


class User(AbstractUser):
    """Custom user model with email as the primary identifier."""

    email = models.EmailField(unique=True)

    # Profile fields
    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # Preferences
    timezone = models.CharField(max_length=50, default="UTC")
    locale = models.CharField(max_length=10, default="en")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        """Get full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username

    def get_organizations(self) -> QuerySet:
        """Get all organizations this user belongs to."""
        from apps.organizations.models import Organization

        return Organization.objects.filter(memberships__user=self, memberships__is_active=True)
