"""Unit tests for hip-pivot latency and execution penalty (arrival inputs)."""

import math

from src.physics.biomechanics import (
    compute_biomechanical_execution_penalty,
    compute_hip_pivot_latency,
    MIN_PLANT_FOOT_DELAY_S,
)


def test_hip_pivot_latency():
    """Verifies hip rotation latency scales monotonically with turn angle."""
    body_angle = 0.0  # Facing +X

    # Open body (within 35 deg)
    t_open = compute_hip_pivot_latency(body_angle, math.radians(20.0))
    assert t_open == MIN_PLANT_FOOT_DELAY_S

    # Moderate turn (60 deg)
    t_mid = compute_hip_pivot_latency(body_angle, math.radians(60.0))
    assert MIN_PLANT_FOOT_DELAY_S < t_mid < 0.40

    # Extreme pivot (150 deg)
    t_closed = compute_hip_pivot_latency(body_angle, math.radians(150.0))
    assert t_closed > 0.50
    assert t_closed <= 0.70

    # Monotonicity test
    assert t_open <= t_mid <= t_closed


def test_biomechanical_execution_penalty():
    """Verifies completion multiplier drops on sharp turns and weak foot."""
    body_angle = 0.0

    # Open pass strong foot
    p_open = compute_biomechanical_execution_penalty(
        body_angle, 0.0, is_weak_foot=False
    )
    assert p_open == 1.0

    # Closed pass strong foot
    p_closed = compute_biomechanical_execution_penalty(
        body_angle, math.radians(120.0), is_weak_foot=False
    )
    assert p_closed < 0.75

    # Weak foot penalty applied
    p_weak = compute_biomechanical_execution_penalty(body_angle, 0.0, is_weak_foot=True)
    assert abs(p_weak - 0.88) < 0.02
    assert p_weak < p_open
