"""Behavioural intelligence engine.

This module turns raw activity (tasks, focus sessions, habit logs) into the
higher-order signals that make Mov distinctive. Everything here is pure-ish
(reads the DB, returns plain dicts) so it can be called from API views, Celery
tasks and tests alike.

Signals produced:
  * focus_by_day            – minutes of deep work per day
  * context_switching       – interruptions per focus hour (lower is better)
  * procrastination_trend   – avg delay between a task's due date and completion
  * consistency             – how evenly effort is spread across days
  * burnout_risk            – 0..1 composite (long hours + low quality + late nights)
  * momentum                – rewards steady output without harsh streak resets
"""
import statistics
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from apps.focus.models import FocusSession
from apps.habits.models import Habit, HabitLog
from apps.tasks.models import Task


def _daterange(days, end=None):
    end = (end or timezone.localdate())
    return [end - timedelta(days=i) for i in range(days - 1, -1, -1)]


def focus_by_day(user, days=30):
    since = timezone.now() - timedelta(days=days)
    sessions = FocusSession.objects.filter(owner=user, started_at__gte=since)
    buckets = defaultdict(int)
    for s in sessions:
        buckets[timezone.localtime(s.started_at).date()] += s.actual_minutes
    return [
        {"date": d.isoformat(), "minutes": buckets.get(d, 0)} for d in _daterange(days)
    ]


def context_switching(user, days=30):
    """Interruptions per focused hour. A proxy for fragmented attention."""
    since = timezone.now() - timedelta(days=days)
    sessions = list(FocusSession.objects.filter(owner=user, started_at__gte=since))
    total_minutes = sum(s.actual_minutes for s in sessions)
    total_interruptions = sum(s.interruptions for s in sessions)
    hours = max(total_minutes / 60, 0.0001)
    return {
        "interruptions_per_hour": round(total_interruptions / hours, 2),
        "total_interruptions": total_interruptions,
        "focus_hours": round(hours, 1),
    }


def procrastination_trend(user, days=60):
    """Average lateness (in days) of completed-with-deadline tasks, week by week.

    Positive numbers mean tasks tend to be finished after their due date.
    """
    since = timezone.now() - timedelta(days=days)
    tasks = Task.objects.filter(
        owner=user, status="done", completed_at__gte=since, due_date__isnull=False
    )
    weekly = defaultdict(list)
    for t in tasks:
        lateness = (t.completed_at - t.due_date).total_seconds() / 86400
        week = timezone.localtime(t.completed_at).date().isocalendar()
        weekly[(week[0], week[1])].append(lateness)
    trend = [
        {"week": f"{y}-W{w:02d}", "avg_lateness_days": round(statistics.mean(v), 2)}
        for (y, w), v in sorted(weekly.items())
    ]
    overall = round(statistics.mean([x for v in weekly.values() for x in v]), 2) if weekly else 0.0
    return {"overall_avg_lateness_days": overall, "by_week": trend}


def consistency_score(user, days=30):
    """How evenly effort is distributed. 100 = active every day, 0 = bursty.

    Computed as 100 * (active_days / days) discounted by the coefficient of
    variation of daily minutes — steady beats spiky.
    """
    fb = focus_by_day(user, days)
    minutes = [d["minutes"] for d in fb]
    active = [m for m in minutes if m > 0]
    if not active:
        return 0.0
    coverage = len(active) / days
    mean = statistics.mean(active)
    stdev = statistics.pstdev(active) if len(active) > 1 else 0
    cv = (stdev / mean) if mean else 0
    score = 100 * coverage * (1 / (1 + cv))
    return round(min(100.0, score), 1)


def momentum_score(user, days=21):
    """Recency-weighted output: completed tasks + focus blocks.

    Unlike a streak, a single quiet day nudges momentum down a little rather than
    erasing it, and a couple of productive days restore it quickly.
    """
    today = timezone.localdate()
    decay = 0.88
    score = 0.0
    norm = 0.0
    completed = defaultdict(int)
    for t in Task.objects.filter(
        owner=user, status="done", completed_at__gte=timezone.now() - timedelta(days=days)
    ):
        completed[timezone.localtime(t.completed_at).date()] += 1
    focus = {d["date"]: d["minutes"] for d in focus_by_day(user, days)}

    weight = 1.0
    for offset in range(days):
        day = today - timedelta(days=offset)
        day_output = completed.get(day, 0) + (focus.get(day.isoformat(), 0) / 60)
        # Saturating per-day contribution so one heroic day can't peg the score.
        score += weight * min(day_output, 4)
        norm += weight * 4
        weight *= decay
    return round(100 * score / norm, 1) if norm else 0.0


