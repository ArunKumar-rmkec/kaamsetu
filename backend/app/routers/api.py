"""HTTP API. Scoring and allocation stay in app.scoring and app.services."""

from __future__ import annotations

import json
import secrets
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.agents.explainer import profile_reasons
from app.agents.listing import claims_from_job
from app.agents.orchestrator import log_result, run as run_agent
from app.catalog import DISTRICTS, QUESTIONS, SECTORS, TAXONOMY, TAXONOMY_BY_CODE
from app.config import MOCK_OTP, UPLOAD_DIR
from app.deps import (
    current_user,
    employer_payload,
    employer_profile,
    job_brief,
    load_json,
    owned_match,
    require_role,
    seeker_payload,
    seeker_profile,
)
from app.models import (
    AssessmentAnswer,
    Checkin,
    EmployerProfile,
    Feedback,
    Hire,
    Job,
    JobSkill,
    Match,
    SeekerProfile,
    SeekerSkill,
    SimulationReport,
    User,
)
from app.schemas import ChatIn, CheckinIn, ConsentIn, FeedbackIn, MapIn, OnboardingIn, OtpRequest, OtpVerify, VerifyIn
from app.scoring.trust import apply_listing, trust_score
from app.services.feedback_service import (
    advance_day,
    advance_week,
    award_for_events,
    get_clock,
    mark_hired_badge,
    record_checkin,
    submit_feedback,
)
from app.services.matching_service import run_matching
from app.services.simulation import live_fairness_snapshot

import app.agents.registry  # noqa: F401  — registers agent handlers

router = APIRouter(prefix="/api")


def _db():
    from app.db import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.get("/health")
def health():
    from app.agents.llm import llm_configured
    from app.db import SessionLocal

    session = SessionLocal()
    try:
        clock = get_clock(session)
        seekers = session.scalar(select(func.count()).select_from(SeekerProfile)) or 0
        return {
            "ok": True,
            "week": clock.week,
            "day": clock.day,
            "seekers": seekers,
            "llm_configured": llm_configured(),
            "otp": "mock",
        }
    finally:
        session.close()


@router.get("/meta")
def meta():
    return {
        "districts": DISTRICTS,
        "taxonomy": TAXONOMY,
        "sectors": SECTORS,
        "questions": QUESTIONS,
        "otp_hint": MOCK_OTP,
        "labels": {
            "simulated_verification": "SIMULATED",
            "simulated_population": "SIMULATED",
        },
    }


@router.post("/auth/request-otp")
def request_otp(body: OtpRequest):
    phone = _phone(body.phone)
    if body.role not in ("seeker", "employer", "official"):
        raise HTTPException(status_code=400, detail="Role must be seeker, employer, or official")
    return {
        "sent": True,
        "simulated": True,
        "phone": phone,
        "hint": MOCK_OTP,
        "message": "No SMS was sent. Use the mock OTP shown on the sign-in screen.",
    }


@router.post("/auth/verify-otp")
def verify_otp(body: OtpVerify, db: Session = Depends(_db)):
    if body.otp.strip() != MOCK_OTP:
        raise HTTPException(status_code=400, detail="That OTP does not match the mock code")
    phone = _phone(body.phone)
    if body.role not in ("seeker", "employer", "official"):
        raise HTTPException(status_code=400, detail="Unknown role")
    user = db.scalar(select(User).where(User.phone == phone))
    if user and user.role != body.role:
        raise HTTPException(status_code=409, detail=f"This phone is already a {user.role}")
    if user is None:
        user = User(role=body.role, phone=phone, name=body.name.strip() or "New user", token=secrets.token_urlsafe(18))
        db.add(user)
        db.flush()
        if body.role == "seeker":
            db.add(SeekerProfile(user_id=user.id, district_id=body.district_id or "coimbatore"))
        elif body.role == "employer":
            db.add(
                EmployerProfile(
                    user_id=user.id,
                    company_name=body.company_name.strip() or f"{user.name} unit",
                    district_id=body.district_id or "coimbatore",
                )
            )
        db.commit()
        db.refresh(user)
    elif body.name.strip():
        user.name = body.name.strip()
        db.commit()
    return {"token": user.token, "user": {"id": user.id, "name": user.name, "phone": user.phone, "role": user.role}}


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "phone": user.phone, "role": user.role}


@router.get("/seekers/me")
def seeker_me(user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "seeker")
    profile = seeker_profile(db, user)
    reasons = profile_reasons(_reason_seeker(profile), _reason_skills(profile), _reason_answers(profile))
    payload = seeker_payload(user, profile, reasons)
    payload["clock"] = _clock(db)
    return payload


