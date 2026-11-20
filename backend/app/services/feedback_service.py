"""Checkpoint feedback, check-ins, score updates, and badges.

Double-blind rule: a week's two ratings stay hidden until both exist. Score
updates run once, when the pair is revealed.
"""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Checkin, Clock, EmployerProfile, Feedback, Hire, Job, SeekerProfile
from app.scoring.glicko import inflate_rd, rating_to_score, role_benchmark, update as glicko_update
from app.scoring.kalman import performance_observation, predict, update as kalman_update
from app.scoring.trust import apply_feedback, decay, trust_score


def get_clock(db: Session) -> Clock:
    clock = db.get(Clock, 1)
    if clock is None:
        clock = Clock(id=1, week=1, day=1)
        db.add(clock)
        db.commit()
        db.refresh(clock)
    return clock


def advance_day(db: Session) -> Clock:
    clock = get_clock(db)
    clock.day += 1
    if clock.day > 7:
        clock.day = 1
        _advance_week_effects(db, clock)
        clock.week += 1
    db.commit()
    return clock


def advance_week(db: Session) -> Clock:
    clock = get_clock(db)
    _advance_week_effects(db, clock)
    clock.week += 1
    clock.day = 1
    db.commit()
    return clock


def _advance_week_effects(db: Session, clock: Clock) -> None:
    """One simulated week of RD inflation, potential prediction, and trust decay."""
    seekers = db.scalars(select(SeekerProfile)).all()
    for seeker in seekers:
        seeker.skill_rd = inflate_rd(seeker.skill_rd, 1)
        seeker.skill_last_week = clock.week + 1
        level, velocity, p00, p01, p11 = predict(
            seeker.potential,
            seeker.potential_velocity,
            seeker.potential_p00,
            seeker.potential_p01,
            seeker.potential_p11,
        )
        seeker.potential = round(level, 2)
        seeker.potential_velocity = round(velocity, 3)
        seeker.potential_p00 = p00
        seeker.potential_p01 = p01
        seeker.potential_p11 = p11
        if seeker.checkin_streak and clock.day >= 1:
            # A week boundary breaks a streak that had no check-in this week.
            had = db.scalar(
                select(Checkin.id).where(Checkin.seeker_id == seeker.user_id, Checkin.week == clock.week).limit(1)
            )
            if had is None:
                seeker.checkin_streak = 0
    employers = db.scalars(select(EmployerProfile)).all()
    for employer in employers:
        alpha, beta = decay(employer.trust_alpha, employer.trust_beta, employer.trust_alpha0, employer.trust_beta0)
        employer.trust_alpha = alpha
        employer.trust_beta = beta
        employer.trust_score = trust_score(alpha, beta)
    _refresh_badges(db)


def submit_feedback(db: Session, hire: Hire, role: str, rating: int, comment: str, week: int) -> Feedback:
    existing = db.scalar(
        select(Feedback).where(Feedback.hire_id == hire.id, Feedback.week == week, Feedback.author_role == role)
    )
    if existing:
        existing.rating = rating
        existing.comment = comment
        row = existing
    else:
        row = Feedback(hire_id=hire.id, week=week, author_role=role, rating=rating, comment=comment)
        db.add(row)
        db.flush()
    _maybe_reveal(db, hire, week)
    db.commit()
    db.refresh(row)
    return row


def _maybe_reveal(db: Session, hire: Hire, week: int) -> None:
    rows = db.scalars(select(Feedback).where(Feedback.hire_id == hire.id, Feedback.week == week)).all()
    by_role = {item.author_role: item for item in rows}
    if "seeker" not in by_role or "employer" not in by_role:
        return
    for item in rows:
        item.revealed = True
    if by_role["seeker"].scores_applied and by_role["employer"].scores_applied:
        return
    _apply_scores(db, hire, by_role["employer"].rating, by_role["seeker"].rating)
    for item in rows:
        item.scores_applied = True
    _refresh_badges(db)