def burnout_risk(user, days=14):
    """Composite 0..1 risk from overwork, declining focus quality and late nights."""
    since = timezone.now() - timedelta(days=days)
    sessions = list(FocusSession.objects.filter(owner=user, started_at__gte=since))
    if not sessions:
        return 0.0

    daily_minutes = defaultdict(int)
    late_night = 0
    qualities = []
    for s in sessions:
        local = timezone.localtime(s.started_at)
        daily_minutes[local.date()] += s.actual_minutes
        if local.hour >= 22 or local.hour < 5:
            late_night += 1
        qualities.append(s.quality)

    avg_daily = statistics.mean(daily_minutes.values())
    overwork = max(0.0, min(1.0, (avg_daily - 240) / 240))  # ramps up past 4h/day
    late_ratio = late_night / len(sessions)
    quality_drop = max(0.0, (3 - statistics.mean(qualities)) / 3)

    risk = 0.5 * overwork + 0.25 * late_ratio + 0.25 * quality_drop
    return round(min(1.0, risk), 2)


def behavioral_intelligence(user, days=30):
    """Bundle all behavioural signals into a single dashboard payload."""
    return {
        "range_days": days,
        "focus_by_day": focus_by_day(user, days),
        "context_switching": context_switching(user, days),
        "procrastination": procrastination_trend(user, max(days, 60)),
        "consistency": consistency_score(user, days),
        "momentum": momentum_score(user),
        "burnout_risk": burnout_risk(user),
    }


def update_profile_snapshot(user):
    """Persist the rolling momentum/consistency/burnout numbers onto the profile
    so other features (recommendations, scheduling) can read them cheaply."""
    profile = user.profile
    profile.momentum_score = momentum_score(user)
    profile.consistency_score = consistency_score(user)
    profile.burnout_risk = burnout_risk(user)
    profile.save(update_fields=["momentum_score", "consistency_score", "burnout_risk", "updated_at"])
    return profile


# --------------------------------------------------------------------------- #
# Pattern discovery
# --------------------------------------------------------------------------- #
def discover_patterns(user, days=60):
    """Surface recurring routines, bottlenecks and productive windows.

    Heuristic rules over the activity history. Each pattern has a type, a
    human-readable message and a confidence so the UI can rank them.
    """
    patterns = []
    since = timezone.now() - timedelta(days=days)
    sessions = list(FocusSession.objects.filter(owner=user, started_at__gte=since))

    # 1. Most productive time-of-day window.
    if sessions:
        hour_minutes = defaultdict(int)
        for s in sessions:
            hour_minutes[timezone.localtime(s.started_at).hour] += s.actual_minutes
        best_hour = max(hour_minutes, key=hour_minutes.get)
        patterns.append(
            {
                "type": "productive_window",
                "message": f"You focus best around {best_hour:02d}:00 — protect that window for deep work.",
                "confidence": 0.8,
            }
        )

        # 2. Best day of the week.
        weekday_minutes = defaultdict(int)
        for s in sessions:
            weekday_minutes[timezone.localtime(s.started_at).strftime("%A")] += s.actual_minutes
        best_day = max(weekday_minutes, key=weekday_minutes.get)
        patterns.append(
            {
                "type": "productive_day",
                "message": f"{best_day} is consistently your strongest day.",
                "confidence": 0.7,
            }
        )

    # 3. Bottleneck: tasks stuck in blocked/in_progress for a long time.
    stale = Task.objects.filter(
        owner=user, status__in=["in_progress", "blocked"], updated_at__lte=timezone.now() - timedelta(days=7)
    ).count()
    if stale:
        patterns.append(
            {
                "type": "bottleneck",
                "message": f"{stale} task(s) have been in progress or blocked for over a week. Consider breaking them down.",
                "confidence": 0.9,
            }
        )

    # 4. Habit consistency callout.
    strong = []
    for habit in Habit.objects.filter(owner=user, is_active=True):
        recent = HabitLog.objects.filter(
            habit=habit, date__gte=timezone.localdate() - timedelta(days=14)
        ).count()
        if recent >= 10:
            strong.append(habit.name)
    if strong:
        patterns.append(
            {
                "type": "habit_streak",
                "message": f"Strong consistency on: {', '.join(strong[:3])}. Keep the momentum!",
                "confidence": 0.75,
            }
        )

    return patterns


# --------------------------------------------------------------------------- #
# Predictive scheduling
# --------------------------------------------------------------------------- #
def predictive_schedule(user, horizon_days=7):
    """Project which upcoming tasks are likely to be completed on time.

    For each open task with a due date in the horizon we estimate completion
    confidence from: remaining effort vs. the user's recent daily capacity, the
    user's historical completion rate, and their current momentum.
    """
    from apps.tasks.views import user_completion_rate  # local import avoids cycle

    now = timezone.now()
    horizon = now + timedelta(days=horizon_days)
    tasks = Task.objects.filter(
        owner=user, due_date__gte=now, due_date__lte=horizon
    ).exclude(status="done").order_by("due_date")

    # Recent daily focus capacity (minutes).
    fb = focus_by_day(user, 14)
    daily_capacity = max(30, statistics.mean([d["minutes"] for d in fb]) if fb else 60)
    completion_rate = user_completion_rate(user)
    momentum = momentum_score(user) / 100

    predictions = []
    cumulative_minutes = 0
    for t in tasks:
        cumulative_minutes += t.estimated_minutes
        days_until_due = max(0.5, (t.due_date - now).total_seconds() / 86400)
        available_minutes = daily_capacity * days_until_due
        capacity_ratio = min(1.5, available_minutes / max(cumulative_minutes, 1))
        confidence = 0.5 * min(1.0, capacity_ratio) + 0.3 * completion_rate + 0.2 * momentum
        predictions.append(
            {
                "task_id": t.id,
                "title": t.title,
                "due_date": t.due_date,
                "estimated_minutes": t.estimated_minutes,
                "confidence": round(min(0.99, max(0.05, confidence)), 2),
            }
        )
    return {
        "horizon_days": horizon_days,
        "daily_capacity_minutes": round(daily_capacity),
        "predictions": predictions,
    }


