"""Simulated API Setu. No government endpoint is called. Rules are canned and documented in the UI."""

from __future__ import annotations

import re

from app.scoring.trust import trust_band, trust_score, verification_prior

# Demo patterns. A value that matches the shape passes, with one deliberate fail suffix.
_GST = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")
_UDYAM = re.compile(r"^UDYAM-[A-Z]{2}-\d{2}-\d{7}$")
_EPFO = re.compile(r"^[A-Z]{2}/[A-Z]{3}/\d{5,7}$")


def verify(payload: dict) -> dict:
    aadhaar = re.sub(r"\s+", "", payload.get("aadhaar", ""))
    gstin = payload.get("gstin", "").strip().upper()
    udyam = payload.get("udyam", "").strip().upper()
    epfo = payload.get("epfo_id", "").strip().upper()

    aadhaar_ok = len(aadhaar) == 12 and aadhaar.isdigit() and not aadhaar.startswith(("0", "9"))
    gst_ok = bool(_GST.match(gstin)) and not gstin.endswith("Z")
    # The GST regex already requires a Z in the body. The fail demo ends with ZZ,
    # which fails the regex. Keep the endswith check as a second, explicit gate
    # for inputs that somehow match a looser form. Re-evaluate: our regex ends with
    # Z[0-9A-Z], so a normal GSTIN does not end with Z unless the check character is Z.
    # Demo fail value 33AABCU9603R1ZZ ends with Z and has 16 chars, so regex fails.
    # Do not double-penalise a valid check character of Z. Drop the endswith test.
    gst_ok = bool(_GST.match(gstin)) and not gstin.endswith("ZZ")
    udyam_ok = bool(_UDYAM.match(udyam))
    epfo_ok = bool(_EPFO.match(epfo))

    checks = {
        "provider": "API Setu",
        "mode": "SIMULATED",
        "disclaimer": "Canned results. No Aadhaar, GST, Udyam, or EPFO system was contacted.",
        "aadhaar_ekyc": {
            "passed": aadhaar_ok,
            "masked": _mask_aadhaar(aadhaar),
            "name_match": "Y" if aadhaar_ok else "N",
            "rule": "12 digits, not starting with 0 or 9",
        },
        "gst": {
            "passed": gst_ok,
            "value": gstin,
            "status": "Active" if gst_ok else "Not found",
            "rule": "15-character GSTIN. The demo fail value ends with ZZ.",
        },
        "udyam": {
            "passed": udyam_ok,
            "value": udyam,
            "status": "Registered" if udyam_ok else "Not found",
            "rule": "UDYAM-TN-07-0012345 shape",
        },
        "epfo": {
            "passed": epfo_ok,
            "value": epfo,
            "status": "Registered" if epfo_ok else "Not found",
            "rule": "CB/CBE/1234567 shape",
        },
    }
    alpha, beta = verification_prior(aadhaar_ok, gst_ok, udyam_ok, epfo_ok)
    checks["passed_count"] = sum(1 for key in ("aadhaar_ekyc", "gst", "udyam", "epfo") if checks[key]["passed"])
    checks["trust_alpha0"] = alpha
    checks["trust_beta0"] = beta
    checks["trust_score"] = trust_score(alpha, beta)
    checks["trust_band"] = trust_band(checks["trust_score"])
    checks["verified"] = checks["passed_count"] >= 2
    return checks


def _mask_aadhaar(value: str) -> str:
    if len(value) < 4:
        return "XXXX-XXXX-XXXX"
    return f"XXXX-XXXX-{value[-4:]}"
