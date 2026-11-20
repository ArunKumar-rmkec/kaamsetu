"""Synthetic Tamil Nadu population. Random(42) keeps every reseed identical.

Demo sign-in (mock OTP 123456):
  seeker   9840011101  Priya Selvam, Annamalai's shop floor
  employer 9840022202  Annamalai Textiles, Coimbatore
  official 9840033303  District employment desk
"""

from __future__ import annotations

import json
import random
import secrets
import shutil
import subprocess
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.agents.employer_verification import verify
from app.agents.listing import claims_from_job, compare, mock_tags
from app.catalog import DISTRICTS, TAXONOMY
from app.config import UPLOAD_DIR
from app.db import SessionLocal, engine
from app.models import (
    AssessmentAnswer,
    Base,
    Checkin,
    Clock,
    ConsentEvent,
    EmployerProfile,
    Feedback,
    Hire,
    Job,
    JobSkill,
    Match,
    SeekerProfile,
    SeekerSkill,
    User,
)
from app.scoring.rubric import potential_from_scores, score_answer
from app.services.feedback_service import award_for_events, mark_hired_badge
from app.services.matching_service import run_matching

DEMO_SEEKER_PHONE = "9840011101"
DEMO_EMPLOYER_PHONE = "9840022202"
DEMO_OFFICIAL_PHONE = "9840033303"

FIRST_WOMEN = ["Kavya", "Divya", "Meena", "Lakshmi", "Anitha", "Revathi", "Sangeetha", "Deepa", "Nandhini", "Ishwarya"]
FIRST_MEN = ["Arun", "Karthik", "Suresh", "Murugan", "Vignesh", "Hari", "Prakash", "Senthil", "Gokul", "Dinesh"]
LAST = ["Pandian", "Murugesan", "Krishnan", "Subramanian", "Natarajan", "Ramasamy", "Ganesan", "Pillai", "Thevar", "Nadar"]
EDUCATION = ["10th", "12th", "ITI", "Diploma", "College"]
SHIFTS = ["day", "day", "day", "rotating", "night"]
SETTINGS = ["indoor", "indoor", "outdoor", "either"]
SUPERVISION = ["close", "independent", "either"]
TEAMS = ["solo", "small", "small", "large", "any"]
COMPANIES = [
    "Kongu Auto Components",
    "Cauvery Foods",
    "Vaigai Logistics",
    "Bhavani Garments",
    "Noyyal Engineering",
    "Madurai Tiffin Hall",
    "Pallavan Builders",
    "Thamirabarani Packers",
    "Vellore Care Home",
    "Salem Electronics",
    "Kaveri Silks Unit",
    "Amaravathi Motors",
    "Ponni Agro Foods",
    "Cholan Retail",
    "Mullai Warehousing",
    "Surya Stitching",
    "Kumari Seafoods",
    "Palar Construction",
    "Bharani Health Assist",
    "Thenpennai Textiles",
    "Irumbu Weld Works",
    "Malai Data Desk",
    "Kovai Fresh Kitchen",
]


