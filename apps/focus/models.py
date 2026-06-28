from django.db import models

from apps.common.models import OwnedModel
from apps.tasks.models import Task


class FocusSession(OwnedModel):
    """A timed deep-work session.

    `interruptions` records context switches during the session and feeds the
    behavioural-intelligence "context switching" metric. `quality` is the user's
    self-rated focus (1..5).
    """

    task = models.ForeignKey(
        Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="focus_sessions"
    )
    label = models.CharField(max_length=200, blank=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    planned_minutes = models.PositiveIntegerField(default=25)
    actual_minutes = models.PositiveIntegerField(default=0)
    interruptions = models.PositiveSmallIntegerField(default=0)
    quality = models.PositiveSmallIntegerField(default=3)  # 1..5
    notes = models.TextField(blank=True)

    class Meta(OwnedModel.Meta):
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["owner", "started_at"])]

    def __str__(self):
        return self.label or f"Focus {self.started_at:%Y-%m-%d %H:%M}"


class WorkContextSnapshot(OwnedModel):
    """Captures the user's active working set so a session can be recovered after
    an interruption (smart session recovery).

    The payload is a denormalized list of {type, id, title} references rather
    than hard FKs, so a snapshot survives even if an underlying item is later
    deleted.
    """

    label = models.CharField(max_length=200, blank=True)
    items = models.JSONField(default=list)  # [{type, id, uuid, title}]
    active_task = models.ForeignKey(
        Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    def __str__(self):
        return self.label or f"Snapshot {self.created_at:%Y-%m-%d %H:%M}"
