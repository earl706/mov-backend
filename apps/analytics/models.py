from django.db import models

from apps.common.models import OwnedModel


class Retrospective(OwnedModel):
    """A weekly AI-generated productivity retrospective.

    Stored so the user can browse history and so generation can run async via
    Celery. `metrics` is the behavioural snapshot used to write the narrative.
    """

    week_start = models.DateField()
    headline = models.CharField(max_length=255)
    summary = models.TextField()
    highlights = models.JSONField(default=list)
    suggestions = models.JSONField(default=list)
    metrics = models.JSONField(default=dict)

    class Meta(OwnedModel.Meta):
        unique_together = [("owner", "week_start")]
        ordering = ["-week_start"]

    def __str__(self):
        return f"Retro {self.week_start} for {self.owner_id}"