def seed(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if db.scalar(select(User.id).limit(1)) and not reset:
            print("database already seeded; pass --reset to rebuild")
            return
        rng = random.Random(42)
        db.add(Clock(id=1, week=2, day=2))
        official = _user(DEMO_OFFICIAL_PHONE, "official", "District Employment Desk", "demo-official-token")
        db.add(official)

        employers = [_demo_employer(db)]
        for index, company in enumerate(COMPANIES):
            employers.append(_random_employer(db, rng, index, company))
        db.flush()

        jobs = []
        jobs.extend(_demo_jobs(db, employers[0]))
        made = 0
        while made < 57:
            employer = employers[rng.randrange(len(employers))]
            if not employer.verified and rng.random() < 0.7:
                continue
            jobs.append(_random_job(db, rng, employer, flagged=(made in (3, 11, 19, 28))))
            made += 1
        db.flush()

        seekers = [_demo_seeker(db)]
        for index in range(199):
            seekers.append(_random_seeker(db, rng, index))
        db.commit()

        summary = run_matching(db, week=2)
        _demo_story(db)
        for seeker in db.scalars(select(SeekerProfile)).all():
            award_for_events(seeker)
        db.commit()
        print(
            json.dumps(
                {
                    "seekers": len(seekers),
                    "employers": len(employers),
                    "jobs": len(jobs) + 0,
                    "matching": summary,
                    "demo": {
                        "seeker": DEMO_SEEKER_PHONE,
                        "employer": DEMO_EMPLOYER_PHONE,
                        "official": DEMO_OFFICIAL_PHONE,
                        "otp": "123456",
                    },
                },
                indent=2,
            )
        )
    finally:
        db.close()


def _user(phone: str, role: str, name: str, token: str | None = None) -> User:
    return User(role=role, phone=phone, name=name, token=token or secrets.token_urlsafe(18))


def _demo_employer(db) -> EmployerProfile:
    user = _user(DEMO_EMPLOYER_PHONE, "employer", "Annamalai", "demo-employer-token")
    db.add(user)
    db.flush()
    checks = verify(
        {
            "aadhaar": "234123412341",
            "gstin": "33AABCU9603R1ZM",
            "udyam": "UDYAM-TN-07-0012345",
            "epfo_id": "CB/CBE/1234567",
        }
    )
    profile = EmployerProfile(
        user_id=user.id,
        company_name="Annamalai Textiles",
        district_id="coimbatore",
        gstin="33AABCU9603R1ZM",
        udyam="UDYAM-TN-07-0012345",
        epfo_id="CB/CBE/1234567",
        aadhaar_masked=checks["aadhaar_ekyc"]["masked"],
        verification_json=json.dumps(checks),
        verified=True,
        trust_alpha=checks["trust_alpha0"] + 0.4,
        trust_beta=checks["trust_beta0"],
        trust_alpha0=checks["trust_alpha0"],
        trust_beta0=checks["trust_beta0"],
        trust_score=round(100 * (checks["trust_alpha0"] + 0.4) / (checks["trust_alpha0"] + 0.4 + checks["trust_beta0"]), 1),
    )
    db.add(profile)
    return profile


def _random_employer(db, rng: random.Random, index: int, company: str) -> EmployerProfile:
    phone = f"98410{index:05d}"
    user = _user(phone, "employer", company.split()[0])
    db.add(user)
    db.flush()
    fail = index in (4, 9, 15)
    payload = {
        "aadhaar": "900000000000" if fail else f"23{index:010d}"[:12],
        "gstin": "33AABCU9603R1ZZ" if fail else "33AABCU9603R1ZM",
        "udyam": "NOT-A-UDYAM" if index in (4, 18) else f"UDYAM-TN-{(index % 40):02d}-{index:07d}",
        "epfo_id": "BAD" if index == 15 else f"CB/CBE/{1000000 + index}",
    }
    checks = verify(payload)
    alpha, beta = checks["trust_alpha0"], checks["trust_beta0"]
    profile = EmployerProfile(
        user_id=user.id,
        company_name=company,
        district_id=DISTRICTS[index % len(DISTRICTS)]["id"],
        gstin=payload["gstin"],
        udyam=payload["udyam"],
        epfo_id=payload["epfo_id"],
        aadhaar_masked=checks["aadhaar_ekyc"]["masked"],
        verification_json=json.dumps(checks),
        verified=checks["verified"],
        trust_alpha=alpha,
        trust_beta=beta,
        trust_alpha0=alpha,
        trust_beta0=beta,
        trust_score=checks["trust_score"],
    )
    db.add(profile)
    return profile


def _demo_jobs(db, employer: EmployerProfile) -> list[Job]:
    specs = [
        {
            "title": "Sewing machine operator",
            "sector": "garments",
            "salary": (14000, 16500),
            "will_train": True,
            "skills": [("8152.02", 3, True), ("7533.01", 2, False)],
            "mismatch": False,
            "openings": 4,
            "physical": 2,
        },
        {
            "title": "Garment quality checker",
            "sector": "garments",
            "salary": (15000, 18000),
            "will_train": False,
            "skills": [("3139.10", 3, True)],
            "mismatch": False,
            "openings": 2,
            "physical": 2,
        },
        {
            "title": "Floor helper, night cutting",
            "sector": "garments",
            "salary": (16000, 19000),
            "will_train": False,
            "skills": [("7533.01", 2, True)],
            "mismatch": True,
            "openings": 3,
            "physical": 3,
            "night": True,
            "flagged_only": True,
        },
    ]
    jobs = []
    for spec in specs:
        jobs.append(_add_job(db, employer, spec, district="coimbatore"))
    return jobs


def _random_job(db, rng: random.Random, employer: EmployerProfile, flagged: bool) -> Job:
    skill = rng.choice(TAXONOMY)
    extra = rng.choice(TAXONOMY)
    low = rng.randrange(12, 24) * 1000
    high = low + rng.choice([1500, 2000, 3000, 4000])
    spec = {
        "title": skill["title_en"],
        "sector": skill["sector"],
        "salary": (low, high),
        "will_train": rng.random() < 0.42,
        "skills": [(skill["code"], rng.randint(2, 4), True)],
        "mismatch": flagged,
        "openings": rng.randint(2, 6),
        "physical": rng.randint(1, 5),
        "night": rng.random() < 0.12,
        "lodging": rng.random() < 0.28,
        "shift": rng.choice(["day", "day", "rotating", "night"]),
        "setting": rng.choice(SETTINGS),
        "team": rng.choice(["small", "small", "large", "solo"]),
        "freshers": rng.random() < 0.7,
        "hike": rng.choice([0, 5, 8, 10]),
        "perks": rng.choice(["", "Canteen", "Bus from the bus stand", "ESI and PF", "One meal"]),
    }
    if extra["code"] != skill["code"] and rng.random() < 0.4:
        spec["skills"].append((extra["code"], 2, False))
    return _add_job(db, employer, spec, district=employer.district_id if rng.random() < 0.75 else rng.choice(DISTRICTS)["id"])


def _add_job(db, employer: EmployerProfile, spec: dict, district: str) -> Job:
    night = spec.get("night", False)
    shift = spec.get("shift", "night" if night else "day")
    claims = {
        "setting": spec.get("setting", "indoor"),
        "team_size": spec.get("team", "small"),
        "physical": spec.get("physical", 2),
        "night_required": night,
        "lodging_provided": spec.get("lodging", False),
        "sector": spec["sector"],
    }
    mismatch = spec.get("mismatch", False)
    tags = mock_tags(claims, mismatch)
    report = compare(claims, tags)
    video_name = _video_file(f"job-{employer.user_id}-{spec['title'][:18].replace(' ', '-').lower()}")
    job = Job(
        employer_id=employer.user_id,
        title=spec["title"],
        sector=spec["sector"],
        district_id=district,
        description=f"{spec['title']} at {employer.company_name}. Structured workplace, not a free-text advert.",
        salary_min=spec["salary"][0],
        salary_max=spec["salary"][1],
        hike_pct=spec.get("hike", 5 if spec.get("will_train") else 0),
        perks=spec.get("perks", "Canteen"),
        negotiation_low=spec["salary"][0] - 500,
        negotiation_high=spec["salary"][1] + 500,
        open_to_freshers=spec.get("freshers", True),
        will_train=spec["will_train"],
        openings=spec["openings"],
        shift=shift,
        night_required=night,
        physical=spec.get("physical", 2),
        setting=spec.get("setting", "indoor"),
        lodging_provided=spec.get("lodging", False),
        supervision=spec.get("supervision", "close"),
        team_size=spec.get("team", "small"),
        video_path=video_name,
        video_tags_json=json.dumps(tags),
        verification_status=report["status"],
        verification_report_json=json.dumps(report),
        verification_source="mock-tags",
        status="open",
        created_week=1,
    )
    db.add(job)
    db.flush()
    for code, level, required in spec["skills"]:
        db.add(JobSkill(job_id=job.id, code=code, min_level=level, required=required))
    tag_path = UPLOAD_DIR / f"{Path(video_name).stem}.tags.json"
    tag_path.write_text(json.dumps(tags, indent=2))
    return job


def _video_file(stem: str) -> str:
    """Reuse one generated clip. The checker compares tag files, not the pixels, unless a vision key is set."""
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in stem)[:60]
    target = UPLOAD_DIR / f"{safe}.mp4"
    canonical = UPLOAD_DIR / "_sample-floor.mp4"
    if not canonical.exists() or canonical.stat().st_size < 32:
        if shutil.which("ffmpeg"):
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=0x0e6b4f:s=320x180:d=2",
                    "-pix_fmt",
                    "yuv420p",
                    str(canonical),
                ],
                capture_output=True,
                check=False,
            )
        if not canonical.exists() or canonical.stat().st_size < 32:
            canonical.write_bytes(b"KAAMSETU-PLACEHOLDER-VIDEO")
    if not target.exists():
        shutil.copy(canonical, target)
    return target.name


