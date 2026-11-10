"""Arrival-time core: margin(j) = t_press(j) - t_ball(j), per outlet.

A pass is trapped when any opponent reaches the ball-to-runner intercept
before the ball does, regardless of the static cushion at decision time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import List, Optional, Tuple

from src.core.geometry import PitchPoint
from src.models.pressing.readiness import resolve_facing
from src.models.pressing.types import PressingActor, gate_tracking_velocity
from src.physics.biomechanics import compute_hip_pivot_latency
from src.physics.arrival_constants import (
    HUMAN_REACTION_FLOOR_S,
    PASS_GROUND_INITIAL_SPEED_MS,
    PASS_TURF_ROLLING_DECELERATION_MSS,
    PRESSER_MAX_BURST_ACCEL_MSS,
    PRESSER_SPRINT_MAX_SPEED_MS,
)


@dataclass(frozen=True)
class ArrivalResult:
    receiver_track_id: int
    margin_s: float
    t_ball_s: float
    t_press_s: float
    best_presser_id: Optional[int]
    marking_dist_m: float


def flight_time_s(
    dist_m: float,
    v0_ms: float = PASS_GROUND_INITIAL_SPEED_MS,
    a_turf_mss: float = PASS_TURF_ROLLING_DECELERATION_MSS,
) -> float:
    """Rolling ground-pass flight time: dist = v0 * t - 0.5 * a * t^2.

    Returns inf when the ball cannot arrive (beyond stopping distance).
    Callers treat inf as no-ball, not a slow ball.
    """
    if dist_m <= 0.0:
        return 0.0
    disc = v0_ms * v0_ms - 2.0 * a_turf_mss * dist_m
    if disc <= 0.0:
        return math.inf
    return round((v0_ms - math.sqrt(disc)) / a_turf_mss, 3)


def intercept_target(
    receiver_pos: PitchPoint,
    receiver_vel_ms: Tuple[float, float],
    passer_pos: PitchPoint,
    prep_latency_s: float = 0.0,
    pass_speed_ms: float = PASS_GROUND_INITIAL_SPEED_MS,
    a_turf_mss: float = PASS_TURF_ROLLING_DECELERATION_MSS,
) -> Tuple[PitchPoint, float]:
    """Joint ball-to-runner intercept: the point where ball travel meets the
    receiver's run. Solves dist(t) = v0*t - 0.5*a*t^2 by bisection.

    Monotone horizon: ball speed v0-a*t must exceed any gated run speed, so
    t_hi = (v0 - max_run) / a, floored at 0. Past it the gap can go
    non-monotone (dead ball, live runner): unreachable, not a slow ball.
    Unclamped: the intercept is playable space, on or off the pitch.
    Receiver runs during prep; pressers stay frozen (snapshot convention).
    """
    px = receiver_pos.x + receiver_vel_ms[0] * prep_latency_s
    py = receiver_pos.y + receiver_vel_ms[1] * prep_latency_s
    vx, vy = receiver_vel_ms

    def gap(t: float) -> float:
        d = math.hypot(px + vx * t - passer_pos.x, py + vy * t - passer_pos.y)
        return d - (pass_speed_ms * t - 0.5 * a_turf_mss * t * t)

    if gap(0.0) <= 0.0:
        return PitchPoint(x=round(px, 2), y=round(py, 2)), prep_latency_s
    t_hi = (pass_speed_ms - PRESSER_SPRINT_MAX_SPEED_MS) / a_turf_mss
    if t_hi <= 0.0 or gap(t_hi) > 0.0:
        return PitchPoint(x=round(px, 2), y=round(py, 2)), math.inf
    lo, hi = 0.0, t_hi
    for _ in range(64):
        mid = 0.5 * (lo + hi)
        if gap(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    tf = 0.5 * (lo + hi)
    return (
        PitchPoint(x=round(px + vx * tf, 2), y=round(py + vy * tf, 2)),
        prep_latency_s + tf,
    )


def presser_engagement_latency_s(
    presser: PressingActor,
    target: PitchPoint,
) -> Tuple[float, str]:
    """Turn-plus-reaction latency before a presser can sprint at the target.

    Known facing prices the turn on the hip-pivot curve. Unknown facing pays
    the human reaction floor: unknown is not engaged.
    """
    facing, source = resolve_facing(presser)
    if facing is None:
        return HUMAN_REACTION_FLOOR_S, source
    required = math.atan2(target.y - presser.pos_m.y, target.x - presser.pos_m.x)
    return compute_hip_pivot_latency(facing, required), source


def presser_arrival_s(
    presser: PressingActor,
    target: PitchPoint,
    max_accel_mss: float = PRESSER_MAX_BURST_ACCEL_MSS,
    max_speed_ms: float = PRESSER_SPRINT_MAX_SPEED_MS,
    engagement_latency_s: float = 0.0,
    lead_s: float = 0.0,
) -> Tuple[float, float]:
    """Defender arrival time under sprint acceleration kinematics.

    Profile: d = v0 * t + 0.5 * a * t^2 up to max_speed_ms, plus an
    engagement latency for turn/reaction (see presser_engagement_latency_s).
    Only the closing velocity component counts; running away starts at 0.
    lead_s advances the start position by gated velocity times lead_s
    (live presser motion during ball flight); 0.0 keeps the frozen shape.
    Standing on the intercept (dist < 1 mm) skips the sprint and prices
    engagement latency only: the most dangerous geometry, never zero.
    """
    (vx, vy), _ = gate_tracking_velocity(presser.vel_ms, presser.speed_capped)
    sx = presser.pos_m.x + vx * lead_s
    sy = presser.pos_m.y + vy * lead_s
    dx = target.x - sx
    dy = target.y - sy
    dist = math.hypot(dx, dy)
    if dist < 1e-3:
        return round(engagement_latency_s, 3), 0.0

    closing = (vx * dx + vy * dy) / dist
    v0 = max(0.0, min(max_speed_ms, closing))

    # Time and distance to reach max sprint velocity
    t_vmax = max(0.0, (max_speed_ms - v0) / max_accel_mss)
    d_accel = v0 * t_vmax + 0.5 * max_accel_mss * (t_vmax**2)

    if dist <= d_accel:
        t_press = (
            -v0 + math.sqrt(max(0.0, v0 * v0 + 2.0 * max_accel_mss * dist))
        ) / max_accel_mss
    else:
        d_remaining = dist - d_accel
        t_press = t_vmax + (d_remaining / max_speed_ms)

    return round(t_press + engagement_latency_s, 3), round(dist, 2)


def arrival_margin(
    receiver: PressingActor,
    opponents: List[PressingActor],
    passer_pos: PitchPoint,
    pass_speed_ms: float = PASS_GROUND_INITIAL_SPEED_MS,
    prep_latency_s: float = 0.0,
    live_pressers: bool = False,
) -> ArrivalResult:
    """Per-outlet race: margin = t_press - t_ball at the joint intercept.

    Ball travel meets the receiver's run (no lead cap: the cap timed the
    ball to a point the runner had already passed). Pressers race to the
    same intercept. Frozen by default: positions at decision time except
    the receiver's run and ball flight, a documented pro-receiver bias.
    live_pressers advances each presser by gated velocity times t_ball
    (needs live tracking velocities; 360 snapshots carry none, so the
    calibration stays frozen). t_ball chains at full precision into the
    presser advance; only the reported t_ball_s is rounded to ms.

    marking_dist_m is the nearest opponent's frozen-snapshot distance to
    the intercept: context for display, never ranked or calibrated on.
    """
    rec_vel, _ = gate_tracking_velocity(receiver.vel_ms, receiver.speed_capped)
    target, t_ball = intercept_target(
        receiver.pos_m, rec_vel, passer_pos, prep_latency_s, pass_speed_ms
    )

    if not math.isfinite(t_ball):
        return ArrivalResult(
            receiver_track_id=receiver.track_id,
            margin_s=-99.0,
            t_ball_s=math.inf,
            t_press_s=math.inf,
            best_presser_id=None,
            marking_dist_m=99.0,
        )

    best_presser: Optional[int] = None
    t_press = math.inf
    marking = math.inf
    for op in opponents:
        if not op.pitch_valid:
            continue
        # Live advance once: engagement angle and sprint share the advanced
        # start; marking stays frozen-snapshot by definition.
        runner = op
        if live_pressers:
            (vx, vy), _ = gate_tracking_velocity(op.vel_ms, op.speed_capped)
            runner = replace(
                op,
                pos_m=PitchPoint(op.pos_m.x + vx * t_ball, op.pos_m.y + vy * t_ball),
            )
        engage, _ = presser_engagement_latency_s(runner, target)
        arrival, _ = presser_arrival_s(runner, target, engagement_latency_s=engage)
        frozen_dist = math.dist((op.pos_m.x, op.pos_m.y), (target.x, target.y))
        if frozen_dist < marking:
            marking = frozen_dist
        if arrival < t_press:
            t_press = arrival
            best_presser = op.track_id

    if math.isinf(t_press):
        t_press = 99.0
    if math.isinf(marking):
        marking = 99.0
    return ArrivalResult(
        receiver_track_id=receiver.track_id,
        margin_s=round(t_press - t_ball, 3),
        t_ball_s=round(t_ball, 3),
        t_press_s=round(t_press, 3),
        best_presser_id=best_presser,
        marking_dist_m=round(marking, 2),
    )
