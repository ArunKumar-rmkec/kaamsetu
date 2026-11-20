"""Fairness adjustments added on top of relevance. They never replace a hard filter.

Potential boost is zero unless the job is marked will_train. That is deliberate:
potential is a training bet, not a reason to outrank a skilled applicant for a
job that expects someone who can already do the work.
"""

from __future__ import annotations

from app.config import (
    FAIR_EXPOSURE_MAX,
    FAIR_FIRST_TIME,
    FAIR_POTENTIAL_MAX,
    FAIR_UNCERTAINTY_MAX,
)


def adjustment(
    rd: float,
    exposure: int,
    median_exposure: float,
    potential: float,
    will_train: bool,
    first_time: bool,
    uncertainty_max: float = FAIR_UNCERTAINTY_MAX,
    exposure_max: float = FAIR_EXPOSURE_MAX,
    potential_max: float = FAIR_POTENTIAL_MAX,
    first_time_bonus: float = FAIR_FIRST_TIME,
) -> dict[str, float]:
    uncertainty = uncertainty_max * min(max(rd, 0.0), 350.0) / 350.0
    if median_exposure <= 0:
        exposure_bonus = exposure_max if exposure <= 0 else 0.0
    else:
        deficit = max(0.0, (median_exposure - exposure) / median_exposure)
        exposure_bonus = exposure_max * min(1.0, deficit)
    potential_bonus = potential_max * (max(0.0, min(100.0, potential)) / 100.0) if will_train else 0.0
    first_bonus = first_time_bonus if first_time else 0.0
    total = uncertainty + exposure_bonus + potential_bonus + first_bonus
    return {
        "uncertainty": round(uncertainty, 4),
        "exposure": round(exposure_bonus, 4),
        "potential": round(potential_bonus, 4),
        "first_time": round(first_bonus, 4),
        "total": round(total, 4),
    }


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0
