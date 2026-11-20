"""Two-state Kalman filter for a seeker's potential level and weekly trend.

State x = [level, velocity]. Level is 0–100. Velocity is points per week.
Measurement is a weekly performance observation. Prediction runs on each
simulated week advance; the update runs when double-blind feedback is revealed.
"""

from __future__ import annotations

# Process noise and measurement noise are prototype constants, not learned.
Q_LEVEL = 1.0
Q_VELOCITY = 0.25
R_MEAS = 16.0  # σ = 4 points on a 0–100 observation
VELOCITY_LIMIT = 5.0


def initial_covariance() -> tuple[float, float, float]:
    """P = [[36, 0], [0, 1]] returned as (p00, p01, p11)."""
    return 36.0, 0.0, 1.0


def predict(
    level: float,
    velocity: float,
    p00: float,
    p01: float,
    p11: float,
) -> tuple[float, float, float, float, float]:
    """Time update for dt = 1 week. F = [[1, 1], [0, 1]]."""
    level_p = level + velocity
    velocity_p = velocity
    # P = F P F^T + Q
    # F P = [[p00+p01, p01+p11], [p01, p11]]
    # F P F^T = [[p00+2 p01+p11, p01+p11], [p01+p11, p11]]
    n00 = p00 + 2 * p01 + p11 + Q_LEVEL
    n01 = p01 + p11
    n11 = p11 + Q_VELOCITY
    level_p = _clamp_level(level_p)
    velocity_p = _clamp_velocity(velocity_p)
    return level_p, velocity_p, n00, n01, n11


def update(
    level: float,
    velocity: float,
    p00: float,
    p01: float,
    p11: float,
    observation: float,
) -> tuple[float, float, float, float, float]:
    """Measurement update. H = [1, 0], so only level is observed."""
    observation = _clamp_level(observation)
    # y = z - H x; S = H P H^T + R = p00 + R
    innovation = observation - level
    s = p00 + R_MEAS
    k0 = p00 / s
    k1 = p01 / s
    level_u = _clamp_level(level + k0 * innovation)
    velocity_u = _clamp_velocity(velocity + k1 * innovation)
    # Joseph-free covariance: (I - K H) P
    # I - KH = [[1-k0, 0], [-k1, 1]]
    n00 = (1 - k0) * p00
    n01 = (1 - k0) * p01
    n11 = p11 - k1 * p01
    # Numerical floor so later inversions stay sane.
    n00 = max(n00, 0.5)
    n11 = max(n11, 0.05)
    return level_u, velocity_u, n00, n01, n11


def performance_observation(stars: int, checkin_ratio: float | None) -> float:
    """Blend the employer rating with check-in consistency when check-ins exist."""
    rating_score = max(1, min(5, int(stars))) / 5.0 * 100.0
    if checkin_ratio is None:
        return rating_score
    ratio = min(1.0, max(0.0, checkin_ratio))
    return 0.75 * rating_score + 0.25 * ratio * 100.0


def potential_band(level: float) -> str:
    if level >= 75:
        return "High"
    if level >= 50:
        return "Medium"
    return "Building"


def _clamp_level(value: float) -> float:
    return max(0.0, min(100.0, value))


def _clamp_velocity(value: float) -> float:
    return max(-VELOCITY_LIMIT, min(VELOCITY_LIMIT, value))