@router.post("/seekers/onboarding")
def onboard(body: OnboardingIn, user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "seeker")
    profile = seeker_profile(db, user)
    user.name = body.name.strip() or user.name
    for field in (
        "district_id",
        "education",
        "gender",
        "age",
        "years_experience",
        "expected_wage",
        "shift",
        "night_ok",
        "physical",
        "setting",
        "lodging_needed",
        "max_commute_km",
        "supervision",
        "team_size",
        "consent",
    ):
        setattr(profile, field, getattr(body, field))
    mapped = {"codes": []}
    if body.free_text_skill.strip():
        mapped = run_agent(db, "taxonomy_mapper", {"text": body.free_text_skill, "level": 2})
    codes = {(item.code): item.level for item in body.skills}
    for item in mapped.get("codes", []):
        codes.setdefault(item["code"], item["level"])
    unknown = [code for code in codes if code not in TAXONOMY_BY_CODE]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown skill codes: {unknown}")
    if not codes:
        raise HTTPException(status_code=400, detail="Add at least one skill from the list")
    for existing in list(profile.skills):
        db.delete(existing)
    for code, level in codes.items():
        db.add(SeekerSkill(user_id=user.id, code=code, level=int(level), source="mapped" if code not in {s.code for s in body.skills} else "self"))
    assessment = run_agent(db, "assessment", {"answers": [item.model_dump() for item in body.answers]})
    for existing in list(profile.answers):
        db.delete(existing)
    for item in assessment["answers"]:
        db.add(
            AssessmentAnswer(
                user_id=user.id,
                question_id=item["question_id"],
                answer=item["answer"],
                rubric_score=item["rubric_score"],
            )
        )
    profile.potential = assessment["potential"]
    profile.assessment_done = len(assessment["answers"]) >= 6
    profile.onboarding_complete = True
    award_for_events(profile)
    db.commit()
    clock = get_clock(db)
    matching = run_matching(db, week=clock.week, job_id=None)
    log_result(db, "matching", {"seeker_id": user.id, "week": clock.week}, matching)
    profile = seeker_profile(db, user)
    reasons = profile_reasons(_reason_seeker(profile), _reason_skills(profile), _reason_answers(profile))
    return {
        "profile": seeker_payload(user, profile, reasons),
        "assessment": assessment,
        "mapped_skills": mapped.get("codes", []),
        "matching": matching,
    }


@router.post("/seekers/consent")
def set_consent(body: ConsentIn, user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "seeker")
    profile = seeker_profile(db, user)
    profile.consent = body.consent
    if not body.consent:
        for match in db.scalars(select(Match).where(Match.seeker_id == user.id, Match.status == "allocated")).all():
            db.delete(match)
    db.commit()
    log_result(db, "consent_broker", {"seeker_id": user.id, "action": "consent_toggle"}, {"consent": body.consent, "used_llm": False})
    return {"consent": profile.consent}


@router.get("/seekers/matches")
def seeker_matches(user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "seeker")
    rows = db.scalars(select(Match).where(Match.seeker_id == user.id)).all()
    cards = []
    for match in rows:
        job = db.scalar(select(Job).where(Job.id == match.job_id))
        employer = db.get(EmployerProfile, job.employer_id) if job else None
        if job and employer:
            from app.agents.consent import seeker_card

            cards.append(seeker_card(match, job, employer))
    cards.sort(key=lambda item: item["fits"]["final"], reverse=True)
    return {"matches": cards, "clock": _clock(db)}


@router.post("/seekers/matches/{match_id}/accept")
def accept_match(match_id: int, user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "seeker")
    match, job = owned_match(db, user, match_id)
    profile = seeker_profile(db, user)
    if not profile.consent:
        raise HTTPException(status_code=400, detail="Turn consent on before sharing your details")
    if match.status not in ("interested", "accepted"):
        raise HTTPException(status_code=400, detail="Wait for the employer to send interest first")
    match.status = "accepted"
    from app.agents.consent import record

    record(db.add, match, user.id, job.employer_id, "accept")
    db.commit()
    run_agent(db, "consent_broker", {"action": "accept", "match_id": match.id})
    return {"status": match.status, "revealed": True}


