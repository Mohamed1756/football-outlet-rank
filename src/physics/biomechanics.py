"""
Biomechanical Execution Cost and Physical Latency Models.
Calculates hip rotation latency, foot plant delay, and compressed presser
interception distance for goalkeeper distribution execution.
"""

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
    Computes physical execution latency (seconds) required for a goalkeeper
    to align hips, plant the standing foot, and strike the pass.
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


def evaluate_effective_press_closure(
    initial_dist_m: float, presser_closing_speed_ms: float, prep_latency_s: float
) -> float:
    """
    Calculates the remaining distance (meters) between the goalkeeper and nearest
    presser at the exact instant the ball is struck, after accounting for execution latency.
    """
    closure_m = presser_closing_speed_ms * prep_latency_s
    effective_dist_m = max(0.0, initial_dist_m - closure_m)
    return round(effective_dist_m, 2)


def compute_biomechanical_execution_penalty(
    body_facing_angle_rad: float,
    target_pass_angle_rad: float,
    is_weak_foot: bool = False,
) -> float:
    """
    Calculates execution completion multiplier in [0.20, 1.0].
    Applies angle-dependent difficulty and weak-foot penalty.
    """
    diff_rad = abs(wrap_angle_rad(target_pass_angle_rad - body_facing_angle_rad))

    # Base difficulty curve from alignment
    if diff_rad <= OPEN_HIP_THRESHOLD_RAD:
        alignment_mult = 1.0
    elif diff_rad <= RIGHT_ANGLE_HIP_RAD:
        frac = (diff_rad - OPEN_HIP_THRESHOLD_RAD) / (
            RIGHT_ANGLE_HIP_RAD - OPEN_HIP_THRESHOLD_RAD
        )
        alignment_mult = 1.0 - frac * 0.25  # Drops from 1.0 to 0.75
    else:
        frac = min(
            1.0, (diff_rad - RIGHT_ANGLE_HIP_RAD) / (math.pi - RIGHT_ANGLE_HIP_RAD)
        )
        alignment_mult = 0.75 - frac * 0.40  # Drops from 0.75 to 0.35

    if is_weak_foot:
        alignment_mult *= 0.88  # 12% weak-foot variance penalty

    return round(max(0.20, alignment_mult), 3)
