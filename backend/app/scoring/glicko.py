"""Glicko-1 skill rating (Glickman 1999), one observation at a time.

The seeker has rating mu and rating deviation RD. An employer rating is one
game against a role benchmark (mu_opp, rd_opp). Decisions stay in this module.
"""

from __future__ import annotations

import math

Q = math.log(10) / 400.0
RD_MAX_DEFAULT = 350.0
C_DEFAULT = 30.0


def g(rd: float) -> float:
    return 1.0 / math.sqrt(1.0 + 3.0 * Q * Q * rd * rd / (math.pi**2))


def expected_score(mu: float, mu_opp: float, rd_opp: float) -> float:
    return 1.0 / (1.0 + 10 ** (-g(rd_opp) * (mu - mu_opp) / 400.0))


def inflate_rd(rd: float, weeks: int, c: float = C_DEFAULT, rd_max: float = RD_MAX_DEFAULT) -> float:
    """RD grows with idle weeks, then saturates. weeks <= 0 leaves RD unchanged."""
    if weeks <= 0:
        return min(rd, rd_max)
    grown = math.sqrt(rd * rd + (c * c) * weeks)
    return min(grown, rd_max)


def update(
    mu: float,
    rd: float,
    mu_opp: float,
    rd_opp: float,
    score: float,
) -> tuple[float, float]:
    """Apply one Glicko-1 update.

    score is in [0, 1]. Returns (mu, rd). RD passed in should already include
    any inactivity inflation the caller wants applied.
    """
    score = min(1.0, max(0.0, score))
    expect = expected_score(mu, mu_opp, rd_opp)
    # Keep the variance term defined if a rating collapses to 0 or 1.
    expect = min(1 - 1e-6, max(1e-6, expect))
    gg = g(rd_opp)
    d_squared = 1.0 / (Q * Q * gg * gg * expect * (1.0 - expect))
    precision = (1.0 / (rd * rd)) + (1.0 / d_squared)
    mu_new = mu + (Q / precision) * gg * (score - expect)
    rd_new = math.sqrt(1.0 / precision)
    return mu_new, rd_new


def rating_to_score(stars: int) -> float:
    """Map a 1–5 checkpoint rating onto the Glicko score s."""
    table = {1: 0.0, 2: 0.25, 3: 0.5, 4: 0.75, 5: 1.0}
    return table[max(1, min(5, int(stars)))]


def role_benchmark(min_level: int) -> tuple[float, float]:
    """Opponent rating for a job whose hardest required skill is min_level (1–5)."""
    level = max(1, min(5, int(min_level)))
    return 1400.0 + level * 80.0, 70.0


def skill_index(mu: float) -> float:
    """Display index 0–100. 1500 → 50, 1800 → 100, 1200 → 0."""
    return round(max(0.0, min(100.0, (mu - 1200.0) / 6.0)), 1)


def skill_band(mu: float, rd: float) -> str:
    """Conservative band uses mu − RD so a noisy high rating stays Building or Medium."""
    conservative = mu - rd
    if conservative >= 1550:
        return "High"
    if conservative >= 1400:
        return "Medium"
    return "Building"