@router.post("/seekers/matches/{match_id}/decline")
def decline_match(match_id: int, user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "seeker")
    match, job = owned_match(db, user, match_id)
    if match.status in ("hired",):
        raise HTTPException(status_code=400, detail="This hire is already recorded")
    match.status = "declined"
    from app.agents.consent import record

    record(db.add, match, user.id, job.employer_id, "decline")
    db.commit()
    run_agent(db, "consent_broker", {"action": "decline", "match_id": match.id})
    return {"status": match.status}


@router.post("/seekers/checkin")
def checkin(body: CheckinIn, user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "seeker")
    if body.mood not in ("good", "okay", "tough"):
        raise HTTPException(status_code=400, detail="Mood must be good, okay, or tough")
    profile = seeker_profile(db, user)
    clock = get_clock(db)
    row = record_checkin(db, profile, body.mood, body.note.strip(), clock.week, clock.day)
    return {"id": row.id, "week": row.week, "day": row.day, "mood": row.mood, "streak": profile.checkin_streak}


@router.get("/seekers/hires")
def seeker_hires(user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "seeker")
    return {"hires": _hire_rows(db, seeker_id=user.id, viewer="seeker"), "clock": _clock(db)}


@router.post("/seekers/feedback")
def seeker_feedback(body: FeedbackIn, user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "seeker")
    return _save_feedback(db, user, body, "seeker")


@router.post("/agents/intake")
def intake(body: ChatIn, user: User = Depends(current_user), db: Session = Depends(_db)):
    result = run_agent(db, "voice_intake", {"message": body.message, "lang": body.lang, "user_id": user.id})
    return result


@router.post("/agents/map-skill")
def map_skill(body: MapIn, user: User = Depends(current_user), db: Session = Depends(_db)):
    return run_agent(db, "taxonomy_mapper", {"text": body.text, "level": body.level, "user_id": user.id})


@router.get("/employers/me")
def employer_me(user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "employer")
    profile = employer_profile(db, user)
    jobs = db.scalars(select(Job).where(Job.employer_id == user.id).options(selectinload(Job.skills))).all()
    payload = employer_payload(user, profile, list(jobs))
    payload["clock"] = _clock(db)
    return payload


@router.post("/employers/verify")
def verify_employer(body: VerifyIn, user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "employer")
    profile = employer_profile(db, user)
    result = run_agent(db, "employer_verification", body.model_dump())
    profile.gstin = body.gstin.strip().upper()
    profile.udyam = body.udyam.strip().upper()
    profile.epfo_id = body.epfo_id.strip().upper()
    profile.aadhaar_masked = result["aadhaar_ekyc"]["masked"]
    profile.verification_json = json.dumps(result)
    profile.verified = bool(result["verified"])
    profile.trust_alpha = result["trust_alpha0"]
    profile.trust_beta = result["trust_beta0"]
    profile.trust_alpha0 = result["trust_alpha0"]
    profile.trust_beta0 = result["trust_beta0"]
    profile.trust_score = result["trust_score"]
    db.commit()
    return result


