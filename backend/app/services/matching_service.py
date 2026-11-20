"""Build scored edges from persisted seekers and jobs, then write the allocation."""

from __future__ import annotations

import json
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.agents.explainer import match_reasons
from app.catalog import DISTRICT_BY_ID, TAXONOMY_BY_CODE
from app.config import SEEKER_CAP
from app.models import Hire, Job, Match, SeekerProfile
from app.scoring.allocate import allocate
from app.scoring.fairness import adjustment, median
from app.scoring.fit import env_fit, passes_hard_filters, pay_fit, reliability, relevance, skill_fit
from app.scoring.geo import commute_km, sector_ids


PROTECTED = {"interested", "accepted", "hired", "declined"}


def run_matching(db: Session, week: int, job_id: int | None = None) -> dict:
    """Recompute `allocated` rows. In-progress matches are left untouched."""
    seekers = db.scalars(select(SeekerProfile).options(selectinload(SeekerProfile.skills))).all()
    jobs = db.scalars(select(Job).options(selectinload(Job.skills), selectinload(Job.employer))).all()
    if job_id is not None:
        jobs = [job for job in jobs if job.id == job_id]

    districts = {key: value for key, value in DISTRICT_BY_ID.items()}
    sectors = {key: sector_ids(key, districts) for key in districts}
    exposures = [seeker.exposure for seeker in seekers]
    median_exposure = median([float(value) for value in exposures])

    existing = db.scalars(select(Match)).all()
    existing_by_pair = {(item.seeker_id, item.job_id): item for item in existing}
    held_statuses = {"interested", "accepted", "hired"}
    held_by_job: Counter[int] = Counter()
    held_by_seeker: Counter[int] = Counter()
    for item in existing:
        if item.status in held_statuses:
            held_by_job[item.job_id] += 1
            held_by_seeker[item.seeker_id] += 1
    hired_now = set(db.scalars(select(Hire.seeker_id).where(Hire.active.is_(True))).all())

    scored: list[dict] = []
    edges: list[tuple[str, str, float]] = []
    openings: dict[str, int] = {}
    seeker_caps: dict[str, int] = {}

    for job in jobs:
        remaining = max(0, job.openings - held_by_job[job.id])
        openings[str(job.id)] = remaining
        employer_ok = bool(job.employer and job.employer.verified)
        for seeker in seekers:
            seeker_caps[str(seeker.user_id)] = max(0, SEEKER_CAP - held_by_seeker[seeker.user_id])
            breakdown = score_pair(
                seeker,
                job,
                districts,
                sectors,
                median_exposure,
                employer_ok,
                seats_left=remaining,
                already_hired=seeker.user_id in hired_now,
            )
            if not breakdown["allowed"]:
                continue
            pair = (seeker.user_id, job.id)
            current = existing_by_pair.get(pair)
            if current and current.status in PROTECTED:
                continue
            scored.append(breakdown)
            edges.append((str(seeker.user_id), str(job.id), breakdown["final_score"]))

    chosen = set(
        allocate(edges, openings, mode="kaamsetu", seeker_cap=SEEKER_CAP, seeker_caps=seeker_caps)
    )
    created = 0
    removed = 0
    chosen_pairs = {(int(seeker_id), int(job_id)) for seeker_id, job_id in chosen}

    scope_job_ids = {job.id for job in jobs}
    for match in existing:
        if match.job_id not in scope_job_ids:
            continue
        if match.status != "allocated":
            continue
        if (match.seeker_id, match.job_id) not in chosen_pairs:
            db.delete(match)
            removed += 1

    by_key = {(item["seeker_id"], item["job_id"]): item for item in scored}
    for seeker_id, job_id in chosen_pairs:
        current = existing_by_pair.get((seeker_id, job_id))
        payload = by_key[(seeker_id, job_id)]
        if current is None:
            db.add(_match_from(payload, week))
            seeker = next(item for item in seekers if item.user_id == seeker_id)
            seeker.exposure += 1
            created += 1
        elif current.status == "allocated":
            _apply_scores(current, payload, week)

    db.commit()
    return {
        "allocated": len(chosen_pairs),
        "created": created,
        "removed": removed,
        "feasible_edges": len(edges),
        "seekers": len(seekers),
        "jobs": len(jobs),
        "median_exposure": median_exposure,
    }