def _demo_seeker(db) -> SeekerProfile:
    user = _user(DEMO_SEEKER_PHONE, "seeker", "Priya Selvam", "demo-seeker-token")
    db.add(user)
    db.flush()
    profile = SeekerProfile(
        user_id=user.id,
        district_id="coimbatore",
        education="ITI",
        gender="woman",
        age=22,
        years_experience=1,
        expected_wage=14500,
        shift="day",
        night_ok=False,
        physical=2,
        setting="indoor",
        lodging_needed=False,
        max_commute_km=30,
        supervision="close",
        team_size="small",
        consent=True,
        onboarding_complete=True,
        skill_mu=1660,
        skill_rd=160,
        skill_last_week=2,
        hired_before=False,
        checkin_streak=4,
        checkin_total=4,
        assessment_done=True,
    )
    answers = {
        "safety_stop": "I switch off the power, keep the area safe, and tell the supervisor what stopped.",
        "public_correction": "I stay calm, listen, thank them, and practice the step again so I improve.",
        "family_overtime": "I tell the supervisor about the family need and we plan who can cover the overtime.",
        "teammate_behind": "I help my teammate and we finish the line together instead of leaving them behind.",
        "safety_speak": "I stop the table and report the safety problem to the supervisor before someone is hurt.",
        "learned_without_class": "I learned stitching by watching my neighbour and practicing every evening on scrap cloth.",
    }
    scores = []
    for question_id, text in answers.items():
        value = score_answer(question_id, text)
        scores.append(value)
        db.add(AssessmentAnswer(user_id=user.id, question_id=question_id, answer=text, rubric_score=value))
    profile.potential = potential_from_scores(scores)
    db.add(profile)
    db.add(SeekerSkill(user_id=user.id, code="8152.02", level=4, source="self"))
    db.add(SeekerSkill(user_id=user.id, code="7533.01", level=4, source="self"))
    db.add(SeekerSkill(user_id=user.id, code="3139.10", level=2, source="self"))
    for day, mood in ((1, "good"), (2, "good"), (3, "okay"), (1, "good")):
        week = 1 if day < 4 else 2
        # four rows: week 1 days 1-3 and week 2 day 1. The loop above collides. Write explicitly below.
    db.add(Checkin(seeker_id=user.id, week=1, day=1, mood="good", note="Reached the unit on time."))
    db.add(Checkin(seeker_id=user.id, week=1, day=2, mood="good", note="Learned a new stitch."))
    db.add(Checkin(seeker_id=user.id, week=1, day=3, mood="okay", note="Long table, still finished."))
    db.add(Checkin(seeker_id=user.id, week=2, day=1, mood="good", note="Bus was on time."))
    return profile


