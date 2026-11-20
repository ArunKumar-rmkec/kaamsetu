"""Persistence models. JSON documents are stored as text so SQLite and Postgres share one schema."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String(20), index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    token: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    seeker: Mapped["SeekerProfile | None"] = relationship(back_populates="user", uselist=False)
    employer: Mapped["EmployerProfile | None"] = relationship(back_populates="user", uselist=False)


class SeekerProfile(Base):
    __tablename__ = "seeker_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    district_id: Mapped[str] = mapped_column(String(40), default="coimbatore")
    education: Mapped[str] = mapped_column(String(40), default="10th")
    gender: Mapped[str] = mapped_column(String(20), default="woman")
    age: Mapped[int] = mapped_column(Integer, default=21)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    expected_wage: Mapped[int] = mapped_column(Integer, default=15000)
    shift: Mapped[str] = mapped_column(String(20), default="day")
    night_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    physical: Mapped[int] = mapped_column(Integer, default=3)
    setting: Mapped[str] = mapped_column(String(20), default="indoor")
    lodging_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    max_commute_km: Mapped[int] = mapped_column(Integer, default=25)
    supervision: Mapped[str] = mapped_column(String(20), default="either")
    team_size: Mapped[str] = mapped_column(String(20), default="small")
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    skill_mu: Mapped[float] = mapped_column(Float, default=1500.0)
    skill_rd: Mapped[float] = mapped_column(Float, default=350.0)
    skill_last_week: Mapped[int] = mapped_column(Integer, default=1)
    potential: Mapped[float] = mapped_column(Float, default=0.0)
    potential_velocity: Mapped[float] = mapped_column(Float, default=0.0)
    potential_p00: Mapped[float] = mapped_column(Float, default=36.0)
    potential_p01: Mapped[float] = mapped_column(Float, default=0.0)
    potential_p11: Mapped[float] = mapped_column(Float, default=1.0)
    exposure: Mapped[int] = mapped_column(Integer, default=0)
    hired_before: Mapped[bool] = mapped_column(Boolean, default=False)
    checkin_streak: Mapped[int] = mapped_column(Integer, default=0)
    checkin_total: Mapped[int] = mapped_column(Integer, default=0)
    assessment_done: Mapped[bool] = mapped_column(Boolean, default=False)
    badges_json: Mapped[str] = mapped_column(Text, default="[]")

    user: Mapped[User] = relationship(back_populates="seeker")
    skills: Mapped[list["SeekerSkill"]] = relationship(back_populates="seeker", cascade="all, delete-orphan")
    answers: Mapped[list["AssessmentAnswer"]] = relationship(back_populates="seeker", cascade="all, delete-orphan")


class SeekerSkill(Base):
    __tablename__ = "seeker_skills"
    __table_args__ = (UniqueConstraint("user_id", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("seeker_profiles.user_id"), index=True)
    code: Mapped[str] = mapped_column(String(20))
    level: Mapped[int] = mapped_column(Integer, default=2)
    source: Mapped[str] = mapped_column(String(20), default="self")

    seeker: Mapped[SeekerProfile] = relationship(back_populates="skills")


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"
    __table_args__ = (UniqueConstraint("user_id", "question_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("seeker_profiles.user_id"), index=True)
    question_id: Mapped[str] = mapped_column(String(40))
    answer: Mapped[str] = mapped_column(Text, default="")
    rubric_score: Mapped[int] = mapped_column(Integer, default=0)

    seeker: Mapped[SeekerProfile] = relationship(back_populates="answers")


class EmployerProfile(Base):
    __tablename__ = "employer_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(160))
    district_id: Mapped[str] = mapped_column(String(40), default="coimbatore")
    gstin: Mapped[str] = mapped_column(String(20), default="")
    udyam: Mapped[str] = mapped_column(String(40), default="")
    epfo_id: Mapped[str] = mapped_column(String(40), default="")
    aadhaar_masked: Mapped[str] = mapped_column(String(20), default="")
    verification_json: Mapped[str] = mapped_column(Text, default="{}")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    trust_alpha: Mapped[float] = mapped_column(Float, default=2.0)
    trust_beta: Mapped[float] = mapped_column(Float, default=2.0)
    trust_alpha0: Mapped[float] = mapped_column(Float, default=2.0)
    trust_beta0: Mapped[float] = mapped_column(Float, default=2.0)
    trust_score: Mapped[float] = mapped_column(Float, default=50.0)

    user: Mapped[User] = relationship(back_populates="employer")
    jobs: Mapped[list["Job"]] = relationship(back_populates="employer")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("employer_profiles.user_id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    sector: Mapped[str] = mapped_column(String(40), default="garments")
    district_id: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text, default="")
    salary_min: Mapped[int] = mapped_column(Integer)
    salary_max: Mapped[int] = mapped_column(Integer)
    hike_pct: Mapped[float] = mapped_column(Float, default=0)
    perks: Mapped[str] = mapped_column(Text, default="")
    negotiation_low: Mapped[int] = mapped_column(Integer, default=0)
    negotiation_high: Mapped[int] = mapped_column(Integer, default=0)
    open_to_freshers: Mapped[bool] = mapped_column(Boolean, default=True)
    will_train: Mapped[bool] = mapped_column(Boolean, default=False)
    openings: Mapped[int] = mapped_column(Integer, default=3)
    filled: Mapped[int] = mapped_column(Integer, default=0)
    shift: Mapped[str] = mapped_column(String(20), default="day")
    night_required: Mapped[bool] = mapped_column(Boolean, default=False)
    physical: Mapped[int] = mapped_column(Integer, default=3)
    setting: Mapped[str] = mapped_column(String(20), default="indoor")
    lodging_provided: Mapped[bool] = mapped_column(Boolean, default=False)
    supervision: Mapped[str] = mapped_column(String(20), default="close")
    team_size: Mapped[str] = mapped_column(String(20), default="small")
    video_path: Mapped[str] = mapped_column(String(240), default="")
    video_tags_json: Mapped[str] = mapped_column(Text, default="{}")
    verification_status: Mapped[str] = mapped_column(String(20), default="pending")
    verification_report_json: Mapped[str] = mapped_column(Text, default="{}")
    verification_source: Mapped[str] = mapped_column(String(40), default="mock-tags")
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_week: Mapped[int] = mapped_column(Integer, default=1)

    employer: Mapped[EmployerProfile] = relationship(back_populates="jobs")
    skills: Mapped[list["JobSkill"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class JobSkill(Base):
    __tablename__ = "job_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    code: Mapped[str] = mapped_column(String(20))
    min_level: Mapped[int] = mapped_column(Integer, default=2)
    required: Mapped[bool] = mapped_column(Boolean, default=True)

    job: Mapped[Job] = relationship(back_populates="skills")


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("seeker_id", "job_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seeker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    week: Mapped[int] = mapped_column(Integer, default=1)
    skill_fit: Mapped[float] = mapped_column(Float, default=0)
    env_fit: Mapped[float] = mapped_column(Float, default=0)
    pay_fit: Mapped[float] = mapped_column(Float, default=0)
    reliability: Mapped[float] = mapped_column(Float, default=0)
    relevance: Mapped[float] = mapped_column(Float, default=0)
    fair_uncertainty: Mapped[float] = mapped_column(Float, default=0)
    fair_exposure: Mapped[float] = mapped_column(Float, default=0)
    fair_potential: Mapped[float] = mapped_column(Float, default=0)
    fair_first: Mapped[float] = mapped_column(Float, default=0)
    final_score: Mapped[float] = mapped_column(Float, default=0)
    distance_km: Mapped[float] = mapped_column(Float, default=0)
    reasons_json: Mapped[str] = mapped_column(Text, default="[]")
    # allocated → interested → accepted (revealed) → hired, or declined
    status: Mapped[str] = mapped_column(String(20), default="allocated", index=True)


class Hire(Base):
    __tablename__ = "hires"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), unique=True)
    seeker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    week_hired: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (UniqueConstraint("hire_id", "week", "author_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hire_id: Mapped[int] = mapped_column(ForeignKey("hires.id"), index=True)
    week: Mapped[int] = mapped_column(Integer)
    author_role: Mapped[str] = mapped_column(String(20))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text, default="")
    revealed: Mapped[bool] = mapped_column(Boolean, default=False)
    scores_applied: Mapped[bool] = mapped_column(Boolean, default=False)


class Checkin(Base):
    __tablename__ = "checkins"
    __table_args__ = (UniqueConstraint("seeker_id", "week", "day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seeker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    week: Mapped[int] = mapped_column(Integer)
    day: Mapped[int] = mapped_column(Integer)
    mood: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(Text, default="")


class Clock(Base):
    __tablename__ = "clock"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week: Mapped[int] = mapped_column(Integer, default=1)
    day: Mapped[int] = mapped_column(Integer, default=1)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent: Mapped[str] = mapped_column(String(40), index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    used_llm: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class SimulationReport(Base):
    __tablename__ = "simulation_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    report_json: Mapped[str] = mapped_column(Text)


class ConsentEvent(Base):
    __tablename__ = "consent_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), index=True)
    seeker_id: Mapped[int] = mapped_column(Integer)
    employer_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
