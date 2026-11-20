"""Scoring and allocation tests. No database and no network."""

from __future__ import annotations

from app.scoring.allocate import allocate
from app.scoring.fairness import adjustment
from app.scoring.fit import passes_hard_filters, pay_fit, relevance, skill_fit
from app.scoring.geo import nearest_ids, sector_ids
from app.scoring.glicko import expected_score, inflate_rd, skill_band, update
from app.scoring.kalman import initial_covariance, predict, update as kalman_update
from app.scoring.metrics import gini
from app.scoring.rubric import potential_from_scores, score_answer
from app.scoring.trust import apply_feedback, decay, trust_score, verification_prior
from app.catalog import DISTRICT_BY_ID


def test_glicko_positive_result_raises_rating_and_shrinks_rd():
    mu, rd = update(1500, 200, 1500, 70, 1.0)
    assert mu > 1500
    assert rd < 200
    assert expected_score(1500, 1500, 70) == 0.5


def test_glicko_loss_lowers_rating():
    mu, _rd = update(1500, 200, 1500, 70, 0.0)
    assert mu < 1500


def test_rd_inflates_with_idle_weeks_and_caps():
    grown = inflate_rd(50, 2, c=30, rd_max=350)
    assert grown > 50
    assert inflate_rd(340, 20, c=30, rd_max=350) == 350
    assert inflate_rd(120, 0) == 120


def test_skill_band_is_conservative():
    assert skill_band(1800, 100) == "High"
    assert skill_band(1700, 310) == "Building"


def test_kalman_moves_toward_a_higher_observation_and_picks_up_velocity():
    # The first update only moves level: the prior cross-covariance is zero.
    # After one predict, level and velocity are coupled, so the next high
    # observation pulls the trend upward.
    p00, p01, p11 = initial_covariance()
    level, velocity, p00, p01, p11 = kalman_update(50, 0, p00, p01, p11, 90)
    assert level > 50
    assert velocity == 0
    level, velocity, p00, p01, p11 = predict(level, velocity, p00, p01, p11)
    _level, velocity, *_ = kalman_update(level, velocity, p00, p01, p11, 92)
    assert velocity > 0


def test_kalman_predict_carries_velocity():
    level, velocity, p00, _p01, _p11 = predict(60, 2, 10, 0, 1)
    assert level == 62
    assert velocity == 2
    assert p00 > 10


def test_trust_prior_feedback_and_decay():
    alpha, beta = verification_prior(True, True, True, True)
    weak_alpha, weak_beta = verification_prior(False, False, False, False)
    assert trust_score(alpha, beta) > trust_score(weak_alpha, weak_beta)
    boosted_alpha, boosted_beta = apply_feedback(alpha, beta, 5)
    assert trust_score(boosted_alpha, boosted_beta) > trust_score(alpha, beta)
    decayed_alpha, decayed_beta = decay(boosted_alpha, boosted_beta, alpha, beta, lam=0.15)
    assert alpha < decayed_alpha < boosted_alpha
    assert decayed_beta == beta


def test_skill_fit_and_pay_fit_bounds():
    perfect = skill_fit({"7533.01": 4}, [{"code": "7533.01", "min_level": 3, "required": True}])
    missing = skill_fit({}, [{"code": "7533.01", "min_level": 3, "required": True}])
    assert perfect == 1
    assert missing == 0
    assert pay_fit(14000, 15000, 17000, 14000, 18000, 5, True) == 1
    under = pay_fit(20000, 10000, 12000, 10000, 13000, 0, False)
    assert under < 0.8


def test_relevance_weights_sum_to_one():
    assert abs(relevance(1, 1, 1, 1) - 1) < 1e-9


def test_potential_boost_only_when_the_job_will_train():
    common = dict(rd=200, exposure=0, median_exposure=5, potential=80, first_time=True)
    trained = adjustment(will_train=True, **common)
    not_trained = adjustment(will_train=False, **common)
    assert trained["potential"] > 0
    assert not_trained["potential"] == 0
    assert trained["total"] > not_trained["total"]


