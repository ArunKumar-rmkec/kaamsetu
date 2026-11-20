"""Optional LLM calls. Used only to extract or phrase. Scoring never reads the result as a decision."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, OPENAI_VISION_MODEL


def llm_configured() -> bool:
    return bool(OPENAI_API_KEY)


def complete_json(system: str, user: str, timeout: float = 25.0) -> dict[str, Any] | None:
    """Ask for a JSON object. Returns None on any failure so callers keep the deterministic path."""
    if not OPENAI_API_KEY:
        return None
    body = {
        "model": OPENAI_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    return _post(body, timeout)


def complete_vision_json(system: str, user_text: str, image_data_urls: list[str], timeout: float = 40.0) -> dict[str, Any] | None:
    if not OPENAI_API_KEY or not image_data_urls:
        return None
    content: list[dict] = [{"type": "text", "text": user_text}]
    for url in image_data_urls[:3]:
        content.append({"type": "image_url", "image_url": {"url": url}})
    body = {
        "model": OPENAI_VISION_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
    }
    return _post(body, timeout)


def _post(body: dict, timeout: float) -> dict[str, Any] | None:
    try:
        response = httpx.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json=body,
            timeout=timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None
