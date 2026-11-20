"""Request bodies. Responses are plain dicts built next to the route that owns them."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OtpRequest(BaseModel):
    phone: str
    role: str


class OtpVerify(BaseModel):
    phone: str
    otp: str
    role: str
    name: str = ""
    company_name: str = ""
    district_id: str = "coimbatore"


class SkillIn(BaseModel):
    code: str
    level: int = Field(ge=1, le=5)


class AnswerIn(BaseModel):
    question_id: str
    answer: str


class OnboardingIn(BaseModel):
    name: str
    district_id: str
    education: str
    gender: str
    age: int = Field(ge=16, le=60)
    years_experience: int = Field(ge=0, le=40)
    expected_wage: int = Field(ge=0, le=200000)
    shift: str
    night_ok: bool
    physical: int = Field(ge=1, le=5)
    setting: str
    lodging_needed: bool
    max_commute_km: int = Field(ge=0, le=200)
    supervision: str
    team_size: str
    consent: bool
    skills: list[SkillIn]
    free_text_skill: str = ""
    answers: list[AnswerIn]


class ConsentIn(BaseModel):
    consent: bool


class CheckinIn(BaseModel):
    mood: str
    note: str = ""


class FeedbackIn(BaseModel):
    hire_id: int
    week: int
    rating: int = Field(ge=1, le=5)
    comment: str = ""


class VerifyIn(BaseModel):
    aadhaar: str
    gstin: str
    udyam: str
    epfo_id: str


class ChatIn(BaseModel):
    message: str
    lang: str = "en"


class MapIn(BaseModel):
    text: str
    level: int = 2
