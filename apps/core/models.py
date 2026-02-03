"""Base models for the application."""

import uuid

from django.db import models


class TimestampMixin(models.Model):
    """Mixin that adds created_at and updated_at fields."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    """Mixin that uses UUID as primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """Mixin for soft delete functionality."""

    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        from django.utils import timezone

        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def restore(self) -> None:
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])


class BaseModel(UUIDMixin, TimestampMixin):
    """Base model with UUID primary key and timestamps."""

    class Meta:
        abstract = True


class SoftDeleteModel(BaseModel, SoftDeleteMixin):
    """Base model with UUID, timestamps, and soft delete."""

    class Meta:
        abstract = True
