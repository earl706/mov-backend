from django.db import models

from apps.common.models import OwnedModel


class Notification(OwnedModel):
    LEVEL = [
        ("info", "Info"),
        ("success", "Success"),
        ("warning", "Warning"),
        ("insight", "Insight"),  # AI-surfaced suggestions
    ]

    level = models.CharField(max_length=16, choices=LEVEL, default="info")
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    # Optional deep link the UI can route to, e.g. "/tasks/42".
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta(OwnedModel.Meta):
        indexes = [models.Index(fields=["owner", "is_read"])]

    def __str__(self):
        return self.title


def notify(user, title, body="", level="info", link=""):
    """Helper used across the codebase to create a notification."""
    return Notification.objects.create(
        owner=user, title=title, body=body, level=level, link=link
    )
