"""Shared abstract models used across the platform."""
import uuid

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Adds created/updated timestamps and a stable UUID public identifier.

    Using a UUID alongside the integer PK lets the frontend and knowledge graph
    reference entities with an opaque, non-enumerable id while keeping efficient
    integer joins internally.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class OwnedModel(TimeStampedModel):
    """A timestamped model that belongs to a single user (the owner)."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta(TimeStampedModel.Meta):
        abstract = True