@router.post("/jobs")
def create_job(
    user: User = Depends(current_user),
    db: Session = Depends(_db),
    title: str = Form(...),
    sector: str = Form(...),
    district_id: str = Form(...),
    description: str = Form(""),
    salary_min: int = Form(...),
    salary_max: int = Form(...),
    hike_pct: float = Form(0),
    perks: str = Form(""),
    negotiation_low: int = Form(0),
    negotiation_high: int = Form(0),
    open_to_freshers: str = Form("true"),
    will_train: str = Form("false"),
    openings: int = Form(2),
    shift: str = Form("day"),
    night_required: str = Form("false"),
    physical: int = Form(3),
    setting: str = Form("indoor"),
    lodging_provided: str = Form("false"),
    supervision: str = Form("close"),
    team_size: str = Form("small"),
    skills_json: str = Form(...),
    demo_mismatch: str = Form("false"),
    video: UploadFile | None = File(None),
):
    require_role(user, "employer")
    profile = employer_profile(db, user)
    if not profile.verified:
        raise HTTPException(status_code=400, detail="Finish the simulated verification before posting")
    try:
        skills = json.loads(skills_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="skills_json must be a JSON list") from exc
    if not skills:
        raise HTTPException(status_code=400, detail="Add at least one skill")
    mismatch = _as_bool(demo_mismatch)
    video_name = _store_video(video, mismatch)
    job = Job(
        employer_id=user.id,
        title=title.strip(),
        sector=sector,
        district_id=district_id,
        description=description.strip(),
        salary_min=salary_min,
        salary_max=salary_max,
        hike_pct=hike_pct,
        perks=perks.strip(),
        negotiation_low=negotiation_low or salary_min,
        negotiation_high=negotiation_high or salary_max,
        open_to_freshers=_as_bool(open_to_freshers),
        will_train=_as_bool(will_train),
        openings=max(1, openings),
        shift=shift,
        night_required=_as_bool(night_required),
        physical=physical,
        setting=setting,
        lodging_provided=_as_bool(lodging_provided),
        supervision=supervision,
        team_size=team_size,
        video_path=video_name,
        status="open",
        created_week=get_clock(db).week,
    )
    db.add(job)
    db.flush()
    for item in skills:
        if item["code"] not in TAXONOMY_BY_CODE:
            raise HTTPException(status_code=400, detail=f"Unknown skill {item['code']}")
        db.add(JobSkill(job_id=job.id, code=item["code"], min_level=int(item.get("min_level", 2)), required=bool(item.get("required", True))))
    db.flush()
    db.refresh(job)
    claims = claims_from_job(
        {
            "setting": job.setting,
            "team_size": job.team_size,
            "physical": job.physical,
            "night_required": job.night_required,
            "lodging_provided": job.lodging_provided,
            "sector": job.sector,
        }
    )
    report = run_agent(
        db,
        "listing_verification",
        {
            "claims": claims,
            "video_path": str(UPLOAD_DIR / video_name) if video_name else "",
            "mismatch": mismatch,
        },
    )
    job.video_tags_json = json.dumps(report.get("tags", {}))
    job.verification_status = report["status"]
    job.verification_report_json = json.dumps(report)
    job.verification_source = report.get("source", "mock-tags")
    alpha, beta = apply_listing(profile.trust_alpha, profile.trust_beta, report["status"] == "passed")
    profile.trust_alpha = alpha
    profile.trust_beta = beta
    profile.trust_score = trust_score(alpha, beta)
    db.commit()
    clock = get_clock(db)
    if report["status"] == "passed":
        matching = run_matching(db, week=clock.week)
        log_result(db, "matching", {"job_id": job.id}, matching)
    else:
        matching = {"skipped": True, "reason": "flagged listings stay off the seeker feed"}
    job = db.scalar(select(Job).options(selectinload(Job.skills)).where(Job.id == job.id))
    return {"job": job_brief(job), "verification": report, "matching": matching, "label": report.get("label", "mock-tags")}


@router.get("/employers/jobs/{job_id}/candidates")
def candidates(job_id: int, user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "employer")
    job = db.scalar(select(Job).where(Job.id == job_id, Job.employer_id == user.id))
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    from app.agents.consent import employer_card

    cards = []
    matches = db.scalars(select(Match).where(Match.job_id == job.id)).all()
    for match in matches:
        seeker_user = db.get(User, match.seeker_id)
        profile = db.scalar(
            select(SeekerProfile).options(selectinload(SeekerProfile.skills)).where(SeekerProfile.user_id == match.seeker_id)
        )
        if seeker_user is None or profile is None:
            continue
        skills = [
            {
                "code": item.code,
                "level": item.level,
                "title_en": TAXONOMY_BY_CODE.get(item.code, {}).get("title_en", item.code),
                "title_ta": TAXONOMY_BY_CODE.get(item.code, {}).get("title_ta", item.code),
            }
            for item in profile.skills
        ]
        cards.append(employer_card(match, seeker_user, profile, skills))
    cards.sort(key=lambda item: item["fits"]["final"], reverse=True)
    return {"job": {"id": job.id, "title": job.title, "verification_status": job.verification_status}, "candidates": cards}


@router.post("/employers/matches/{match_id}/interest")
def send_interest(match_id: int, user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "employer")
    match, job = owned_match(db, user, match_id)
    if match.status not in ("allocated", "interested"):
        raise HTTPException(status_code=400, detail="Interest was already answered")
    match.status = "interested"
    from app.agents.consent import record

    record(db.add, match, match.seeker_id, user.id, "interest")
    db.commit()
    run_agent(db, "consent_broker", {"action": "interest", "match_id": match.id})
    return {"status": match.status}


