"""Shared lookups for routes."""

from __future__ import annotations

import json

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import EmployerProfile, Job, Match, SeekerProfile, User
from app.scoring.glicko import skill_band, skill_index
from app.scoring.kalman import potential_band
from app.scoring.trust import trust_band


def db_session(db: Session = Depends(get_db)) -> Session:
    return db


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Sign in first")
    token = authorization.split(" ", 1)[1].strip()
    user = db.scalar(select(User).where(User.token == token))
    if user is None:
        raise HTTPException(status_code=401, detail="That session is not recognised")
    return user


def require_role(user: User, role: str) -> None:
    if user.role != role:
        raise HTTPException(status_code=403, detail=f"This action is for the {role} role")


def seeker_profile(db: Session, user: User) -> SeekerProfile:
    profile = db.scalar(
        select(SeekerProfile)
        .where(SeekerProfile.user_id == user.id)
        .options(selectinload(SeekerProfile.skills), selectinload(SeekerProfile.answers))
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Seeker profile not found")
    return profile


def employer_profile(db: Session, user: User) -> EmployerProfile:
    profile = db.scalar(select(EmployerProfile).where(EmployerProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    return profile


def load_json(raw: str, fallback):
    try:
        return json.loads(raw or "")
    except json.JSONDecodeError:
        return fallback


def seeker_payload(user: User, profile: SeekerProfile, reasons: dict | None = None) -> dict:
    from app.catalog import TAXONOMY_BY_CODE

    skills = []
    for item in profile.skills:
        meta = TAXONOMY_BY_CODE.get(item.code, {})
        skills.append(
            {
                "code": item.code,
                "level": item.level,
                "source": item.source,
                "title_en": meta.get("title_en", item.code),
                "title_ta": meta.get("title_ta", item.code),
            }
        )
    return {
        "user": {"id": user.id, "name": user.name, "phone": user.phone, "role": user.role},
        "profile": {
            "district_id": profile.district_id,
            "education": profile.education,
            "gender": profile.gender,
            "age": profile.age,
            "years_experience": profile.years_experience,
            "expected_wage": profile.expected_wage,
            "shift": profile.shift,
            "night_ok": profile.night_ok,
            "physical": profile.physical,
            "setting": profile.setting,
            "lodging_needed": profile.lodging_needed,
            "max_commute_km": profile.max_commute_km,
            "supervision": profile.supervision,
            "team_size": profile.team_size,
            "consent": profile.consent,
            "onboarding_complete": profile.onboarding_complete,
            "skill_mu": profile.skill_mu,
            "skill_rd": round(profile.skill_rd, 1),
            "skill_index": skill_index(profile.skill_mu),
            "skill_band": skill_band(profile.skill_mu, profile.skill_rd),
            "potential": profile.potential,
            "potential_velocity": profile.potential_velocity,
            "potential_band": potential_band(profile.potential),
            "exposure": profile.exposure,
            "hired_before": profile.hired_before,
            "checkin_streak": profile.checkin_streak,
            "checkin_total": profile.checkin_total,
            "assessment_done": profile.assessment_done,
            "badges": load_json(profile.badges_json, []),
            "reasons": reasons or {"skill": [], "potential": []},
            "photo": "placeholder",
        },
        "skills": skills,
        "answers": [
            {"question_id": item.question_id, "answer": item.answer, "rubric_score": item.rubric_score}
            for item in profile.answers
        ],
    }


def employer_payload(user: User, profile: EmployerProfile, jobs: list[Job]) -> dict:
    verification = load_json(profile.verification_json, {})
    passed = sum(1 for job in jobs if job.verification_status == "passed")
    flagged = sum(1 for job in jobs if job.verification_status == "flagged")
    from app.agents.explainer import trust_reasons

    view = {
        "verification": verification,
        "trust_score": profile.trust_score,
        "passed_listings": passed,
        "flagged_listings": flagged,
    }
    return {
        "user": {"id": user.id, "name": user.name, "phone": user.phone, "role": user.role},
        "company_name": profile.company_name,
        "district_id": profile.district_id,
        "verified": profile.verified,
        "trust_score": profile.trust_score,
        "trust_band": trust_band(profile.trust_score),
        "trust_alpha": round(profile.trust_alpha, 2),
        "trust_beta": round(profile.trust_beta, 2),
        "trust_reasons": trust_reasons(view),
        "verification": verification,
        "verification_label": "SIMULATED",
        "jobs": [job_brief(job) for job in jobs],
    }


def job_brief(job: Job) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "sector": job.sector,
        "district_id": job.district_id,
        "description": job.description,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "hike_pct": job.hike_pct,
        "perks": job.perks,
        "negotiation_low": job.negotiation_low,
        "negotiation_high": job.negotiation_high,
        "open_to_freshers": job.open_to_freshers,
        "will_train": job.will_train,
        "openings": job.openings,
        "filled": job.filled,
        "shift": job.shift,
        "night_required": job.night_required,
        "physical": job.physical,
        "setting": job.setting,
        "lodging_provided": job.lodging_provided,
        "supervision": job.supervision,
        "team_size": job.team_size,
        "video_path": job.video_path,
        "verification_status": job.verification_status,
        "verification_source": job.verification_source,
        "verification_report": load_json(job.verification_report_json, {}),
        "status": job.status,
        "skills": [
            {"code": item.code, "min_level": item.min_level, "required": item.required} for item in job.skills
        ]
        if job.skills
        else [],
    }


def owned_match(db: Session, user: User, match_id: int) -> tuple[Match, Job]:
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    job = db.scalar(select(Job).options(selectinload(Job.skills)).where(Job.id == match.job_id))
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if user.role == "seeker" and match.seeker_id != user.id:
        raise HTTPException(status_code=403, detail="That match belongs to someone else")
    if user.role == "employer" and job.employer_id != user.id:
        raise HTTPException(status_code=403, detail="That match is on another employer's job")
    return match, job
