"""Score situational answers with the rubric. An LLM may add a gloss; it cannot change the number."""

from __future__ import annotations

from app.agents.llm import complete_json, llm_configured
from app.scoring.kalman import potential_band
from app.scoring.rubric import potential_from_scores, score_answer


def assess(answers: list[dict]) -> dict:
    """answers: [{question_id, answer}]. Returns scores, potential, band, optional gloss."""
    scored = []
    for item in answers:
        value = score_answer(item["question_id"], item.get("answer", ""))
        scored.append({"question_id": item["question_id"], "answer": item.get("answer", ""), "rubric_score": value})
    potential = potential_from_scores([item["rubric_score"] for item in scored])
    gloss = None
    used_llm = False
    if llm_configured() and scored:
        extracted = complete_json(
            "You explain a prototype rubric result in two short sentences. Reply JSON "
            '{"gloss_en": "...", "gloss_ta": "..."}. Do not invent a different score.',
            f"Potential {potential}. Per-question scores: {scored}",
        )
        if extracted:
            gloss = {"en": extracted.get("gloss_en", ""), "ta": extracted.get("gloss_ta", "")}
            used_llm = True
    return {
        "answers": scored,
        "potential": potential,
        "band": potential_band(potential),
        "gloss": gloss,
        "used_llm": used_llm,
        "decided_by": "rubric",
    }