@router.post("/employers/matches/{match_id}/hire")
def hire(match_id: int, user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "employer")
    match, job = owned_match(db, user, match_id)
    if match.status != "accepted":
        raise HTTPException(status_code=400, detail="The seeker has not accepted yet, so details stay hidden and you cannot mark a hire")
    if db.scalar(select(Hire).where(Hire.match_id == match.id)):
        raise HTTPException(status_code=400, detail="Already marked hired")
    clock = get_clock(db)
    match.status = "hired"
    job.filled += 1
    row = Hire(
        match_id=match.id,
        seeker_id=match.seeker_id,
        job_id=job.id,
        employer_id=user.id,
        week_hired=clock.week,
        active=True,
    )
    db.add(row)
    profile = db.get(SeekerProfile, match.seeker_id)
    if profile:
        mark_hired_badge(profile)
    db.commit()
    return {"hire_id": row.id, "status": "hired", "week": clock.week}


@router.get("/employers/hires")
def employer_hires(user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "employer")
    return {"hires": _hire_rows(db, employer_id=user.id, viewer="employer"), "clock": _clock(db)}


@router.post("/employers/feedback")
def employer_feedback(body: FeedbackIn, user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "employer")
    return _save_feedback(db, user, body, "employer")


@router.get("/officials/overview")
def overview(user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "official")
    seekers = db.scalars(select(SeekerProfile)).all()
    jobs = db.scalars(select(Job).options(selectinload(Job.employer))).all()
    hires = db.scalars(select(Hire)).all()
    matches = db.scalars(select(Match)).all()
    first_match = {}
    for match in matches:
        first_match[match.seeker_id] = min(first_match.get(match.seeker_id, match.week), match.week)
    hire_rows = []
    for hire in hires:
        profile = db.get(SeekerProfile, hire.seeker_id)
        hire_rows.append({"was_first_time": bool(profile and not profile.hired_before)})
    snapshot = live_fairness_snapshot(
        [item.exposure for item in seekers],
        hire_rows,
        list(first_match.values()),
    )
    by_district = []
    for district in DISTRICTS:
        people = [item for item in seekers if item.district_id == district["id"]]
        local_jobs = [item for item in jobs if item.district_id == district["id"]]
        exposures = [item.exposure for item in people]
        by_district.append(
            {
                "id": district["id"],
                "name_en": district["name_en"],
                "name_ta": district["name_ta"],
                "seekers": len(people),
                "jobs": len(local_jobs),
                "mean_exposure": round(sum(exposures) / len(exposures), 2) if exposures else 0,
                "zero_exposure": sum(1 for value in exposures if value == 0),
            }
        )
    flagged = []
    for job in jobs:
        if job.verification_status == "flagged":
            employer = job.employer
            flagged.append(
                {
                    "job_id": job.id,
                    "title": job.title,
                    "company": employer.company_name if employer else "",
                    "district_id": job.district_id,
                    "report": load_json(job.verification_report_json, {}),
                    "source": job.verification_source,
                }
            )
    latest = db.scalar(select(SimulationReport).order_by(SimulationReport.id.desc()))
    return {
        "label": "SIMULATED POPULATION",
        "clock": _clock(db),
        "counts": {
            "seekers": len(seekers),
            "jobs": len(jobs),
            "open_jobs": sum(1 for job in jobs if job.status == "open" and job.verification_status == "passed"),
            "flagged": len(flagged),
            "hires": len(hires),
            "matches": len(matches),
        },
        "fairness": snapshot,
        "districts": by_district,
        "flagged_listings": flagged,
        "latest_simulation": load_json(latest.report_json, None) if latest else None,
    }


@router.post("/officials/matching/run")
def officials_match(user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "official")
    clock = get_clock(db)
    result = run_agent(db, "matching", {"week": clock.week})
    return result


@router.post("/officials/clock/day")
def clock_day(user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "official")
    clock = advance_day(db)
    return {"week": clock.week, "day": clock.day, "label": "SIMULATED TIME"}


@router.post("/officials/clock/week")
def clock_week(user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "official")
    clock = advance_week(db)
    return {"week": clock.week, "day": clock.day, "label": "SIMULATED TIME"}


@router.post("/officials/simulate")
def simulate(user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "official")
    report = run_agent(db, "fairness_auditor", {"seed": 7})
    db.add(SimulationReport(report_json=json.dumps(report)))
    db.commit()
    return report


@router.get("/agents/runs")
def agent_runs(user: User = Depends(current_user), db: Session = Depends(_db)):
    require_role(user, "official")
    from app.models import AgentRun

    rows = db.scalars(select(AgentRun).order_by(AgentRun.id.desc()).limit(40)).all()
    return {
        "runs": [
            {
                "id": row.id,
                "agent": row.agent,
                "used_llm": row.used_llm,
                "created_at": row.created_at.isoformat(),
                "result": load_json(row.result_json, {}),
            }
            for row in rows
        ]
    }


