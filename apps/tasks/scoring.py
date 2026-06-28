from datetime import timedelta

from django.utils import timezone

DEFAULT_WEIGHTS = {
    "importance": 1.0,
    "urgency": 1.0,
    "deadline": 1.2,
    "effort": 0.8,
    "completion_history": 0.6,
}

def _deadline_factor(due_date, now=None):

    if not due_date:
        return 0.3
    now = now or timezone.now()
    hours_left = (due_date - now).total_seconds() / 3600
    if hours_left <= 0:
        return 1.0

    return max(0.0, min(1.0, 1 - (hours_left / 336)))

def _effort_factor(estimated_minutes):

    if not estimated_minutes:
        return 0.5
    return max(0.2, min(1.0, 60 / (estimated_minutes + 30)))

def score_task(task, weights=None, completion_rate=0.5, now=None):

    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    now = now or timezone.now()

    factors = {
        "importance": (task.importance or 3) / 5,
        "urgency": (task.urgency or 3) / 5,
        "deadline": _deadline_factor(task.due_date, now),
        "effort": _effort_factor(task.estimated_minutes),
        "completion_history": max(0.0, min(1.0, completion_rate)),
    }

    weighted = sum(factors[k] * weights[k] for k in factors)
    total_weight = sum(weights[k] for k in factors)
    score = round(100 * weighted / total_weight, 1) if total_weight else 0.0

    return {
        "score": score,
        "factors": {k: round(v, 3) for k, v in factors.items()},
        "weights": weights,
    }
