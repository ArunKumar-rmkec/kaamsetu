"""Seed catalogue: Tamil Nadu districts and a small NCO-style skill taxonomy.

Codes follow the NCO family shape (4-digit family + dot + task) but this list is a
prototype subset, not the official NCO-2015 catalogue.
"""

from __future__ import annotations

DISTRICTS: list[dict] = [
    {"id": "coimbatore", "name_en": "Coimbatore", "name_ta": "கோயம்புத்தூர்", "lat": 11.0168, "lng": 76.9558},
    {"id": "tiruppur", "name_en": "Tiruppur", "name_ta": "திருப்பூர்", "lat": 11.1085, "lng": 77.3411},
    {"id": "erode", "name_en": "Erode", "name_ta": "ஈரோடு", "lat": 11.3410, "lng": 77.7172},
    {"id": "salem", "name_en": "Salem", "name_ta": "சேலம்", "lat": 11.6643, "lng": 78.1460},
    {"id": "namakkal", "name_en": "Namakkal", "name_ta": "நாமக்கல்", "lat": 11.2194, "lng": 78.1677},
    {"id": "trichy", "name_en": "Tiruchirappalli", "name_ta": "திருச்சிராப்பள்ளி", "lat": 10.7905, "lng": 78.7047},
    {"id": "thanjavur", "name_en": "Thanjavur", "name_ta": "தஞ்சாவூர்", "lat": 10.7870, "lng": 79.1378},
    {"id": "madurai", "name_en": "Madurai", "name_ta": "மதுரை", "lat": 9.9252, "lng": 78.1198},
    {"id": "tirunelveli", "name_en": "Tirunelveli", "name_ta": "திருநெல்வேலி", "lat": 8.7139, "lng": 77.7567},
    {"id": "vellore", "name_en": "Vellore", "name_ta": "வேலூர்", "lat": 12.9165, "lng": 79.1325},
]

TAXONOMY: list[dict] = [
    {"code": "7533.01", "title_en": "Tailor, garment", "title_ta": "தையல்காரர்", "sector": "garments"},
    {"code": "8152.02", "title_en": "Sewing machine operator", "title_ta": "தையல் இயந்திர இயக்குநர்", "sector": "garments"},
    {"code": "3139.10", "title_en": "Quality checker, garments", "title_ta": "தர சரிபார்ப்பாளர்", "sector": "garments"},
    {"code": "7223.05", "title_en": "CNC / lathe operator", "title_ta": "சிஎன்சி இயக்குநர்", "sector": "auto"},
    {"code": "7212.08", "title_en": "Welder", "title_ta": "வெல்டர்", "sector": "auto"},
    {"code": "7231.12", "title_en": "Two-wheeler mechanic", "title_ta": "இருசக்கர வாகன மெக்கானிக்", "sector": "auto"},
    {"code": "8160.20", "title_en": "Food processing helper", "title_ta": "உணவு பதப்படுத்தல் உதவியாளர்", "sector": "food"},
    {"code": "5120.15", "title_en": "Kitchen assistant", "title_ta": "சமையல் உதவியாளர்", "sector": "hospitality"},
    {"code": "5131.06", "title_en": "Housekeeping attendant", "title_ta": "வீட்டுப்பராமரிப்பு பணியாளர்", "sector": "hospitality"},
    {"code": "8322.18", "title_en": "Delivery associate", "title_ta": "விநியோக பணியாளர்", "sector": "logistics"},
    {"code": "9333.22", "title_en": "Warehouse packer", "title_ta": "கிடங்கு பொதி செய்பவர்", "sector": "logistics"},
    {"code": "7112.09", "title_en": "Mason helper", "title_ta": "கொத்தனார் உதவியாளர்", "sector": "construction"},
    {"code": "5223.04", "title_en": "Shop sales associate", "title_ta": "கடை விற்பனை பணியாளர்", "sector": "retail"},
    {"code": "5321.16", "title_en": "Patient care assistant", "title_ta": "நோயாளி பராமரிப்பு உதவியாளர்", "sector": "healthcare"},
    {"code": "8212.21", "title_en": "Electronics assembler", "title_ta": "மின்னணு பொருத்தும் பணியாளர்", "sector": "electronics"},
    {"code": "6111.30", "title_en": "Farm produce sorter", "title_ta": "விளைபொருள் பிரிப்பாளர்", "sector": "agri"},
    {"code": "3512.14", "title_en": "Data entry operator", "title_ta": "தரவு உள்ளீட்டு இயக்குநர்", "sector": "ites"},
    {"code": "3122.19", "title_en": "Junior line supervisor", "title_ta": "இளைய வரிசை மேற்பார்வையாளர்", "sector": "auto"},
]

TAXONOMY_BY_CODE = {item["code"]: item for item in TAXONOMY}
DISTRICT_BY_ID = {item["id"]: item for item in DISTRICTS}

