"""Reason strings in English and Tamil. Codes are stable; copy is a template, not a model judgement."""

from __future__ import annotations

from app.catalog import TAXONOMY_BY_CODE


def match_reasons(row: dict, skill_titles: dict[str, str] | None = None) -> list[dict]:
    """Pick up to three reasons. A fairness term is kept when it materially moved the score."""
    titles = skill_titles or {}
    parts: list[tuple[float, dict]] = []
    skill_name = titles.get(row.get("top_skill_code", ""), row.get("top_skill_name") or "this skill")
    if row.get("skill_fit", 0) >= 0.55:
        parts.append(
            (
                0.40 * row["skill_fit"],
                _reason(
                    "skill_overlap",
                    f"Skill overlap is strong on {skill_name} (your level {row.get('top_skill_have', '–')} / asked {row.get('top_skill_need', '–')}).",
                    f"{skill_name} திறன் பொருத்தம் நல்லது (உங்கள் நிலை {row.get('top_skill_have', '–')} / கேட்கப்பட்டது {row.get('top_skill_need', '–')}).",
                ),
            )
        )
    if row.get("env_fit", 0) >= 0.6:
        parts.append(
            (
                0.25 * row["env_fit"],
                _reason(
                    "env_fit",
                    "Shift, workplace setting, travel, and team size line up with the preferences on your profile.",
                    "ஷிப்ட், பணிச்சூழல், பயணம், குழு அளவு ஆகியவை உங்கள் விருப்பத்துடன் பொருந்துகின்றன.",
                ),
            )
        )
    if row.get("pay_fit", 0) >= 0.75:
        parts.append(
            (
                0.20 * row["pay_fit"],
                _reason(
                    "pay_fit",
                    "The offered pay meets, or sits inside, the wage and negotiation range you entered.",
                    "வழங்கும் ஊதியம் நீங்கள் குறித்த ஊதியம் அல்லது பேச்சுவார்த்தை வரம்புக்குள் உள்ளது.",
                ),
            )
        )
    if row.get("reliability", 0) >= 0.45:
        parts.append(
            (
                0.15 * row["reliability"],
                _reason(
                    "reliability",
                    "Check-ins and a tightening skill rating make this a steadier recommendation.",
                    "தினசரி பதிவுகளும் நிலையான திறன் மதிப்பீடும் இந்த பரிந்துரையை உறுதிப்படுத்துகின்றன.",
                ),
            )
        )
    fairness_bits = [
        (
            row.get("fair_potential", 0),
            _reason(
                "fair_potential",
                "This employer will train, so your potential score lifted the match. Jobs that will not train do not get this lift.",
                "இந்த முதலாளி பயிற்சி தருவார், அதனால் உங்கள் ஆற்றல் மதிப்பெண் பொருத்தத்தை உயர்த்தியது. பயிற்சி இல்லாத வேலைகளுக்கு இந்த உயர்வு இல்லை.",
            ),
        ),
        (
            row.get("fair_exposure", 0),
            _reason(
                "fair_exposure",
                "You have been shown fewer openings than the district median, so an exposure adjustment was added.",
                "மாவட்ட சராசரியை விட குறைவான வாய்ப்புகளே உங்களுக்கு காட்டப்பட்டுள்ளன, அதனால் ஒரு வாய்ப்பு சரிசெய்தல் சேர்க்கப்பட்டது.",
            ),
        ),
        (
            row.get("fair_first", 0),
            _reason(
                "fair_first",
                "A first-job adjustment was added so a first chance is not crowded out.",
                "முதல் வேலை வாய்ப்பு ஒதுங்கிப் போகாமல் இருக்க ஒரு சரிசெய்தல் சேர்க்கப்பட்டது.",
            ),
        ),
        (
            row.get("fair_uncertainty", 0),
            _reason(
                "fair_uncertainty",
                "Your skill rating is still uncertain, so you are not buried while the evidence is thin.",
                "உங்கள் திறன் மதிப்பீடு இன்னும் உறுதியாகவில்லை. ஆதாரம் குறைவாக இருக்கும்போது நீங்கள் கீழே தள்ளப்பட மாட்டீர்கள்.",
            ),
        ),
    ]
    for weight, reason in fairness_bits:
        if weight >= 0.015:
            parts.append((weight, reason))
    parts.sort(key=lambda item: item[0], reverse=True)
    chosen = [reason for _, reason in parts[:3]]
    if not chosen:
        chosen.append(
            _reason(
                "available",
                "This opening cleared the district, travel, and shift filters.",
                "இந்த வேலை மாவட்டம், பயணம், ஷிப்ட் வடிகட்டிகளைக் கடந்தது.",
            )
        )
    return chosen


