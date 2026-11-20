"""Single dispatcher. Every agent call is logged. There is no hidden tool loop."""

from __future__ import annotations

import json
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.models import AgentRun

Handler = Callable[[dict, Session], dict]
AGENTS: dict[str, Handler] = {}


def register(name: str):
    def wrap(fn: Handler) -> Handler:
        AGENTS[name] = fn
        return fn

    return wrap


def run(db: Session, name: str, payload: dict) -> dict:
    if name not in AGENTS:
        raise KeyError(name)
    result = AGENTS[name](payload, db)
    log_result(db, name, payload, result)
    return result


def log_result(db: Session, name: str, payload: dict, result: dict) -> None:
    db.add(
        AgentRun(
            agent=name,
            payload_json=json.dumps(payload, default=str)[:4000],
            result_json=json.dumps(result, default=str)[:8000],
            used_llm=bool(result.get("used_llm")),
        )
    )
    db.commit()
