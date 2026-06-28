"""Celery application for background jobs (analytics rollups, retrospectives)."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mov.settings")

app = Celery("mov")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):  # pragma: no cover - utility task
    print(f"Request: {self.request!r}")
