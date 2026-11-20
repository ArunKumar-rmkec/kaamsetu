"""Text intake. Voice is a browser concern; this agent answers the transcript or typed text."""

from __future__ import annotations

from app.agents.llm import complete_json, llm_configured
from app.agents.taxonomy import map_text


def reply(message: str, lang: str = "en") -> dict:
    mapped = map_text(message) if message.strip() else {"codes": [], "source": "keyword-map", "used_llm": False}
    scripted = _script(message, mapped, lang)
    used_llm = mapped.get("used_llm", False)
    text = scripted
    if llm_configured() and message.strip():
        extracted = complete_json(
            "You are KaamSetu's intake helper for a rural Tamil Nadu job seeker. "
            "Reply JSON {\"text\": \"...\"} in the requested language. "
            "Do not invent jobs, wages, or scores. If skills were mapped, mention those titles only. "
            "Keep it under 70 words.",
            f"Language: {lang}. Mapped skills: {mapped.get('codes')}. Seeker said: {message}",
        )
        if extracted and extracted.get("text"):
            text = extracted["text"]
            used_llm = True
    return {
        "reply": text,
        "mapped_skills": mapped.get("codes", []),
        "source": "llm" if used_llm else "script",
        "used_llm": used_llm,
    }


def _script(message: str, mapped: dict, lang: str) -> str:
    lowered = message.lower()
    codes = mapped.get("codes") or []
    if codes:
        titles = ", ".join(item["title_ta"] if lang == "ta" else item["title_en"] for item in codes)
        if lang == "ta":
            return f"இதை இந்த திறன் குறியீடுகளுடன் பொருத்தினேன்: {titles}. சுயவிவரத்தில் சேர்க்க விரும்பினால் திறன் பக்கத்தில் உறுதி செய்யுங்கள்."
        return f"I mapped that to {titles}. Confirm the level on your skills step if you want it saved."
    if any(word in lowered for word in ("score", "potential", "skill", "மதிப்பெண்", "திறன்")):
        if lang == "ta":
            return "திறன் மதிப்பெண் உங்கள் குறியீடுகளிலும் பணிமனை கருத்திலும் இருந்து வரும். ஆற்றல் மதிப்பெண் ஆறு சூழல் கேள்விகளில் இருந்து வரும். இரண்டையும் ஒரு விதி முடிவு செய்கிறது."
        return "Skill Score comes from your skill codes and later workplace ratings. Potential Score comes from the six situational questions. A fixed rule decides both."
    if lang == "ta":
        return "நீங்கள் செய்யும் வேலையை எளிய வார்த்தைகளில் சொல்லுங்கள். உதாரணம்: தையல் இயந்திரம், பைக் மெக்கானிக், கிடங்கில் பொதி."
    return "Tell me the work you can do, in plain words. For example: sewing machine, bike mechanic, or packing in a warehouse."