def _random_seeker(db, rng: random.Random, index: int) -> SeekerProfile:
    woman = rng.random() < 0.48
    first = rng.choice(FIRST_WOMEN if woman else FIRST_MEN)
    name = f"{first} {rng.choice(LAST)}"
    phone = f"98420{index:05d}"
    user = _user(phone, "seeker", name)
    db.add(user)
    db.flush()
    district = DISTRICTS[index % len(DISTRICTS)]["id"]
    if rng.random() < 0.35:
        district = rng.choice(DISTRICTS)["id"]
    experience = rng.choice([0, 0, 0, 1, 1, 2, 4])
    skills = rng.sample(TAXONOMY, k=rng.choice([1, 1, 2, 2, 3]))
    levels = [rng.randint(1, 5) for _ in skills]
    avg = sum(levels) / len(levels)
    mu = 1320 + avg * 70 + experience * 25 + rng.uniform(-40, 40)
    rd = rng.uniform(220, 350) if experience == 0 else rng.uniform(90, 240)
    answers = _synthetic_answers(rng, high=rng.random() < 0.35)
    scores = [score_answer(key, text) for key, text in answers.items()]
    potential = potential_from_scores(scores)
    profile = SeekerProfile(
        user_id=user.id,
        district_id=district,
        education=rng.choice(EDUCATION),
        gender="woman" if woman else "man",
        age=rng.randint(18, 32),
        years_experience=experience,
        expected_wage=rng.randrange(11, 26) * 1000,
        shift=rng.choice(SHIFTS),
        night_ok=rng.random() < 0.25,
        physical=rng.randint(1, 5),
        setting=rng.choice(SETTINGS),
        lodging_needed=rng.random() < 0.22,
        max_commute_km=rng.choice([12, 15, 20, 25, 30, 40, 60]),
        supervision=rng.choice(SUPERVISION),
        team_size=rng.choice(TEAMS),
        consent=rng.random() > 0.04,
        onboarding_complete=True,
        skill_mu=round(mu, 1),
        skill_rd=round(rd, 1),
        skill_last_week=2,
        potential=potential,
        exposure=rng.choice([0, 0, 0, 0, 1, 2, 4, 8, 12]),
        hired_before=experience > 0 and rng.random() < 0.55,
        checkin_streak=rng.randint(0, 6),
        checkin_total=rng.randint(0, 8),
        assessment_done=True,
    )
    db.add(profile)
    for skill, level in zip(skills, levels):
        db.add(SeekerSkill(user_id=user.id, code=skill["code"], level=level, source="self"))
    for question_id, text in answers.items():
        db.add(
            AssessmentAnswer(
                user_id=user.id,
                question_id=question_id,
                answer=text,
                rubric_score=score_answer(question_id, text),
            )
        )
    return profile


