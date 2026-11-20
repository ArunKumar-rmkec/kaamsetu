"""Fairness metrics for the live district snapshot and the 4-week simulation."""

from __future__ import annotations


def gini(values: list[float]) -> float:
    """Gini coefficient in [0, 1]. Zero means every seeker had the same exposure."""
    if not values:
        return 0.0
    ordered = sorted(max(0.0, float(value)) for value in values)
    total = sum(ordered)
    if total <= 0:
        return 0.0
    weighted = sum(index * value for index, value in enumerate(ordered, start=1))
    n = len(ordered)
    return (2 * weighted) / (n * total) - (n + 1) / n


def summarise_exposure(exposure: dict[str, int]) -> dict:
    values = [float(exposure.get(key, 0)) for key in exposure]
    n = len(values) or 1
    zeros = sum(1 for value in values if value <= 0)
    covered = sum(1 for value in values if value >= 1)
    ordered = sorted(values)
    p10 = ordered[max(0, int(0.10 * (len(ordered) - 1)))] if ordered else 0
    p90 = ordered[max(0, int(0.90 * (len(ordered) - 1)))] if ordered else 0
    return {
        "gini": round(gini(values), 4),
        "share_with_zero_exposure": round(zeros / n, 4),
        "share_with_at_least_one": round(covered / n, 4),
        "mean_exposure": round(sum(values) / n, 3),
        "p90_over_p10": round(p90 / p10, 3) if p10 > 0 else None,
    }
