"""Hip-pivot latency and angle utilities for arrival-race engagement pricing."""

from __future__ import annotations
import math

# Baseline biomechanical constants (Lees & Nolan 1998, Kicking Biomechanics in Soccer)
MIN_PLANT_FOOT_DELAY_S = 0.15  # Minimum time to plant non-kicking foot
MAX_HIP_PIVOT_DELAY_S = 0.70  # Full 180-degree pivot and strike delay
OPEN_HIP_THRESHOLD_RAD = math.radians(35.0)  # No swivel needed within 35 deg
RIGHT_ANGLE_HIP_RAD = math.radians(90.0)  # 90 deg half-turn


def wrap_angle_rad(angle_rad: float) -> float:
    """Wraps an angle into [-pi, pi]."""
    while angle_rad > math.pi:
        angle_rad -= 2.0 * math.pi
    while angle_rad < -math.pi:
        angle_rad += 2.0 * math.pi
    return angle_rad


def compute_hip_pivot_latency(
    body_facing_angle_rad: float, target_pass_angle_rad: float
) -> float:
    """
    Turn-plus-plant latency (seconds) to align hips with a target direction.
    """
    diff_rad = abs(wrap_angle_rad(target_pass_angle_rad - body_facing_angle_rad))

    if diff_rad <= OPEN_HIP_THRESHOLD_RAD:
        # Open body shape: only standing foot plant needed
        return MIN_PLANT_FOOT_DELAY_S

    if diff_rad <= RIGHT_ANGLE_HIP_RAD:
        # Moderate rotation (35 to 90 degrees)
        frac = (diff_rad - OPEN_HIP_THRESHOLD_RAD) / (
            RIGHT_ANGLE_HIP_RAD - OPEN_HIP_THRESHOLD_RAD
        )
        return round(MIN_PLANT_FOOT_DELAY_S + frac * 0.25, 3)

    # Extreme pivot (> 90 degrees)
    frac = min(1.0, (diff_rad - RIGHT_ANGLE_HIP_RAD) / (math.pi - RIGHT_ANGLE_HIP_RAD))
    return round(0.40 + frac * 0.30, 3)
