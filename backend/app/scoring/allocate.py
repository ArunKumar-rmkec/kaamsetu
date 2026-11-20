"""District allocation.

KaamSetu mode: two-phase minimum-cost flow (networkx). Phase 1 gives every
seeker who still has a free slot at most one job, before phase 2 fills each
seeker's remaining cap. Cost falls as the score rises, so minimum cost is
maximum score among maximum flows.

Ranking mode: one greedy pass. The same caps apply, but the highest scores take
a seeker's full cap before later seekers are considered. There is no min-1 phase.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable

import networkx as nx

# Final scores top out near 1.34 (relevance 1 + fairness). Stay positive.
_SCORE_OFFSET = 1.5


def allocate(
    edges: list[tuple[str, str, float]],
    job_openings: dict[str, int],
    mode: str = "kaamsetu",
    seeker_cap: int = 3,
    seeker_caps: dict[str, int] | None = None,
) -> list[tuple[str, str]]:
    """edges are (seeker_id, job_id, score). Higher score is a better match.

    seeker_caps, when set, is the remaining slot count per seeker and overrides
    the flat seeker_cap. Job openings are remaining seats.
    """

    def cap_of(seeker_id: str) -> int:
        if seeker_caps is None:
            return seeker_cap
        return max(0, int(seeker_caps.get(seeker_id, seeker_cap)))

    clean = [(s, j, float(score)) for s, j, score in edges if job_openings.get(j, 0) > 0 and cap_of(s) > 0]
    if mode == "ranking":
        return _greedy(clean, job_openings, cap_of)
    if mode != "kaamsetu":
        raise ValueError(f"unknown allocation mode: {mode}")

    phase1 = _min_cost(clean, job_openings, lambda seeker_id: 1 if cap_of(seeker_id) >= 1 else 0)
    taken = set(phase1)
    used_jobs: Counter[str] = Counter(job for _, job in phase1)
    remaining_openings = {job: max(0, seats - used_jobs[job]) for job, seats in job_openings.items()}
    phase2_edges = [
        (s, j, score) for s, j, score in clean if (s, j) not in taken and remaining_openings.get(j, 0) > 0 and cap_of(s) > 1
    ]
    phase1_seekers = {seeker for seeker, _job in phase1}

    def phase2_cap(seeker_id: str) -> int:
        used = 1 if seeker_id in phase1_seekers else 0
        return max(0, cap_of(seeker_id) - used)

    phase2 = _min_cost(phase2_edges, remaining_openings, phase2_cap)
    return phase1 + phase2


def _greedy(
    edges: list[tuple[str, str, float]],
    job_openings: dict[str, int],
    cap_of: Callable[[str], int],
) -> list[tuple[str, str]]:
    ordered = sorted(edges, key=lambda item: (-item[2], item[0], item[1]))
    seeker_count: Counter[str] = Counter()
    job_count: Counter[str] = Counter()
    chosen: list[tuple[str, str]] = []
    for seeker_id, job_id, _score in ordered:
        if seeker_count[seeker_id] >= cap_of(seeker_id):
            continue
        if job_count[job_id] >= job_openings.get(job_id, 0):
            continue
        seeker_count[seeker_id] += 1
        job_count[job_id] += 1
        chosen.append((seeker_id, job_id))
    return chosen


def _min_cost(
    edges: list[tuple[str, str, float]],
    job_openings: dict[str, int],
    cap_of: Callable[[str], int],
) -> list[tuple[str, str]]:
    if not edges:
        return []
    graph = nx.DiGraph()
    seekers: set[str] = set()
    jobs: set[str] = set()
    for seeker_id, job_id, score in edges:
        if cap_of(seeker_id) <= 0 or int(job_openings.get(job_id, 0)) <= 0:
            continue
        seekers.add(seeker_id)
        jobs.add(job_id)
        weight = int(round((_SCORE_OFFSET - score) * 1000))
        graph.add_edge(f"s:{seeker_id}", f"j:{job_id}", capacity=1, weight=max(weight, 0))
    linked_seekers = [seeker_id for seeker_id in seekers if cap_of(seeker_id) > 0]
    if not linked_seekers or not jobs:
        return []
    for seeker_id in linked_seekers:
        graph.add_edge("SRC", f"s:{seeker_id}", capacity=int(cap_of(seeker_id)), weight=0)
    for job_id in jobs:
        seats = int(job_openings.get(job_id, 0))
        if seats > 0:
            graph.add_edge(f"j:{job_id}", "SNK", capacity=seats, weight=0)
    if graph.number_of_edges() == 0:
        return []
    flow = nx.max_flow_min_cost(graph, "SRC", "SNK")
    chosen: list[tuple[str, str]] = []
    for seeker_id in linked_seekers:
        row = flow.get(f"s:{seeker_id}", {})
        for job_id in jobs:
            if row.get(f"j:{job_id}", 0) > 0:
                chosen.append((seeker_id, job_id))
    return chosen