def profile_reasons(seeker: dict, skills: list[dict], answers: list[dict]) -> dict:
    """Top reasons for the two bands shown on the profile."""
    skill_bits: list[tuple[float, dict]] = []
    if skills:
        best = max(skills, key=lambda item: item["level"])
        title = TAXONOMY_BY_CODE.get(best["code"], {}).get("title_en", best["code"])
        title_ta = TAXONOMY_BY_CODE.get(best["code"], {}).get("title_ta", best["code"])
        skill_bits.append(
            (
                best["level"],
                _reason(
                    "profile_skill",
                    f"Strongest declared skill is {title} at level {best['level']} of 5.",
                    f"அதிகமாக குறித்த திறன் {title_ta}, நிலை {best['level']} / 5.",
                ),
            )
        )
    band = seeker.get("skill_band")
    if band == "High":
        skill_bits.append((4, _reason("profile_mu_high", "The conservative skill rating (rating minus uncertainty) sits in the High band.", "திறன் மதிப்பீடும் அதன் நிச்சயமின்மையும் சேர்த்து உயர் பட்டையில் உள்ளன.")))
    elif seeker.get("skill_rd", 350) >= 250:
        skill_bits.append((3, _reason("profile_rd", "The rating deviation is still wide, so the band stays cautious until a workplace rating arrives.", "மதிப்பீட்டு விலகல் இன்னும் அகலம். பணிமனை கருத்து வரும் வரை பட்டை எச்சரிக்கையாக இருக்கும்.")))
    else:
        skill_bits.append((2, _reason("profile_mu_mid", "The skill rating reflects declared levels plus any checkpoint ratings so far.", "திறன் மதிப்பீடு நீங்கள் குறித்த நிலைகளையும் இதுவரை வந்த கருத்துகளையும் சேர்த்தது.")))
    skill_bits.append((1, _reason("profile_skill_count", f"{len(skills)} skill code(s) are on the profile.", f"சுயவிவரத்தில் {len(skills)} திறன் குறியீடுகள் உள்ளன.")))

    answer_bits: list[tuple[float, dict]] = []
    themes = {
        "safety_stop": ("You described stopping and telling someone when a machine fails.", "இயந்திரம் நிற்கும்போது நிறுத்தி யாரிடமாவது சொல்வதைக் குறிப்பிட்டீர்கள்."),
        "public_correction": ("You described staying calm and learning from a public correction.", "பொதுவான திருத்தத்தை அமைதியாக ஏற்றுக் கற்றுக்கொள்வதைக் குறிப்பிட்டீர்கள்."),
        "family_overtime": ("You described telling the supervisor and planning around a family need.", "குடும்பத் தேவையை மேற்பார்வையாளரிடம் சொல்லி திட்டமிடுவதைக் குறிப்பிட்டீர்கள்."),
        "teammate_behind": ("You described helping a teammate when the line is behind.", "வரிசை பின்தங்கும்போது குழு உறுப்பினருக்கு உதவுவதைக் குறிப்பிட்டீர்கள்."),
        "safety_speak": ("You described speaking up about a safety problem.", "பாதுகாப்பு சிக்கலைத் தெரிவிப்பதைக் குறிப்பிட்டீர்கள்."),
        "learned_without_class": ("You described practicing a skill outside a formal class.", "வகுப்புக்கு வெளியே ஒரு திறனைப் பயின்றதைக் குறிப்பிட்டீர்கள்."),
    }
    for answer in answers:
        en, ta = themes.get(answer["question_id"], ("A situational answer is on file.", "ஒரு சூழல் பதில் பதிவாகியுள்ளது."))
        answer_bits.append((answer.get("rubric_score", 0), _reason(f"assess_{answer['question_id']}", en, ta)))
    if not answer_bits:
        answer_bits.append((0, _reason("assess_missing", "The situational questions are not finished, so potential is still a placeholder.", "சூழல் கேள்விகள் முடியவில்லை, ஆற்றல் மதிப்பெண் இன்னும் இடம்பிடிப்பு.")))
    if seeker.get("potential_velocity", 0) > 0.4:
        answer_bits.append((4, _reason("potential_trend", "Weekly checkpoints are trending up.", "வாராந்திர கருத்துகள் மேல்நோக்கி உள்ளன.")))

    skill_bits.sort(key=lambda item: item[0], reverse=True)
    answer_bits.sort(key=lambda item: item[0], reverse=True)
    return {
        "skill": [reason for _, reason in skill_bits[:3]],
        "potential": [reason for _, reason in answer_bits[:3]],
    }


def trust_reasons(employer: dict) -> list[dict]:
    verification = employer.get("verification") or {}
    bits: list[tuple[float, dict]] = []
    checks = [
        ("aadhaar_ekyc", "Aadhaar e-KYC", "ஆதார் இ-கேஒய்சி", 2.0),
        ("gst", "GST", "ஜிஎஸ்டி", 2.0),
        ("udyam", "Udyam", "உத்யம்", 1.5),
        ("epfo", "EPFO", "இபிஎஃப்ஓ", 1.5),
    ]
    for key, label, label_ta, weight in checks:
        item = verification.get(key) or {}
        if item.get("passed"):
            bits.append((weight, _reason(f"trust_{key}", f"Simulated {label} check passed.", f"உருவக {label_ta} சரிபார்ப்பு தேர்ச்சியடைந்தது.")))
        elif item:
            bits.append((weight, _reason(f"trust_{key}_fail", f"Simulated {label} check did not pass.", f"உருவக {label_ta} சரிபார்ப்பு தேறவில்லை.")))
    flagged = employer.get("flagged_listings", 0)
    passed = employer.get("passed_listings", 0)
    if passed:
        bits.append((1.2, _reason("trust_listing", f"{passed} workplace listing(s) passed the consistency check.", f"{passed} பணிமனை பட்டியல் சீரானது எனச் சரிபார்க்கப்பட்டது.")))
    if flagged:
        bits.append((1.4, _reason("trust_flag", f"{flagged} listing(s) were flagged because the video tags disagree with the job text.", f"{flagged} பட்டியல் குறிக்கப்பட்டது. காணொலி குறிச்சொற்கள் வேலை விவரத்துடன் முரண்படுகின்றன.")))
    score = employer.get("trust_score", 50)
    bits.append((0.5, _reason("trust_score", f"Trust is the mean of a Beta posterior, currently {score}.", f"நம்பிக்கை மதிப்பெண் ஒரு பீட்டா பரவலின் சராசரி, இப்போது {score}.")))
    bits.sort(key=lambda item: item[0], reverse=True)
    return [reason for _, reason in bits[:3]]


def _reason(code: str, en: str, ta: str) -> dict:
    return {"code": code, "en": en, "ta": ta}