@router.get("/files/{name}")
def download(name: str):
    safe = Path(name).name
    path = UPLOAD_DIR / safe
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not stored")
    return FileResponse(path)


def _as_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _phone(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) < 10:
        raise HTTPException(status_code=400, detail="Enter a 10-digit mobile number")
    return digits[-10:]


def _clock(db: Session) -> dict:
    clock = get_clock(db)
    return {"week": clock.week, "day": clock.day, "label": "SIMULATED TIME"}


def _reason_seeker(profile: SeekerProfile) -> dict:
    from app.scoring.glicko import skill_band as band

    return {
        "skill_band": band(profile.skill_mu, profile.skill_rd),
        "skill_rd": profile.skill_rd,
        "potential_velocity": profile.potential_velocity,
    }


def _reason_skills(profile: SeekerProfile) -> list[dict]:
    return [{"code": item.code, "level": item.level} for item in profile.skills]


def _reason_answers(profile: SeekerProfile) -> list[dict]:
    return [{"question_id": item.question_id, "rubric_score": item.rubric_score} for item in profile.answers]


def _store_video(upload: UploadFile | None, mismatch: bool) -> str:
    stamp = secrets.token_hex(4)
    name = f"upload-{stamp}.mp4"
    target = UPLOAD_DIR / name
    if upload is not None and upload.filename:
        data = upload.file.read()
        if len(data) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Video must be under 20 MB")
        target.write_bytes(data)
    else:
        sample = next(iter(UPLOAD_DIR.glob("*.mp4")), None)
        if sample and sample.stat().st_size > 32:
            shutil.copy(sample, target)
        else:
            target.write_bytes(b"KAAMSETU-PLACEHOLDER-VIDEO")
    if mismatch:
        # The checker reads tags, not the pixels, unless a vision key is configured.
        note = UPLOAD_DIR / f"{target.stem}.note"
        note.write_text("demo_mismatch")
    return target.name


def _save_feedback(db: Session, user: User, body: FeedbackIn, role: str) -> dict:
    hire = db.get(Hire, body.hire_id)
    if hire is None:
        raise HTTPException(status_code=404, detail="Hire not found")
    if role == "seeker" and hire.seeker_id != user.id:
        raise HTTPException(status_code=403, detail="Not your hire")
    if role == "employer" and hire.employer_id != user.id:
        raise HTTPException(status_code=403, detail="Not your hire")
    clock = get_clock(db)
    if body.week < hire.week_hired or body.week > clock.week:
        raise HTTPException(status_code=400, detail="That checkpoint week is not open")
    row = submit_feedback(db, hire, role, body.rating, body.comment.strip(), body.week)
    sibling = db.scalars(select(Feedback).where(Feedback.hire_id == hire.id, Feedback.week == body.week)).all()
    revealed = all(item.revealed for item in sibling) and len(sibling) >= 2
    run_agent(
        db,
        "feedback_retention",
        {
            "hire_id": hire.id,
            "week": body.week,
            "revealed": revealed,
            "scores_applied": row.scores_applied,
        },
    )
    return {"id": row.id, "revealed": row.revealed, "scores_applied": row.scores_applied, "week": row.week}


def _hire_rows(db: Session, viewer: str, seeker_id: int | None = None, employer_id: int | None = None) -> list[dict]:
    query = select(Hire)
    if seeker_id is not None:
        query = query.where(Hire.seeker_id == seeker_id)
    if employer_id is not None:
        query = query.where(Hire.employer_id == employer_id)
    rows = []
    for hire in db.scalars(query).all():
        job = db.get(Job, hire.job_id)
        seeker = db.get(User, hire.seeker_id)
        employer = db.get(EmployerProfile, hire.employer_id)
        feedback = db.scalars(select(Feedback).where(Feedback.hire_id == hire.id)).all()
        visible = []
        for item in feedback:
            entry = {"week": item.week, "author_role": item.author_role, "revealed": item.revealed}
            if item.author_role == viewer or item.revealed:
                entry["rating"] = item.rating
                entry["comment"] = item.comment
            else:
                entry["hidden"] = True
            visible.append(entry)
        rows.append(
            {
                "id": hire.id,
                "week_hired": hire.week_hired,
                "active": hire.active,
                "job_title": job.title if job else "",
                "company": employer.company_name if employer else "",
                "seeker_name": seeker.name if seeker and (viewer == "employer" or viewer == "seeker") else "Candidate",
                "feedback": visible,
            }
        )
    return rows
