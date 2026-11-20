"""Runtime configuration. Every secret has a no-key fallback."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
UPLOAD_DIR = ROOT / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.environ.get(
    "KAAMSETU_DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'kaamsetu.sqlite'}",
)

# Universal mock OTP. No SMS is sent.
MOCK_OTP = os.environ.get("KAAMSETU_MOCK_OTP", "123456")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_VISION_MODEL = os.environ.get("OPENAI_VISION_MODEL", OPENAI_MODEL)

# Allocation parameters (see docs/TECHNICAL_REPORT.md).
SEEKER_CAP = int(os.environ.get("KAAMSETU_SEEKER_CAP", "3"))
FAIR_UNCERTAINTY_MAX = float(os.environ.get("KAAMSETU_FAIR_UNCERTAINTY_MAX", "0.08"))
FAIR_EXPOSURE_MAX = float(os.environ.get("KAAMSETU_FAIR_EXPOSURE_MAX", "0.10"))
FAIR_POTENTIAL_MAX = float(os.environ.get("KAAMSETU_FAIR_POTENTIAL_MAX", "0.12"))
FAIR_FIRST_TIME = float(os.environ.get("KAAMSETU_FAIR_FIRST_TIME", "0.04"))

GLICKO_C = float(os.environ.get("KAAMSETU_GLICKO_C", "30"))
GLICKO_RD_MAX = float(os.environ.get("KAAMSETU_GLICKO_RD_MAX", "350"))
TRUST_DECAY_LAMBDA = float(os.environ.get("KAAMSETU_TRUST_DECAY", "0.15"))

HOST = os.environ.get("KAAMSETU_HOST", "0.0.0.0")
PORT = int(os.environ.get("KAAMSETU_PORT", "8421"))
