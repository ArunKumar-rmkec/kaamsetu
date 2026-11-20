"""Listing verification. Compare structured JD claims with video tags.

If OPENAI_API_KEY is set and ffmpeg can pull keyframes, a vision model may
extract tags. Those tags are still compared by this deterministic checker.
Otherwise tags come from a mock tag file. The report always names its source.
"""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
from pathlib import Path

from app.agents.llm import complete_vision_json, llm_configured

CLAIM_FIELDS = ("setting", "team_size", "physical", "night_required", "lodging_provided", "sector")


def claims_from_job(job: dict) -> dict:
    return {
        "setting": job.get("setting", "indoor"),
        "team_size": job.get("team_size", "small"),
        "physical": int(job.get("physical", 3)),
        "night_required": bool(job.get("night_required", False)),
        "lodging_provided": bool(job.get("lodging_provided", False)),
        "sector": job.get("sector", ""),
    }


def mock_tags(claims: dict, mismatch: bool) -> dict:
    """Deterministic stand-in for a vision tagger. A mismatch flips setting and team size."""
    tags = dict(claims)
    tags["source"] = "mock-video-tags"
    if mismatch:
        tags["setting"] = "outdoor" if claims.get("setting") != "outdoor" else "indoor"
        tags["team_size"] = "large" if claims.get("team_size") != "large" else "solo"
        tags["mismatch_injected"] = True
    else:
        tags["mismatch_injected"] = False
    return tags


def extract_keyframes(video_path: Path, dest_dir: Path) -> list[Path]:
    """Pull up to three JPEG frames. Returns [] when ffmpeg or the file fails."""
    if not video_path.exists() or shutil.which("ffmpeg") is None:
        return []
    dest_dir.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []
    for index, second in enumerate((0.4, 1.2, 2.0)):
        target = dest_dir / f"frame_{index}.jpg"
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(second),
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-q:v",
                "8",
                str(target),
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0 and target.exists() and target.stat().st_size > 0:
            frames.append(target)
    return frames


def tags_for_upload(video_path: Path | None, claims: dict, mismatch: bool) -> tuple[dict, str, bool]:
    """Return (tags, source_label, used_llm)."""
    if video_path and llm_configured():
        frames = extract_keyframes(video_path, video_path.parent / f"{video_path.stem}-frames")
        urls = [_data_url(path) for path in frames]
        if urls:
            extracted = complete_vision_json(
                "You tag a workplace video. Reply JSON with keys setting (indoor|outdoor|either), "
                "team_size (solo|small|large), physical (1-5 integer), night_required (bool), "
                "lodging_provided (bool), sector (short english word or empty).",
                "Tag only what the frames show. Use empty string or null when unsure.",
                urls,
            )
            if extracted:
                normalised = _normalise_vision(extracted)
                normalised["source"] = "openai-vision"
                return normalised, "openai-vision", True
    tags = mock_tags(claims, mismatch)
    return tags, "mock-tags", False


def compare(claims: dict, tags: dict) -> dict:
    """Flag the listing when any comparable field disagrees. Physical allows a gap of 1."""
    mismatches = []
    for field in CLAIM_FIELDS:
        if field not in tags or tags.get(field) in (None, ""):
            continue
        claim = claims.get(field)
        seen = tags.get(field)
        if field == "physical":
            try:
                if abs(int(claim) - int(seen)) > 1:
                    mismatches.append({"field": field, "claimed": claim, "seen": seen})
            except (TypeError, ValueError):
                mismatches.append({"field": field, "claimed": claim, "seen": seen})
            continue
        if str(claim) != str(seen):
            mismatches.append({"field": field, "claimed": claim, "seen": seen})
    status = "flagged" if mismatches else "passed"
    return {
        "status": status,
        "mismatches": mismatches,
        "claims": claims,
        "tags": tags,
        "label": tags.get("source", "mock-tags"),
        "summary_en": _summary(status, mismatches, "en"),
        "summary_ta": _summary(status, mismatches, "ta"),
    }


def load_tag_file(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def _summary(status: str, mismatches: list[dict], lang: str) -> str:
    if status == "passed":
        return {
            "en": "Video tags agree with the structured job fields.",
            "ta": "காணொலி குறிச்சொற்கள் வேலை விவரத்துடன் ஒத்துப்போகின்றன.",
        }[lang]
    fields = ", ".join(item["field"] for item in mismatches)
    if lang == "ta":
        return f"காணொலி குறிச்சொற்கள் இந்த புலங்களில் முரண்படுகின்றன: {fields}."
    return f"Video tags disagree on: {fields}."


def _normalise_vision(raw: dict) -> dict:
    setting = raw.get("setting") or "either"
    if setting not in ("indoor", "outdoor", "either"):
        setting = "either"
    team = raw.get("team_size") or "small"
    if team not in ("solo", "small", "large"):
        team = "small"
    try:
        physical = int(raw.get("physical") or 3)
    except (TypeError, ValueError):
        physical = 3
    return {
        "setting": setting,
        "team_size": team,
        "physical": max(1, min(5, physical)),
        "night_required": bool(raw.get("night_required")),
        "lodging_provided": bool(raw.get("lodging_provided")),
        "sector": raw.get("sector") or "",
    }


def _data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"