def _synthetic_answers(rng: random.Random, high: bool) -> dict[str, str]:
    if high:
        return {
            "safety_stop": "I stop the machine, switch off power, and tell the supervisor so the area stays safe.",
            "public_correction": "I listen, stay calm, say thank you, and practice again to improve.",
            "family_overtime": "I inform the supervisor about the family plan and we agree who can cover.",
            "teammate_behind": "I help the teammate and we share the pending pieces so the line can finish.",
            "safety_speak": "I report the safety issue and warn the people beside me before work continues.",
            "learned_without_class": "I learned by watching a neighbour, then practiced every evening until it held.",
        }
    if rng.random() < 0.5:
        return {
            "safety_stop": "I call someone.",
            "public_correction": "I feel bad and go quiet.",
            "family_overtime": "I go home.",
            "teammate_behind": "I do my own work.",
            "safety_speak": "I wait.",
            "learned_without_class": "I tried a little.",
        }
    return {
        "safety_stop": "I stop and tell the supervisor the machine is off.",
        "public_correction": "I listen and try to improve the step.",
        "family_overtime": "I tell them about my family and ask for a plan.",
        "teammate_behind": "I help if I can.",
        "safety_speak": "I report it.",
        "learned_without_class": "I practiced at home after watching.",
    }


def _demo_story(db) -> None:
    """Shape a few rows so each screen has something to show without hiding the algorithm."""
    priya = db.scalar(select(User).where(User.phone == DEMO_SEEKER_PHONE))
    employer = db.scalar(select(User).where(User.phone == DEMO_EMPLOYER_PHONE))
    assert priya and employer
    jobs = db.scalars(select(Job).where(Job.employer_id == employer.id).options(selectinload(Job.skills))).all()
    sewing = next(job for job in jobs if job.title.startswith("Sewing"))
    quality = next(job for job in jobs if job.title.startswith("Garment"))
    priya_matches = db.scalars(select(Match).where(Match.seeker_id == priya.id)).all()
    sewing_match = next((item for item in priya_matches if item.job_id == sewing.id), None)
    if sewing_match is None:
        return
    sewing_match.status = "hired"
    sewing.filled = 1
    hire = Hire(
        match_id=sewing_match.id,
        seeker_id=priya.id,
        job_id=sewing.id,
        employer_id=employer.id,
        week_hired=1,
        active=True,
    )
    db.add(hire)
    db.flush()
    db.add(
        Feedback(
            hire_id=hire.id,
            week=1,
            author_role="employer",
            rating=5,
            comment="Learns the machine quickly and asks when the stitch is off.",
            revealed=True,
            scores_applied=True,
        )
    )
    db.add(
        Feedback(
            hire_id=hire.id,
            week=1,
            author_role="seeker",
            rating=4,
            comment="Supervisor explains. Canteen is fine. Bus is crowded.",
            revealed=True,
            scores_applied=True,
        )
    )
    db.add(ConsentEvent(match_id=sewing_match.id, seeker_id=priya.id, employer_id=employer.id, action="accept"))
    profile = db.get(SeekerProfile, priya.id)
    if profile:
        mark_hired_badge(profile)
        # Apply the week-1 exchange on top of the seeded prior so the numbers are the real update.
        from app.services.feedback_service import _apply_scores

        _apply_scores(db, hire, employer_rates_seeker=5, seeker_rates_employer=4)

    priya_quality = next((item for item in priya_matches if item.job_id == quality.id and item.status == "allocated"), None)
    if priya_quality is None:
        pool = db.scalars(select(Match).where(Match.job_id == quality.id, Match.status == "allocated")).all()
        priya_quality = pool[0] if pool else None
    if priya_quality is not None:
        priya_quality.status = "interested"
        db.add(
            ConsentEvent(
                match_id=priya_quality.id,
                seeker_id=priya_quality.seeker_id,
                employer_id=employer.id,
                action="interest",
            )
        )
    # A second Annamalai opening should show anonymous cards. Sewing already has Priya hired;
    # leave the other sewing allocations anonymous.
    others = db.scalars(select(Match).where(Match.status == "allocated")).all()
    rng = random.Random(7)
    hired_extra = 0
    for match in others:
        if hired_extra >= 10:
            break
        if match.seeker_id == priya.id:
            continue
        if rng.random() > 0.08:
            continue
        job = db.get(Job, match.job_id)
        if job is None or job.filled >= job.openings:
            continue
        match.status = "hired"
        job.filled += 1
        extra = Hire(
            match_id=match.id,
            seeker_id=match.seeker_id,
            job_id=job.id,
            employer_id=job.employer_id,
            week_hired=1,
            active=True,
        )
        db.add(extra)
        db.flush()
        seeker = db.get(SeekerProfile, match.seeker_id)
        if seeker:
            mark_hired_badge(seeker)
        revealed = rng.random() < 0.6
        for role, rating in (("employer", rng.randint(3, 5)), ("seeker", rng.randint(3, 5))):
            db.add(
                Feedback(
                    hire_id=extra.id,
                    week=1,
                    author_role=role,
                    rating=rating,
                    comment="Seeded checkpoint.",
                    revealed=revealed,
                    scores_applied=revealed,
                )
            )
        hired_extra += 1
    db.commit()


if __name__ == "__main__":
    import sys

    seed(reset="--reset" in sys.argv)