def score_pair(
    seeker: SeekerProfile,
    job: Job,
    districts: dict,
    sectors: dict[str, set[str]],
    median_exposure: float,
    employer_verified: bool,
    seats_left: int | None = None,
    already_hired: bool = False,
) -> dict:
    distance = commute_km(seeker.district_id, job.district_id, districts)
    overlap = bool(sectors[seeker.district_id] & sectors[job.district_id])
    seeker_view = _seeker_dict(seeker)
    job_view = _job_dict(job, employer_verified)
    if seats_left is not None:
        job_view["openings"] = seats_left
        job_view["filled"] = 0
    allowed, reason = passes_hard_filters(seeker_view, job_view, distance, overlap)
    seeker_skills = {item.code: item.level for item in seeker.skills}
    job_skills = [{"code": item.code, "min_level": item.min_level, "required": item.required} for item in job.skills]
    skill = skill_fit(seeker_skills, job_skills)
    env = env_fit(seeker_view, job_view, distance)
    pay = pay_fit(
        seeker.expected_wage,
        job.salary_min,
        job.salary_max,
        job.negotiation_low,
        job.negotiation_high,
        job.hike_pct,
        bool(job.perks.strip()),
    )
    rel = reliability(seeker.skill_rd, seeker.checkin_streak, seeker.assessment_done)
    rel_score = relevance(skill, env, pay, rel)
    first_time = (not seeker.hired_before) and (not already_hired)
    fair = adjustment(
        rd=seeker.skill_rd,
        exposure=seeker.exposure,
        median_exposure=median_exposure,
        potential=seeker.potential,
        will_train=job.will_train,
        first_time=first_time,
    )
    top_code, top_have, top_need = _top_skill(seeker_skills, job_skills)
    row = {
        "seeker_id": seeker.user_id,
        "job_id": job.id,
        "allowed": allowed,
        "block_reason": reason,
        "distance_km": round(distance, 1),
        "skill_fit": round(skill, 4),
        "env_fit": round(env, 4),
        "pay_fit": round(pay, 4),
        "reliability": round(rel, 4),
        "relevance": round(rel_score, 4),
        "fair_uncertainty": fair["uncertainty"],
        "fair_exposure": fair["exposure"],
        "fair_potential": fair["potential"],
        "fair_first": fair["first_time"],
        "final_score": round(rel_score + fair["total"], 4),
        "top_skill_code": top_code,
        "top_skill_name": TAXONOMY_BY_CODE.get(top_code, {}).get("title_en", ""),
        "top_skill_have": top_have,
        "top_skill_need": top_need,
    }
    row["reasons"] = match_reasons(row)
    return row


def _top_skill(seeker_skills: dict[str, int], job_skills: list[dict]) -> tuple[str, int | None, int | None]:
    if not job_skills:
        if not seeker_skills:
            return "", None, None
        code = max(seeker_skills, key=seeker_skills.get)
        return code, seeker_skills[code], None
    best = None
    for item in job_skills:
        have = seeker_skills.get(item["code"])
        rank = -1 if have is None else have
        if best is None or rank > best[0]:
            best = (rank, item["code"], have, item["min_level"])
    assert best is not None
    return best[1], best[2], best[3]


def _seeker_dict(seeker: SeekerProfile) -> dict:
    return {
        "consent": seeker.consent,
        "onboarding_complete": seeker.onboarding_complete,
        "night_ok": seeker.night_ok,
        "max_commute_km": seeker.max_commute_km,
        "shift": seeker.shift,
        "physical": seeker.physical,
        "setting": seeker.setting,
        "lodging_needed": seeker.lodging_needed,
        "supervision": seeker.supervision,
        "team_size": seeker.team_size,
    }


