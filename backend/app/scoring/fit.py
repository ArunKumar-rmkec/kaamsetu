"""Relevance components. All outputs are in [0, 1] except where noted.

Weights for the relevance blend live in RELEVANCE_WEIGHTS and are the single
place the product mix is defined.
"""

from __future__ import annotations

RELEVANCE_WEIGHTS = {
    "skill": 0.40,
    "env": 0.25,
    "pay": 0.20,
    "reliability": 0.15,
}


def skill_fit(seeker_skills: dict[str, int], job_skills: list[dict]) -> float:
    """Level-aware overlap. Required skills weigh twice optional skills.

    Missing a required skill contributes 0. Missing an optional skill contributes 0.25.
    A held skill contributes min(1, seeker_level / asked_level).
    """
    if not job_skills:
        return 0.5
    numerator = 0.0
    denominator = 0.0
    for item in job_skills:
        weight = 2.0 if item.get("required", True) else 1.0
        denominator += weight
        have = seeker_skills.get(item["code"])
        if have is None:
            numerator += weight * (0.0 if item.get("required", True) else 0.25)
        else:
            asked = max(int(item.get("min_level", 1)), 1)
            numerator += weight * min(1.0, have / asked)
    return numerator / denominator


def env_fit(seeker: dict, job: dict, distance_km: float) -> float:
    """Mean of seven work-environment dimensions. Hard filters are applied earlier."""
    parts = [
        _shift(seeker.get("shift", "day"), job.get("shift", "day")),
        _physical(int(seeker.get("physical", 3)), int(job.get("physical", 3))),
        _setting(seeker.get("setting", "either"), job.get("setting", "either")),
        _lodging(bool(seeker.get("lodging_needed")), bool(job.get("lodging_provided"))),
        _commute(distance_km, float(seeker.get("max_commute_km", 20)), bool(job.get("lodging_provided"))),
        _choice(seeker.get("supervision", "either"), job.get("supervision", "either"), mismatch=0.55),
        _choice(seeker.get("team_size", "any"), job.get("team_size", "any"), mismatch=0.65),
    ]
    return sum(parts) / len(parts)


def pay_fit(
    expected_wage: float,
    salary_min: float,
    salary_max: float,
    negotiation_low: float,
    negotiation_high: float,
    hike_pct: float,
    perks_present: bool,
) -> float:
    """1 when the midpoint offer meets the expected wage.

    A negotiation band that reaches the expected wage adds 0.15, capped at 1
    together with a small hike and perks bump.
    """
    offered = (salary_min + salary_max) / 2.0
    if expected_wage <= 0:
        base = 0.7
    elif offered >= expected_wage:
        base = 1.0
    else:
        base = max(0.0, offered / expected_wage)
        if negotiation_high >= expected_wage >= negotiation_low:
            base += 0.15
        elif negotiation_high >= expected_wage:
            base += 0.10
    perk = 0.03 if perks_present else 0.0
    hike = min(0.05, max(0.0, hike_pct) / 100.0 * 0.5)
    return min(1.0, base + perk + hike)


def reliability(rd: float, checkin_streak: int, assessment_done: bool) -> float:
    """How much history we can lean on. A new seeker with RD 350 scores low here.

    The fairness layer's uncertainty bonus is what keeps that from becoming a ban.
    """
    uncertainty = 1.0 - min(max(rd, 0.0), 350.0) / 350.0
    streak = min(max(checkin_streak, 0), 10) / 10.0
    assessed = 1.0 if assessment_done else 0.0
    return 0.45 * uncertainty + 0.35 * streak + 0.20 * assessed


def relevance(skill: float, env: float, pay: float, rel: float) -> float:
    w = RELEVANCE_WEIGHTS
    return w["skill"] * skill + w["env"] * env + w["pay"] * pay + w["reliability"] * rel


def passes_hard_filters(seeker: dict, job: dict, distance_km: float, sectors_overlap: bool) -> tuple[bool, str]:
    """Return (allowed, reason_code).

    Hard filters are geography, consent, night shift, commute without lodging,
    closed or flagged supply, and unverified employers. Soft preferences stay in env_fit.
    """
    if not seeker.get("consent", False):
        return False, "no_consent"
    if not seeker.get("onboarding_complete", True):
        return False, "onboarding_incomplete"
    if not sectors_overlap:
        return False, "outside_sector"
    if job.get("night_required") and not seeker.get("night_ok"):
        return False, "night_blocked"
    if not job.get("lodging_provided") and distance_km > float(seeker.get("max_commute_km", 20)):
        return False, "commute_blocked"
    if job.get("verification_status") != "passed":
        return False, "listing_not_cleared"
    if job.get("status") != "open":
        return False, "job_closed"
    if int(job.get("openings", 1)) - int(job.get("filled", 0)) <= 0:
        return False, "no_openings"
    if not job.get("employer_verified", True):
        return False, "employer_unverified"
    return True, "ok"


def _shift(seeker_shift: str, job_shift: str) -> float:
    if seeker_shift == job_shift or "any" in (seeker_shift, job_shift):
        return 1.0
    if "rotating" in (seeker_shift, job_shift):
        return 0.6
    return 0.25


def _physical(seeker_level: int, job_level: int) -> float:
    return max(0.0, 1.0 - abs(seeker_level - job_level) / 4.0)


def _setting(seeker_setting: str, job_setting: str) -> float:
    if seeker_setting == job_setting:
        return 1.0
    if "either" in (seeker_setting, job_setting):
        return 0.9
    return 0.35


def _lodging(needed: bool, provided: bool) -> float:
    if needed and not provided:
        return 0.25
    return 1.0


def _commute(distance_km: float, max_km: float, lodging: bool) -> float:
    if lodging:
        return 1.0
    if max_km <= 0:
        return 0.5
    ratio = distance_km / max_km
    return max(0.5, 1.0 - 0.5 * ratio)


def _choice(seeker_value: str, job_value: str, mismatch: float) -> float:
    if seeker_value == job_value or seeker_value in ("any", "either") or job_value in ("any", "either"):
        return 1.0
    return mismatch
