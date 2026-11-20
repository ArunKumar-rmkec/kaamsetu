"""Register agent entrypoints. The functions themselves live beside the rules they call."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents.assessment import assess
from app.agents.employer_verification import verify
from app.agents.intake import reply as intake_reply
from app.agents.listing import claims_from_job, compare, tags_for_upload
from app.agents.orchestrator import register
from app.agents.taxonomy import map_text
from app.services.matching_service import run_matching
from app.services.simulation import simulate_four_weeks


@register("voice_intake")
def voice_intake(payload: dict, _db: Session) -> dict:
    return intake_reply(payload.get("message", ""), payload.get("lang", "en"))


@register("taxonomy_mapper")
def taxonomy_mapper(payload: dict, _db: Session) -> dict:
    return map_text(payload.get("text", ""), int(payload.get("level", 2)))


@register("assessment")
def assessment(payload: dict, _db: Session) -> dict:
    return assess(payload.get("answers", []))


@register("employer_verification")
def employer_verification(payload: dict, _db: Session) -> dict:
    result = verify(payload)
    result["used_llm"] = False
    return result


@register("matching")
def matching(payload: dict, db: Session) -> dict:
    result = run_matching(db, week=int(payload["week"]), job_id=payload.get("job_id"))
    result["used_llm"] = False
    result["decided_by"] = "min-cost-flow"
    return result


@register("listing_verification")
def listing_verification(payload: dict, _db: Session) -> dict:
    claims = payload["claims"]
    video = payload.get("video_path")
    if payload.get("tags"):
        tags = payload["tags"]
        source = tags.get("source", "mock-tags")
        used = False
    else:
        from pathlib import Path

        path = Path(video) if video else None
        tags, source, used = tags_for_upload(path, claims, bool(payload.get("mismatch")))
    report = compare(claims, tags)
    report["source"] = source
    report["used_llm"] = used
    return report


@register("consent_broker")
def consent_broker(payload: dict, _db: Session) -> dict:
    """The route performs the write. This record is the decision trace."""
    return {
        "action": payload.get("action"),
        "match_id": payload.get("match_id"),
        "revealed": payload.get("action") == "accept",
        "used_llm": False,
        "rule": "Identity is released only after the seeker accepts the employer's interest.",
    }


@register("feedback_retention")
def feedback_retention(payload: dict, _db: Session) -> dict:
    return {
        "hire_id": payload.get("hire_id"),
        "week": payload.get("week"),
        "revealed": payload.get("revealed", False),
        "scores_applied": payload.get("scores_applied", False),
        "used_llm": False,
        "rule": "Ratings stay hidden until both sides submit. Scores move only on reveal.",
    }


@register("fairness_auditor")
def fairness_auditor(payload: dict, db: Session) -> dict:
    report = simulate_four_weeks(db, seed=int(payload.get("seed", 7)))
    report["used_llm"] = False
    return report
