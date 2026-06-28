"""Momentum scoring for habits.

Traditional streak counters punish a single missed day by resetting to zero,
which is demotivating and a poor model of real consistency. Mov instead computes
a *momentum* score: an exponentially-weighted measure of recent adherence that
dips gently on a miss and recovers quickly when you resume.

Returns a value in 0..100 plus a human-friendly "current streak" (counted, but
not used punitively in the score).
"""
from datetime import date, timedelta

# How quickly old days lose influence. ~14-day effective memory.
_DECAY = 0.9


def compute_momentum(log_dates, cadence="daily", target_per_period=1, today=None, window=30):
    """log_dates: iterable of date objects on which the habit was completed."""
    today = today or date.today()
    completed = {d for d in log_dates if d <= today}

    if cadence == "weekly":
        return _weekly_momentum(completed, target_per_period, today, window)

    # Daily: weight each of the last `window` days by recency; expected 1/day.
    weighted_hits = 0.0
    weighted_total = 0.0
    weight = 1.0
    for offset in range(window):
        day = today - timedelta(days=offset)
        weighted_total += weight
        if day in completed:
            weighted_hits += weight
        weight *= _DECAY

    momentum = round(100 * weighted_hits / weighted_total, 1) if weighted_total else 0.0

    return {
        "momentum": momentum,
        "current_streak": _current_streak(completed, today),
        "completions_30d": len([d for d in completed if (today - d).days < 30]),
    }


def _weekly_momentum(completed, target, today, window):
    weeks = max(1, window // 7)
    weighted_hits = 0.0
    weighted_total = 0.0
    weight = 1.0
    for w in range(weeks):
        week_end = today - timedelta(days=7 * w)
        week_start = week_end - timedelta(days=6)
        hits = sum(1 for d in completed if week_start <= d <= week_end)
        # Fraction of the weekly target met (capped at 1).
        weighted_hits += weight * min(1.0, hits / max(1, target))
        weighted_total += weight
        weight *= _DECAY
    momentum = round(100 * weighted_hits / weighted_total, 1) if weighted_total else 0.0
    return {
        "momentum": momentum,
        "current_streak": _current_streak(completed, today),
        "completions_30d": len([d for d in completed if (today - d).days < 30]),
    }


def _current_streak(completed, today):
    """Consecutive days up to today (or yesterday) with a completion."""
    streak = 0
    day = today
    # Allow today to be incomplete without breaking the streak yet.
    if day not in completed:
        day -= timedelta(days=1)
    while day in completed:
        streak += 1
        day -= timedelta(days=1)
    return streak