# Free-text hints used by the taxonomy mapper. Longer phrases should win, so
# the mapper sorts by phrase length.
SKILL_HINTS: list[tuple[str, str]] = [
    ("sewing machine", "8152.02"),
    ("stitch", "7533.01"),
    ("tailor", "7533.01"),
    ("தையல்", "7533.01"),
    ("quality", "3139.10"),
    ("checker", "3139.10"),
    ("cnc", "7223.05"),
    ("lathe", "7223.05"),
    ("சிஎன்சி", "7223.05"),
    ("weld", "7212.08"),
    ("வெல்ட", "7212.08"),
    ("mechanic", "7231.12"),
    ("two wheeler", "7231.12"),
    ("bike", "7231.12"),
    ("food process", "8160.20"),
    ("kitchen", "5120.15"),
    ("cook", "5120.15"),
    ("சமையல்", "5120.15"),
    ("housekeep", "5131.06"),
    ("delivery", "8322.18"),
    ("driver", "8322.18"),
    ("விநியோக", "8322.18"),
    ("pack", "9333.22"),
    ("warehouse", "9333.22"),
    ("mason", "7112.09"),
    ("construction", "7112.09"),
    ("கொத்தனார்", "7112.09"),
    ("sales", "5223.04"),
    ("shop", "5223.04"),
    ("விற்பனை", "5223.04"),
    ("patient", "5321.16"),
    ("hospital", "5321.16"),
    ("நோயாளி", "5321.16"),
    ("electron", "8212.21"),
    ("assembl", "8212.21"),
    ("solder", "8212.21"),
    ("farm", "6111.30"),
    ("sort", "6111.30"),
    ("விளை", "6111.30"),
    ("data entry", "3512.14"),
    ("typing", "3512.14"),
    ("computer", "3512.14"),
    ("supervisor", "3122.19"),
    ("மேற்பார்வை", "3122.19"),
]

QUESTIONS: list[dict] = [
    {
        "id": "safety_stop",
        "prompt_en": "A machine you are using stops suddenly in the middle of the shift. What do you do first, and who do you tell?",
        "prompt_ta": "நீங்கள் பயன்படுத்தும் இயந்திரம் ஷிப்ட் நடுவில் திடீரென நின்றுவிட்டது. முதலில் என்ன செய்வீர்கள்? யாரிடம் சொல்வீர்கள்?",
    },
    {
        "id": "public_correction",
        "prompt_en": "Your supervisor corrects you in front of the team. What do you say and do next?",
        "prompt_ta": "உங்கள் மேற்பார்வையாளர் குழுவின் முன்னால் உங்களைத் திருத்துகிறார். அடுத்து என்ன சொல்வீர்கள், என்ன செய்வீர்கள்?",
    },
    {
        "id": "family_overtime",
        "prompt_en": "You are asked to stay for overtime, but you promised to be home for a family need. How do you decide?",
        "prompt_ta": "கூடுதல் நேரம் வேலை செய்யச் சொல்கிறார்கள், ஆனால் குடும்பத் தேவைக்காக வீட்டில் இருப்பதாக வாக்குறுதி அளித்துள்ளீர்கள். எப்படி முடிவு செய்வீர்கள்?",
    },
    {
        "id": "teammate_behind",
        "prompt_en": "The line is behind and a teammate is struggling. What do you do?",
        "prompt_ta": "பணி வரிசை பின்தங்கியுள்ளது, ஒரு குழு உறுப்பினர் சிரமப்படுகிறார். நீங்கள் என்ன செய்வீர்கள்?",
    },
    {
        "id": "safety_speak",
        "prompt_en": "You notice a safety problem no one has mentioned. What do you do?",
        "prompt_ta": "யாரும் சொல்லாத ஒரு பாதுகாப்பு சிக்கலை நீங்கள் கவனிக்கிறீர்கள். என்ன செய்வீர்கள்?",
    },
    {
        "id": "learned_without_class",
        "prompt_en": "Tell us about a skill you learned without a formal class. How did you practice?",
        "prompt_ta": "வகுப்பு இல்லாமல் நீங்கள் கற்றுக்கொண்ட ஒரு திறனைச் சொல்லுங்கள். எப்படி பயிற்சி செய்தீர்கள்?",
    },
]

SECTORS = [
    {"id": "garments", "en": "Garments", "ta": "ஆடை"},
    {"id": "auto", "en": "Auto components", "ta": "வாகன உதிரிபாகங்கள்"},
    {"id": "food", "en": "Food processing", "ta": "உணவு பதப்படுத்தல்"},
    {"id": "hospitality", "en": "Hospitality", "ta": "விருந்தோம்பல்"},
    {"id": "logistics", "en": "Logistics", "ta": "தளவாடம்"},
    {"id": "construction", "en": "Construction", "ta": "கட்டுமானம்"},
    {"id": "retail", "en": "Retail", "ta": "சில்லறை வணிகம்"},
    {"id": "healthcare", "en": "Healthcare support", "ta": "சுகாதார உதவி"},
    {"id": "electronics", "en": "Electronics assembly", "ta": "மின்னணு பொருத்துதல்"},
    {"id": "agri", "en": "Agri processing", "ta": "வேளாண் பதப்படுத்தல்"},
    {"id": "ites", "en": "Data and ITES", "ta": "தரவு பணி"},
]
