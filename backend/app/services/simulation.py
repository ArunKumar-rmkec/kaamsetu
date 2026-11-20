"""In-memory 4-week comparison. Does not write seeker or job rows.

Each arm is a copy of the seeded population. Ranking uses raw relevance and a
greedy cap. KaamSetu uses fairness-adjusted scores and the two-phase min-cost flow.
"""

from __future__ import annotations

import random
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Job, SeekerProfile
from app.scoring.allocate import allocate
from app.scoring.metrics import gini, summarise_exposure
from app.services.matching_service import build_population_edges


def simulate_four_weeks(db: Session, seed: int = 7) -> dict:
    seekers, jobs = _snapshot(db)
    ranking = _run_arm(seekers, jobs, mode="ranking", seed=seed)
    kaamsetu = _run_arm(seekers, jobs, mode="kaamsetu", seed=seed)
    return {
        "label": "SIMULATED",
        "disclaimer": "Synthetic Tamil Nadu population. This does not call a live labour exchange or change stored profiles.",
        "weeks": 4,
        "seekers": len(seekers),
        "jobs": len(jobs),
        "seed": seed,
        "ranking": ranking,
        "kaamsetu": kaamsetu,
        "read": _readout(ranking, kaamsetu),
    }


def _run_arm(seekers: list[dict], jobs: list[dict], mode: str, seed: int) -> dict:
    rng = random.Random(seed + (1 if mode == "kaamsetu" else 0))
    people = [dict(item) for item in seekers]
    openings = {job["id"]: job["openings"] for job in jobs}
    exposure = {item["id"]: 0 for item in people}
    first_week: dict[str, int] = {}
    hires: list[dict] = []
    weekly = []
    relevance_sum = 0.0
    relevance_n = 0
    high_potential_freshers = {item["id"] for item in people if item["potential"] >= 75 and item["first_time"]}
    covered_train: set[str] = set()

    for week in range(1, 5):
        rows, _ = build_population_edges(people, [{**job, "openings": openings[job["id"]], "filled": 0} for job in jobs])
        score_key = "final_score" if mode == "kaamsetu" else "relevance"
        edges = [(row["seeker_id"], row["job_id"], row[score_key]) for row in rows if openings.get(row["job_id"], 0) > 0]
        job_caps = {job_id: seats for job_id, seats in openings.items()}
        chosen = allocate(edges, job_caps, mode=mode, seeker_cap=3)
        by_pair = {(row["seeker_id"], row["job_id"]): row for row in rows}
        for seeker_id, job_id in chosen:
            exposure[seeker_id] = exposure.get(seeker_id, 0) + 1
            first_week.setdefault(seeker_id, week)
            relevance_sum += by_pair[(seeker_id, job_id)]["relevance"]
            relevance_n += 1
            if job_id and by_pair[(seeker_id, job_id)]["will_train"] and seeker_id in high_potential_freshers:
                covered_train.add(seeker_id)
        hired_this_week = _simulate_hires(chosen, by_pair, openings, people, rng)
        for hire in hired_this_week:
            person = next(item for item in people if item["id"] == hire["seeker_id"])
            person["first_time"] = False
            person["exposure"] = exposure[person["id"]]
            hires.append({**hire, "week": week})
        for person in people:
            person["exposure"] = exposure[person["id"]]
        weekly.append({"week": week, "assignments": len(chosen), "hires": len(hired_this_week)})

    matched_weeks = [first_week[item["id"]] for item in people if item["id"] in first_week]
    time_to_match = sum(matched_weeks) / len(matched_weeks) if matched_weeks else None
    first_time_hires = [hire for hire in hires if hire["was_first_time"]]
    summary = summarise_exposure(exposure)
    return {
        "mode": mode,
        "exposure": summary,
        "gini": summary["gini"],
        "share_with_at_least_one": summary["share_with_at_least_one"],
        "share_with_zero_exposure": summary["share_with_zero_exposure"],
        "first_time_hire_share": round(len(first_time_hires) / len(hires), 4) if hires else 0.0,
        "hires": len(hires),
        "mean_time_to_first_match_weeks": round(time_to_match, 3) if time_to_match is not None else None,
        "unmatched_seekers": sum(1 for item in people if item["id"] not in first_week),
        "mean_relevance": round(relevance_sum / relevance_n, 4) if relevance_n else 0.0,
        "high_potential_fresher_train_coverage": round(
            len(covered_train) / len(high_potential_freshers), 4
        )
        if high_potential_freshers
        else None,
        "weekly": weekly,
    }