def _apply_scores(db: Session, hire: Hire, employer_rates_seeker: int, seeker_rates_employer: int) -> None:
    seeker = db.get(SeekerProfile, hire.seeker_id)
    employer = db.get(EmployerProfile, hire.employer_id)
    job = db.scalar(select(Job).options(selectinload(Job.skills)).where(Job.id == hire.job_id))
    if seeker is None or employer is None or job is None:
        return
    required_levels = [item.min_level for item in job.skills if item.required] or [2]
    mu_opp, rd_opp = role_benchmark(max(required_levels))
    mu, rd = glicko_update(seeker.skill_mu, seeker.skill_rd, mu_opp, rd_opp, rating_to_score(employer_rates_seeker))
    seeker.skill_mu = round(mu, 2)
    seeker.skill_rd = round(rd, 2)
    checkins = db.scalars(select(Checkin).where(Checkin.seeker_id == seeker.user_id, Checkin.week == hire.week_hired)).all()
    ratio = None
    if checkins:
        good = sum(1 for item in checkins if item.mood == "good")
        ratio = good / len(checkins)
    observation = performance_observation(employer_rates_seeker, ratio)
    level, velocity, p00, p01, p11 = kalman_update(
        seeker.potential,
        seeker.potential_velocity,
        seeker.potential_p00,
        seeker.potential_p01,
        seeker.potential_p11,
        observation,
    )
    seeker.potential = round(level, 2)
    seeker.potential_velocity = round(velocity, 3)
    seeker.potential_p00 = p00
    seeker.potential_p01 = p01
    seeker.potential_p11 = p11
    alpha, beta = apply_feedback(employer.trust_alpha, employer.trust_beta, seeker_rates_employer)
    employer.trust_alpha = alpha
    employer.trust_beta = beta
    employer.trust_score = trust_score(alpha, beta)


def record_checkin(db: Session, seeker: SeekerProfile, mood: str, note: str, week: int, day: int) -> Checkin:
    existing = db.scalar(select(Checkin).where(Checkin.seeker_id == seeker.user_id, Checkin.week == week, Checkin.day == day))
    if existing:
        existing.mood = mood
        existing.note = note
        row = existing
    else:
        row = Checkin(seeker_id=seeker.user_id, week=week, day=day, mood=mood, note=note)
        db.add(row)
        seeker.checkin_total += 1
        seeker.checkin_streak += 1
    _award(seeker, "steady_presence", "Five check-ins on file.", "ஐந்து தினசரி பதிவுகள்.") if seeker.checkin_total >= 5 else None
    db.commit()
    db.refresh(row)
    return row


def award_for_events(seeker: SeekerProfile) -> None:
    if seeker.onboarding_complete:
        _award(seeker, "profile_ready", "Profile and consent are in place.", "சுயவிவரமும் ஒப்புதலும் தயார்.")
    if seeker.assessment_done:
        _award(seeker, "assessed", "Situational questions are scored.", "சூழல் கேள்விகள் மதிப்பிடப்பட்டன.")
    if seeker.exposure > 0:
        _award(seeker, "first_recommendation", "At least one opening was allocated.", "குறைந்தது ஒரு வேலை ஒதுக்கப்பட்டது.")
    if seeker.checkin_total >= 5:
        _award(seeker, "steady_presence", "Five check-ins on file.", "ஐந்து தினசரி பதிவுகள்.")
    if seeker.potential_velocity > 0.4:
        _award(seeker, "rising_potential", "Potential trend is upward.", "ஆற்றல் போக்கு மேல்நோக்கி உள்ளது.")
    if seeker.skill_mu - seeker.skill_rd >= 1550:
        _award(seeker, "trusted_skill", "Conservative skill rating is in the High band.", "எச்சரிக்கை திறன் மதிப்பீடு உயர் பட்டையில் உள்ளது.")


def mark_hired_badge(seeker: SeekerProfile) -> None:
    _award(seeker, "hired", "An employer marked a hire.", "ஒரு முதலாளி பணியமர்த்தலைப் பதிவு செய்தார்.")


def _award(seeker: SeekerProfile, code: str, en: str, ta: str) -> None:
    current = json.loads(seeker.badges_json or "[]")
    if any(item.get("code") == code for item in current):
        return
    current.append({"code": code, "en": en, "ta": ta})
    seeker.badges_json = json.dumps(current)


def _refresh_badges(db: Session) -> None:
    for seeker in db.scalars(select(SeekerProfile)).all():
        award_for_events(seeker)