def _job_dict(job: Job, employer_verified: bool) -> dict:
    return {
        "night_required": job.night_required,
        "lodging_provided": job.lodging_provided,
        "verification_status": job.verification_status,
        "status": job.status,
        "openings": job.openings,
        "filled": job.filled,
        "employer_verified": employer_verified,
        "shift": job.shift,
        "physical": job.physical,
        "setting": job.setting,
        "supervision": job.supervision,
        "team_size": job.team_size,
    }


def _match_from(payload: dict, week: int) -> Match:
    return Match(
        seeker_id=payload["seeker_id"],
        job_id=payload["job_id"],
        week=week,
        skill_fit=payload["skill_fit"],
        env_fit=payload["env_fit"],
        pay_fit=payload["pay_fit"],
        reliability=payload["reliability"],
        relevance=payload["relevance"],
        fair_uncertainty=payload["fair_uncertainty"],
        fair_exposure=payload["fair_exposure"],
        fair_potential=payload["fair_potential"],
        fair_first=payload["fair_first"],
        final_score=payload["final_score"],
        distance_km=payload["distance_km"],
        reasons_json=json.dumps(payload["reasons"]),
        status="allocated",
    )


def _apply_scores(match: Match, payload: dict, week: int) -> None:
    match.week = week
    match.skill_fit = payload["skill_fit"]
    match.env_fit = payload["env_fit"]
    match.pay_fit = payload["pay_fit"]
    match.reliability = payload["reliability"]
    match.relevance = payload["relevance"]
    match.fair_uncertainty = payload["fair_uncertainty"]
    match.fair_exposure = payload["fair_exposure"]
    match.fair_potential = payload["fair_potential"]
    match.fair_first = payload["fair_first"]
    match.final_score = payload["final_score"]
    match.distance_km = payload["distance_km"]
    match.reasons_json = json.dumps(payload["reasons"])


def build_population_edges(seekers: list[dict], jobs: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Pure helper for the sandbox simulation. Dicts mirror the ORM fields used above."""
    districts = {key: value for key, value in DISTRICT_BY_ID.items()}
    sectors = {key: sector_ids(key, districts) for key in districts}
    median_exposure = median([float(item["exposure"]) for item in seekers])
    rows = []
    openings = {}
    for job in jobs:
        openings[job["id"]] = max(0, int(job["openings"]) - int(job.get("filled", 0)))
        for seeker in seekers:
            distance = commute_km(seeker["district_id"], job["district_id"], districts)
            overlap = bool(sectors[seeker["district_id"]] & sectors[job["district_id"]])
            allowed, _reason = passes_hard_filters(seeker, job, distance, overlap)
            if not allowed:
                continue
            skill = skill_fit(seeker["skills"], job["skills"])
            env = env_fit(seeker, job, distance)
            pay = pay_fit(
                seeker["expected_wage"],
                job["salary_min"],
                job["salary_max"],
                job["negotiation_low"],
                job["negotiation_high"],
                job["hike_pct"],
                job.get("perks_present", False),
            )
            rel = reliability(seeker["skill_rd"], seeker["checkin_streak"], seeker["assessment_done"])
            rel_score = relevance(skill, env, pay, rel)
            fair = adjustment(
                rd=seeker["skill_rd"],
                exposure=seeker["exposure"],
                median_exposure=median_exposure,
                potential=seeker["potential"],
                will_train=job["will_train"],
                first_time=seeker["first_time"],
            )
            rows.append(
                {
                    "seeker_id": seeker["id"],
                    "job_id": job["id"],
                    "relevance": rel_score,
                    "final_score": rel_score + fair["total"],
                    "will_train": job["will_train"],
                    "potential": seeker["potential"],
                    "first_time": seeker["first_time"],
                }
            )
    return rows, openings