# --------------------------------------------------------------------------- #
# Timeline replay
# --------------------------------------------------------------------------- #
def timeline_activity(user, days=180):
    """Per-day activity intensity for the timeline replay view.

    Combines completed tasks, focus minutes and habit check-ins into a single
    0..N intensity so the frontend can animate months of history.
    """
    today = timezone.localdate()
    completed = defaultdict(int)
    for t in Task.objects.filter(
        owner=user, status="done", completed_at__gte=timezone.now() - timedelta(days=days)
    ):
        completed[timezone.localtime(t.completed_at).date()] += 1

    focus = {d["date"]: d["minutes"] for d in focus_by_day(user, days)}

    habit_days = defaultdict(int)
    for log in HabitLog.objects.filter(
        habit__owner=user, date__gte=today - timedelta(days=days)
    ):
        habit_days[log.date] += 1

    timeline = []
    for d in _daterange(days):
        tasks_done = completed.get(d, 0)
        minutes = focus.get(d.isoformat(), 0)
        habits = habit_days.get(d, 0)
        intensity = tasks_done + (minutes / 60) + habits
        timeline.append(
            {
                "date": d.isoformat(),
                "tasks_completed": tasks_done,
                "focus_minutes": minutes,
                "habits_logged": habits,
                "intensity": round(intensity, 2),
            }
        )
    return timeline


# --------------------------------------------------------------------------- #
# Weekly retrospective
# --------------------------------------------------------------------------- #
def _week_start(d=None):
    d = d or timezone.localdate()
    return d - timedelta(days=d.weekday())  # Monday


def build_retrospective(user, week_start=None):
    """Generate (or refresh) a weekly retrospective for the given week.

    Composes a narrative from the behavioural metrics. The prose is templated
    rather than LLM-generated to keep the prototype deterministic; the structure
    mirrors what an LLM prompt would return so it can be swapped later.
    """
    from .models import Retrospective

    week_start = week_start or _week_start()
    bi = behavioral_intelligence(user, days=7)
    focus_total = sum(d["minutes"] for d in bi["focus_by_day"])
    tasks_done = Task.objects.filter(
        owner=user,
        status="done",
        completed_at__date__gte=week_start,
        completed_at__date__lte=week_start + timedelta(days=6),
    ).count()

    highlights = [
        f"{tasks_done} tasks completed",
        f"{round(focus_total / 60, 1)}h of focused work",
        f"Momentum at {bi['momentum']}/100",
    ]

    suggestions = []
    if bi["burnout_risk"] >= 0.5:
        suggestions.append("Burnout risk is elevated — schedule a lighter day and protect sleep.")
    if bi["context_switching"]["interruptions_per_hour"] > 2:
        suggestions.append("High context switching detected — try batching similar tasks.")
    if bi["consistency"] < 40:
        suggestions.append("Work was bursty this week — small daily blocks beat marathon sessions.")
    if bi["procrastination"]["overall_avg_lateness_days"] > 1:
        suggestions.append("Tasks are finishing late — pull deadlines forward or decompose them.")
    if not suggestions:
        suggestions.append("Great balance this week. Keep doing what's working!")

    if tasks_done >= 10 and bi["momentum"] >= 60:
        headline = "A strong, productive week"
    elif bi["burnout_risk"] >= 0.5:
        headline = "Productive — but watch your energy"
    elif tasks_done == 0:
        headline = "A quiet week"
    else:
        headline = "Steady progress"

    summary = (
        f"This week you completed {tasks_done} tasks and logged "
        f"{round(focus_total / 60, 1)} hours of focus. Your momentum is "
        f"{bi['momentum']}/100 and consistency is {bi['consistency']}/100. "
        + (suggestions[0] if suggestions else "")
    )

    retro, _ = Retrospective.objects.update_or_create(
        owner=user,
        week_start=week_start,
        defaults={
            "headline": headline,
            "summary": summary,
            "highlights": highlights,
            "suggestions": suggestions,
            "metrics": {
                "tasks_done": tasks_done,
                "focus_minutes": focus_total,
                "momentum": bi["momentum"],
                "consistency": bi["consistency"],
                "burnout_risk": bi["burnout_risk"],
            },
        },
    )
    return retro
