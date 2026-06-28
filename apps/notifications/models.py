from django.db import models

from apps.common.models import OwnedModel

class Notification(OwnedModel):
    LEVEL = [
        ("info", "Info"),
        ("success", "Success"),
        ("warning", "Warning"),
        ("insight", "Insight"),
    ]

    level = models.CharField(max_length=16, choices=LEVEL, default="info")
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)

    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta(OwnedModel.Meta):
        indexes = [models.Index(fields=["owner", "is_read"])]

    def __str__(self):
        return self.title

def notify(user, title, body="", level="info", link=""):

    return Notification.objects.create(
        owner=user, title=title, body=body, level=level, link=link
    )
