"""Arrival-time core: margin(j) = t_press(j) - t_ball(j), per outlet.

A pass is trapped when any opponent reaches the receiver's lead target
before the ball does, regardless of the static cushion at decision time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.config import PITCH_LENGTH_METERS, PITCH_WIDTH_METERS
from src.core.geometry import PitchPoint
from src.models.pressing.readiness import resolve_facing
from src.models.pressing.types import PressingActor, gate_tracking_velocity
from src.physics.biomechanics import compute_hip_pivot_latency
from src.physics.gk_constraints import (
    GK_REACTION_TIME_DEFAULT_S,
    MAX_LEAD_DISPLACEMENT_M,
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


def lead_target(
    pos: PitchPoint,
    vel_ms: Tuple[float, float],
    flight_s: float,
    max_displacement_m: float = MAX_LEAD_DISPLACEMENT_M,
) -> PitchPoint:
    """Receiver's lead position: current pos + velocity * ball flight time,
    capped at max_displacement_m. Same-frame convention: both the ball and
    the pressers race to this point, never to the stale current position.
    """
    if not math.isfinite(flight_s):
        return PitchPoint(x=round(pos.x, 2), y=round(pos.y, 2))
    dx = vel_ms[0] * flight_s
    dy = vel_ms[1] * flight_s
    disp = math.hypot(dx, dy)
    if disp > max_displacement_m and disp > 1e-6:
        scale = max_displacement_m / disp
        dx *= scale
        dy *= scale

    lead_x = max(0.0, min(PITCH_LENGTH_METERS, pos.x + dx))
    lead_y = max(0.0, min(PITCH_WIDTH_METERS, pos.y + dy))
    return PitchPoint(x=round(lead_x, 2), y=round(lead_y, 2))


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
        return GK_REACTION_TIME_DEFAULT_S, source
    required = math.atan2(target.y - presser.pos_m.y, target.x - presser.pos_m.x)
    return compute_hip_pivot_latency(facing, required), source


def presser_arrival_s(
    presser: PressingActor,
    target: PitchPoint,
    max_accel_mss: float = PRESSER_MAX_BURST_ACCEL_MSS,
    max_speed_ms: float = PRESSER_SPRINT_MAX_SPEED_MS,
    engagement_latency_s: float = 0.0,
) -> Tuple[float, float]:
    """Defender arrival time under sprint acceleration kinematics.

    Profile: d = v0 * t + 0.5 * a * t^2 up to max_speed_ms, plus an
    engagement latency for turn/reaction (see presser_engagement_latency_s).
    Only the closing velocity component counts; running away starts at 0.
    """
    dx = target.x - presser.pos_m.x
    dy = target.y - presser.pos_m.y
    dist = math.hypot(dx, dy)
    if dist < 1e-3:
        return round(engagement_latency_s, 3), 0.0

    (vx, vy), _ = gate_tracking_velocity(presser.vel_ms, presser.speed_capped)
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
) -> ArrivalResult:
    """Per-outlet race: margin = t_press - t_ball, both timed to the lead.

    Fixed-point iteration: lead from flight, flight to lead, until the lead
    moves <1 cm or 8 rounds. Ball and pressers then race to the same point.
    """
    rec_vel, _ = gate_tracking_velocity(receiver.vel_ms, receiver.speed_capped)
    rx, ry = receiver.pos_m.x, receiver.pos_m.y
    t_ball = prep_latency_s + flight_time_s(
        math.hypot(rx - passer_pos.x, ry - passer_pos.y),
        v0_ms=pass_speed_ms,
    )
    target = lead_target(receiver.pos_m, rec_vel, t_ball)
    for _ in range(8):
        t_next = prep_latency_s + flight_time_s(
            math.hypot(target.x - passer_pos.x, target.y - passer_pos.y),
            v0_ms=pass_speed_ms,
        )
        if not math.isfinite(t_next):
            t_ball = t_next
            break
        nxt = lead_target(receiver.pos_m, rec_vel, t_next)
        if math.hypot(nxt.x - target.x, nxt.y - target.y) < 0.01:
            t_ball, target = t_next, nxt
            break
        t_ball, target = t_next, nxt

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
        engage, _ = presser_engagement_latency_s(op, target)
        arrival, dist = presser_arrival_s(op, target, engagement_latency_s=engage)
        if dist < marking:
            marking = dist
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
