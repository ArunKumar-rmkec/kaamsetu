"""Bayesian employer trust on a Beta posterior, with exponential decay toward the verification prior."""

from __future__ import annotations

import math


def verification_prior(
    aadhaar_ok: bool,
    gst_ok: bool,
    udyam_ok: bool,
    epfo_ok: bool,
) -> tuple[float, float]:
    """Beta(alpha, beta) prior after simulated API Setu checks.

    Base is Beta(2, 2), a mild uninformative start, then each register pulls
    alpha (pass) or beta (fail).
    """
    alpha = 2.0
    beta = 2.0
    alpha, beta = _pull(alpha, beta, aadhaar_ok, pass_weight=2.0, fail_weight=1.5)
    alpha, beta = _pull(alpha, beta, gst_ok, pass_weight=2.0, fail_weight=1.5)
    alpha, beta = _pull(alpha, beta, udyam_ok, pass_weight=1.5, fail_weight=0.8)
    alpha, beta = _pull(alpha, beta, epfo_ok, pass_weight=1.5, fail_weight=0.8)
    return alpha, beta


def apply_listing(alpha: float, beta: float, passed: bool) -> tuple[float, float]:
    if passed:
        return alpha + 0.4, beta
    return alpha, beta + 0.8


def apply_feedback(alpha: float, beta: float, stars: int) -> tuple[float, float]:
    stars = max(1, min(5, int(stars)))
    if stars >= 4:
        return alpha + 1.0, beta
    if stars <= 2:
        return alpha, beta + 1.0
    return alpha + 0.35, beta + 0.35


def decay(
    alpha: float,
    beta: float,
    alpha0: float,
    beta0: float,
    lam: float = 0.15,
) -> tuple[float, float]:
    """One week of decay: (α, β) moves toward the verification prior (α0, β0)."""
    keep = math.exp(-lam)
    return alpha0 + (alpha - alpha0) * keep, beta0 + (beta - beta0) * keep


def trust_score(alpha: float, beta: float) -> float:
    total = alpha + beta
    if total <= 0:
        return 0.0
    return round(100.0 * alpha / total, 1)


def trust_band(score: float) -> str:
    if score >= 75:
        return "High"
    if score >= 55:
        return "Medium"
    return "Building"


def _pull(alpha: float, beta: float, ok: bool, pass_weight: float, fail_weight: float) -> tuple[float, float]:
    if ok:
        return alpha + pass_weight, beta
    return alpha, beta + fail_weight
