from datetime import date, timedelta


_DECAY = 0.9

def compute_momentum(log_dates, cadence="daily", target_per_period=1, today=None, window=30):

    today = today or date.today()
    completed = {d for d in log_dates if d <= today}

    if cadence == "weekly":
        return _weekly_momentum(completed, target_per_period, today, window)


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

    streak = 0
    day = today

    if day not in completed:
        day -= timedelta(days=1)
    while day in completed:
        streak += 1
        day -= timedelta(days=1)
    return streak
