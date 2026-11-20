"""Consent broker. Identity stays hidden until the seeker accepts an employer's interest."""

from __future__ import annotations

from app.models import ConsentEvent, EmployerProfile, Job, Match, SeekerProfile, User


REVEALED = {"accepted", "hired"}


def record(db_add, match: Match, seeker_id: int, employer_id: int, action: str) -> None:
    db_add(
        ConsentEvent(
            match_id=match.id,
            seeker_id=seeker_id,
            employer_id=employer_id,
            action=action,
        )
    )


def employer_card(
    match: Match,
    seeker_user: User,
    seeker: SeekerProfile,
    skills: list[dict],
) -> dict:
    revealed = match.status in REVEALED
    card = {
        "match_id": match.id,
        "status": match.status,
        "revealed": revealed,
        "candidate_ref": f"KS-{seeker.user_id:04d}",
        "district_id": seeker.district_id,
        "age_band": _age_band(seeker.age),
        "education": seeker.education,
        "skills": skills,
        "skill_band": _band_label(seeker),
        "potential_band": _potential_band(seeker.potential),
        "fits": {
            "skill": match.skill_fit,
            "environment": match.env_fit,
            "pay": match.pay_fit,
            "reliability": match.reliability,
            "relevance": match.relevance,
            "final": match.final_score,
        },
        "fairness": {
            "uncertainty": match.fair_uncertainty,
            "exposure": match.fair_exposure,
            "potential": match.fair_potential,
            "first_time": match.fair_first,
        },
        "reasons": _load(match.reasons_json),
        "distance_km": match.distance_km,
    }
    if revealed:
        card["name"] = seeker_user.name
        card["phone"] = seeker_user.phone
        card["age"] = seeker.age
        card["photo"] = "placeholder"
    return card


def seeker_card(match: Match, job: Job, employer: EmployerProfile) -> dict:
    return {
        "match_id": match.id,
        "status": match.status,
        "job_id": job.id,
        "title": job.title,
        "company": employer.company_name,
        "district_id": job.district_id,
        "sector": job.sector,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "will_train": job.will_train,
        "open_to_freshers": job.open_to_freshers,
        "shift": job.shift,
        "setting": job.setting,
        "night_required": job.night_required,
        "lodging_provided": job.lodging_provided,
        "team_size": job.team_size,
        "physical": job.physical,
        "distance_km": match.distance_km,
        "fits": {
            "skill": match.skill_fit,
            "environment": match.env_fit,
            "pay": match.pay_fit,
            "reliability": match.reliability,
            "relevance": match.relevance,
            "final": match.final_score,
        },
        "reasons": _load(match.reasons_json),
        "identity_shared": match.status in REVEALED,
    }


def _age_band(age: int) -> str:
    if age < 21:
        return "18–20"
    if age < 25:
        return "21–24"
    if age < 30:
        return "25–29"
    return "30–35"


def _band_label(seeker: SeekerProfile) -> str:
    from app.scoring.glicko import skill_band

    return skill_band(seeker.skill_mu, seeker.skill_rd)


def _potential_band(level: float) -> str:
    from app.scoring.kalman import potential_band

    return potential_band(level)


def _load(raw: str) -> list:
    import json

    try:
        return json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
