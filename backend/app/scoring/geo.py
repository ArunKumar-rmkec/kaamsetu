"""District sectorisation: home district plus two nearest districts by haversine distance."""

from __future__ import annotations

import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def nearest_ids(district_id: str, districts: dict[str, dict], k: int = 2) -> list[str]:
    home = districts[district_id]
    ranked = []
    for other_id, other in districts.items():
        if other_id == district_id:
            continue
        dist = haversine_km(home["lat"], home["lng"], other["lat"], other["lng"])
        ranked.append((dist, other_id))
    ranked.sort()
    return [district_id for _, district_id in ranked[:k]]


def sector_ids(district_id: str, districts: dict[str, dict]) -> set[str]:
    """Labour-market sector = the district itself and its two nearest districts."""
    return {district_id, *nearest_ids(district_id, districts, 2)}


def commute_km(seeker_district: str, job_district: str, districts: dict[str, dict]) -> float:
    """Same-district roles use a local 8 km hop. Cross-district uses haversine city-centre distance."""
    if seeker_district == job_district:
        return 8.0
    a = districts[seeker_district]
    b = districts[job_district]
    return haversine_km(a["lat"], a["lng"], b["lat"], b["lng"])