def test_uncertainty_and_exposure_bonuses_move_the_right_way():
    high_rd = adjustment(350, 0, 4, 40, False, False)
    low_rd = adjustment(40, 0, 4, 40, False, False)
    assert high_rd["uncertainty"] > low_rd["uncertainty"]
    unseen = adjustment(100, 0, 6, 40, False, False)
    seen = adjustment(100, 12, 6, 40, False, False)
    assert unseen["exposure"] > seen["exposure"]
    assert seen["exposure"] == 0


def test_hard_filters_block_night_commute_and_missing_consent():
    seeker = {
        "consent": True,
        "onboarding_complete": True,
        "night_ok": False,
        "max_commute_km": 15,
    }
    job = {
        "night_required": True,
        "lodging_provided": False,
        "verification_status": "passed",
        "status": "open",
        "openings": 2,
        "filled": 0,
        "employer_verified": True,
    }
    assert passes_hard_filters(seeker, job, 8, True)[0] is False
    job["night_required"] = False
    assert passes_hard_filters(seeker, job, 40, True)[1] == "commute_blocked"
    job["lodging_provided"] = True
    assert passes_hard_filters(seeker, job, 40, True)[0] is True
    seeker["consent"] = False
    assert passes_hard_filters(seeker, job, 8, True)[1] == "no_consent"
    seeker["consent"] = True
    job["verification_status"] = "flagged"
    assert passes_hard_filters(seeker, job, 8, True)[1] == "listing_not_cleared"


def test_sector_is_home_plus_two_nearest():
    sector = sector_ids("coimbatore", DISTRICT_BY_ID)
    assert "coimbatore" in sector
    assert sector == {"coimbatore", *nearest_ids("coimbatore", DISTRICT_BY_ID, 2)}
    assert len(sector) == 3
    assert "tiruppur" in sector


def test_seeker_cap_and_job_seats():
    edges = [
        ("a", "j1", 0.9),
        ("a", "j2", 0.8),
        ("a", "j3", 0.7),
        ("a", "j4", 0.6),
    ]
    chosen = allocate(edges, {"j1": 5, "j2": 5, "j3": 5, "j4": 5}, mode="kaamsetu", seeker_cap=3)
    assert len(chosen) == 3
    assert len({job for _, job in chosen}) == 3


def test_min_one_reaches_a_seeker_that_greedy_ranking_skips():
    edges = [
        ("a", "j1", 0.95),
        ("a", "j2", 0.90),
        ("b", "j1", 0.50),
        ("b", "j2", 0.10),
        ("c", "j1", 0.40),
    ]
    openings = {"j1": 2, "j2": 1}
    ranking = allocate(edges, openings, mode="ranking", seeker_cap=3)
    fair = allocate(edges, openings, mode="kaamsetu", seeker_cap=3)
    assert {seeker for seeker, _job in ranking} == {"a", "b"}
    assert {seeker for seeker, _job in fair} == {"a", "b", "c"}
    # Nobody is assigned the same job twice, and seats hold.
    assert len(fair) == len(set(fair))
    assert sum(1 for _seeker, job in fair if job == "j1") <= 2


def test_higher_score_wins_a_single_seat():
    chosen = allocate(
        [("low", "only", 0.2), ("high", "only", 0.9)],
        {"only": 1},
        mode="kaamsetu",
        seeker_cap=1,
    )
    assert chosen == [("high", "only")]


def test_gini_is_zero_when_exposure_is_even_and_high_when_it_is_not():
    assert gini([2, 2, 2, 2]) == 0
    assert gini([0, 0, 0, 10]) > 0.5


def test_rubric_scores_a_specific_answer_and_ignores_a_blank_one():
    rich = score_answer(
        "safety_stop",
        "I switch off the power, keep people safe, and tell the supervisor.",
    )
    blank = score_answer("safety_stop", "ok")
    assert rich >= 4
    assert blank == 0
    assert potential_from_scores([5, 5, 5, 5, 5, 5]) == 100
