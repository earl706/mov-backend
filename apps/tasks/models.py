from django.db import models
from django.utils import timezone

from apps.common.models import OwnedModel
from apps.projects.models import Project


class Task(OwnedModel):
    STATUS = [
        ("todo", "To do"),
        ("in_progress", "In progress"),
        ("blocked", "Blocked"),
        ("done", "Done"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS, default="todo", db_index=True)

    # Scoring inputs (1..5 scales). See apps.tasks.scoring.
    importance = models.PositiveSmallIntegerField(default=3)
    urgency = models.PositiveSmallIntegerField(default=3)
    estimated_minutes = models.PositiveIntegerField(default=30)

    due_date = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    tags = models.JSONField(default=list, blank=True)
    order = models.IntegerField(default=0)

    class Meta(OwnedModel.Meta):
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["owner", "due_date"]),
        ]

    def __str__(self):
        return self.title

    def mark_status(self, status):
        """Transition status and maintain the started/completed timestamps."""
        self.status = status
        now = timezone.now()
        if status == "in_progress" and not self.started_at:
            self.started_at = now
        if status == "done":
            self.completed_at = self.completed_at or now
        elif status != "done":
            self.completed_at = None
        self.save()

    @property
    def subtask_progress(self):
        total = self.subtasks.count()
        if not total:
            return None
        done = self.subtasks.filter(is_done=True).count()
        return round(100 * done / total, 1)


class Subtask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField(max_length=300)
    is_done = models.BooleanField(default=False)
    estimated_minutes = models.PositiveIntegerField(default=15)
    order = models.IntegerField(default=0)
    # Marks subtasks created by the AI decomposition helper for UI affordances.
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title
