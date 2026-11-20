"""Deterministic scoring of the six situational answers. The LLM never overrides this."""

from __future__ import annotations

# Keywords are stems matched by substring, including Tamil. They are a prototype
# rubric, not a validated psychometric instrument.
QUESTION_KEYWORDS: dict[str, list[str]] = {
    "safety_stop": [
        "stop", "switch", "off", "supervisor", "report", "safe", "power", "tell", "inform",
        "நிறுத்த", "மேற்பார்", "தெரிவி", "பாதுகா", "சொல்",
    ],
    "public_correction": [
        "listen", "sorry", "improve", "calm", "thank", "learn", "again", "ask",
        "கேட்", "மன்னி", "அமைதி", "சரிசெய்", "கற்று", "நன்றி",
    ],
    "family_overtime": [
        "family", "tell", "inform", "plan", "balance", "supervisor", "agree", "home",
        "குடும்ப", "சொல்", "திட்ட", "மேற்பார்", "வீடு",
    ],
    "teammate_behind": [
        "help", "together", "share", "cover", "support", "show", "team",
        "உதவி", "சேர்ந்து", "குழு", "கற்று",
    ],
    "safety_speak": [
        "report", "stop", "supervisor", "safe", "tell", "warn", "flag",
        "தெரிவி", "நிறுத்த", "பாதுகா", "எச்சரி",
    ],
    "learned_without_class": [
        "learn", "practice", "watch", "ask", "tried", "neighbour", "repeat", "youtube", "iti",
        "கற்று", "பயிற்சி", "பார்த்த", "கேட்", "முயன்ற",
    ],
}

QUESTION_ORDER = [
    "safety_stop",
    "public_correction",
    "family_overtime",
    "teammate_behind",
    "safety_speak",
    "learned_without_class",
]


def score_answer(question_id: str, text: str) -> int:
    """Return an integer 0–5. Empty answers are 0. A short but on-theme answer can still score."""
    cleaned = (text or "").strip().lower()
    if len(cleaned) < 8:
        return 0
    hits = sum(1 for stem in QUESTION_KEYWORDS.get(question_id, []) if stem in cleaned)
    length_bonus = 1 if len(cleaned) >= 40 else 0
    if hits == 0 and length_bonus:
        return 2
    return max(1, min(5, hits + length_bonus))


def potential_from_scores(scores: list[int]) -> float:
    if not scores:
        return 0.0
    return round(100.0 * sum(scores) / (5.0 * len(scores)), 1)