def _simulate_hires(chosen, by_pair, openings, people, rng: random.Random) -> list[dict]:
    """Each job hires at most one allocated candidate this week, biased toward higher relevance."""
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for pair in chosen:
        grouped[pair[1]].append(pair)
    first_time_lookup = {item["id"]: item["first_time"] for item in people}
    hired = []
    for job_id, pairs in grouped.items():
        if openings.get(job_id, 0) <= 0:
            continue
        ranked = sorted(pairs, key=lambda pair: by_pair[pair]["relevance"], reverse=True)
        top = ranked[0]
        probability = 0.35 + 0.5 * by_pair[top]["relevance"]
        if rng.random() <= probability:
            openings[job_id] -= 1
            hired.append(
                {
                    "seeker_id": top[0],
                    "job_id": job_id,
                    "was_first_time": first_time_lookup.get(top[0], False),
                }
            )
    return hired


def _snapshot(db: Session) -> tuple[list[dict], list[dict]]:
    seekers = db.scalars(select(SeekerProfile).options(selectinload(SeekerProfile.skills))).all()
    jobs = db.scalars(
        select(Job).options(selectinload(Job.skills), selectinload(Job.employer))
    ).all()
    seeker_rows = []
    for seeker in seekers:
        seeker_rows.append(
            {
                "id": str(seeker.user_id),
                "district_id": seeker.district_id,
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
                "expected_wage": seeker.expected_wage,
                "skills": {item.code: item.level for item in seeker.skills},
                "skill_rd": seeker.skill_rd,
                "checkin_streak": seeker.checkin_streak,
                "assessment_done": seeker.assessment_done,
                "exposure": 0,
                "potential": seeker.potential,
                "first_time": not seeker.hired_before,
            }
        )
    job_rows = []
    for job in jobs:
        if job.verification_status != "passed" or job.status != "open":
            continue
        if not job.employer or not job.employer.verified:
            continue
        job_rows.append(
            {
                "id": str(job.id),
                "district_id": job.district_id,
                "night_required": job.night_required,
                "lodging_provided": job.lodging_provided,
                "verification_status": "passed",
                "status": "open",
                "openings": max(1, job.openings),
                "filled": 0,
                "employer_verified": True,
                "shift": job.shift,
                "physical": job.physical,
                "setting": job.setting,
                "supervision": job.supervision,
                "team_size": job.team_size,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "negotiation_low": job.negotiation_low,
                "negotiation_high": job.negotiation_high,
                "hike_pct": job.hike_pct,
                "perks_present": bool(job.perks.strip()),
                "will_train": job.will_train,
                "skills": [{"code": item.code, "min_level": item.min_level, "required": item.required} for item in job.skills],
            }
        )
    return seeker_rows, job_rows


def _readout(ranking: dict, kaamsetu: dict) -> list[str]:
    lines = []
    if kaamsetu["gini"] < ranking["gini"]:
        lines.append("KaamSetu's exposure Gini is lower, so recommendations are spread more evenly.")
    else:
        lines.append("On this seed, exposure Gini did not fall. Read the coverage numbers beside it.")
    lines.append(
        f"Seekers with at least one recommendation: ranking {ranking['share_with_at_least_one']:.0%}, "
        f"KaamSetu {kaamsetu['share_with_at_least_one']:.0%}."
    )
    lines.append(
        f"First-time share of simulated hires: ranking {ranking['first_time_hire_share']:.0%}, "
        f"KaamSetu {kaamsetu['first_time_hire_share']:.0%}."
    )
    return lines


def live_fairness_snapshot(exposure_values: list[int], hires: list[dict], first_match_weeks: list[int]) -> dict:
    summary = summarise_exposure({str(index): value for index, value in enumerate(exposure_values)})
    first_time = [item for item in hires if item.get("was_first_time")]
    return {
        "exposure": summary,
        "gini": round(gini([float(value) for value in exposure_values]), 4),
        "first_time_hire_share": round(len(first_time) / len(hires), 4) if hires else 0.0,
        "hire_count": len(hires),
        "mean_time_to_first_match_weeks": round(sum(first_match_weeks) / len(first_match_weeks), 3)
        if first_match_weeks
        else None,
    }
