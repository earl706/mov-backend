"""Project health metrics.

Project health is intentionally a *derived* read model computed from the
project's tasks, not stored state. This keeps it always-consistent and lets us
evolve the formula without migrations. The four facets:

- progress:    share of tasks completed (0..100)
- momentum:    recent completion velocity vs. the prior window (0..100)
- confidence:  likelihood of hitting the due date given remaining work + velocity
- eta_days:    naive estimated days to completion at the current velocity
"""
from datetime import timedelta

from django.utils import timezone


def _completion_velocity(tasks, days):
    """Tasks completed within the last `days` days."""
    cutoff = timezone.now() - timedelta(days=days)
    return sum(1 for t in tasks if t.completed_at and t.completed_at >= cutoff)


def compute_project_health(project, tasks=None):
    tasks = list(tasks if tasks is not None else project.tasks.all())
    total = len(tasks)
    if total == 0:
        return {
            "progress": 0.0,
            "momentum": 50.0,
            "confidence": 50.0,
            "eta_days": None,
            "open_tasks": 0,
            "total_tasks": 0,
        }

    done = [t for t in tasks if t.status == "done"]
    progress = round(100 * len(done) / total, 1)

    # Momentum: compare last 7 days of completions to the previous 7 days.
    recent = _completion_velocity(done, 7)
    previous = _completion_velocity(done, 14) - recent
    if recent + previous == 0:
        momentum = 50.0
    else:
        # Map ratio of recent vs. previous into 0..100 with 50 = steady.
        ratio = recent / max(previous, 0.5)
        momentum = round(min(100.0, 50.0 * ratio), 1)

    open_tasks = total - len(done)
    weekly_rate = recent or 0.0001  # avoid div by zero
    eta_days = round((open_tasks / weekly_rate) * 7, 1) if open_tasks else 0.0

    # Confidence blends progress and momentum, penalised if the ETA overshoots
    # the due date.
    confidence = 0.5 * progress + 0.5 * momentum
    if project.due_date and open_tasks:
        days_left = (project.due_date - timezone.now().date()).days
        if days_left <= 0:
            confidence *= 0.5
        elif eta_days > days_left:
            confidence *= max(0.4, days_left / eta_days)
    confidence = round(min(100.0, max(0.0, confidence)), 1)

    return {
        "progress": progress,
        "momentum": momentum,
        "confidence": confidence,
        "eta_days": eta_days,
        "open_tasks": open_tasks,
        "total_tasks": total,
    }
