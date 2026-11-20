"""Map free text onto the seed taxonomy. The allowed code list is closed."""

from __future__ import annotations

from app.agents.llm import complete_json, llm_configured
from app.catalog import SKILL_HINTS, TAXONOMY, TAXONOMY_BY_CODE


def map_text(text: str, level: int = 2) -> dict:
    """Return {codes: [{code, level, title_en, title_ta}], source, used_llm}."""
    deterministic = _keyword_map(text, level)
    used_llm = False
    codes = deterministic
    source = "keyword-map"
    if llm_configured() and text.strip():
        allowed = ", ".join(f"{item['code']} {item['title_en']}" for item in TAXONOMY)
        extracted = complete_json(
            "You map a worker's words onto a closed skill list. Reply JSON {\"codes\": [\"7533.01\"]}. "
            "Use only codes from the list. Return an empty list if nothing fits.",
            f"Allowed codes:\n{allowed}\n\nWorker said:\n{text}",
        )
        if extracted and isinstance(extracted.get("codes"), list):
            cleaned = []
            for code in extracted["codes"]:
                if code in TAXONOMY_BY_CODE and code not in {item["code"] for item in cleaned}:
                    item = TAXONOMY_BY_CODE[code]
                    cleaned.append(
                        {"code": code, "level": level, "title_en": item["title_en"], "title_ta": item["title_ta"]}
                    )
            if cleaned:
                codes = cleaned
                source = "llm-extract-validated"
                used_llm = True
    return {"codes": codes, "source": source, "used_llm": used_llm, "input": text}


def _keyword_map(text: str, level: int) -> list[dict]:
    lowered = text.lower()
    found: list[dict] = []
    seen: set[str] = set()
    for phrase, code in sorted(SKILL_HINTS, key=lambda item: len(item[0]), reverse=True):
        if phrase in lowered and code not in seen:
            seen.add(code)
            item = TAXONOMY_BY_CODE[code]
            found.append({"code": code, "level": level, "title_en": item["title_en"], "title_ta": item["title_ta"]})
    return found
