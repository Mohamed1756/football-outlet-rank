"""Receiver readiness: can this body take the ball on the front foot?

Open (facing upfield, pass into stride) is ready now. Back-to-passer prices
in a turn via the existing hip-pivot model instead of vetoing. Back to the
nearest presser shields; chest-open to a converging presser is vulnerable.
Facing falls back pose -> velocity (>=0.5 m/s) -> ball-oriented -> unknown,
and unknown discounts instead of nuking.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from src.core.geometry import PitchPoint
from src.models.pressing.types import PressingActor, gate_tracking_velocity
from src.physics.biomechanics import (
    compute_biomechanical_execution_penalty,
    compute_hip_pivot_latency,
    wrap_angle_rad,
)
from src.physics.gk_constraints import (
    EXPOSED_MULTIPLIER,
    RECEIVER_FIRST_TOUCH_LATENCY_S,
    RETENTION_CRITICAL_CUSHION_S,
    RETENTION_LOGISTIC_STEEPNESS_K,
    SHIELD_ANGLE_DEG,
    SHIELD_BONUS,
    UNKNOWN_FACING_MULTIPLIER,
    VELOCITY_FACING_FLOOR_MS,
)

SHIELD_ANGLE_RAD = math.radians(SHIELD_ANGLE_DEG)


@dataclass(frozen=True)
class ReadinessResult:
    receiver_track_id: int
    readiness_mult: float
    turn_latency_s: float
    facing_source: str
    note: str
    reception_latency_s: float = RECEIVER_FIRST_TOUCH_LATENCY_S

    def post_cushion_s(self, arrival_margin_s: float) -> float:
        return round(arrival_margin_s - self.reception_latency_s, 3)

    def retention_prob(self, arrival_margin_s: float) -> float:
        """First-touch retention probability from post-receipt cushion."""
        cushion = self.post_cushion_s(arrival_margin_s)
        return round(
            1.0
            / (
                1.0
                + math.exp(
                    -RETENTION_LOGISTIC_STEEPNESS_K
                    * (cushion - RETENTION_CRITICAL_CUSHION_S)
                )
            ),
            4,
        )


def resolve_facing(
    actor: PressingActor,
    ball_pos: Optional[PitchPoint] = None,
) -> Tuple[float, str]:
    if actor.facing_rad is not None:
        return actor.facing_rad, actor.facing_source or "pose"
    (vx, vy), gated = gate_tracking_velocity(actor.vel_ms, actor.speed_capped)
    if not gated and math.hypot(vx, vy) >= VELOCITY_FACING_FLOOR_MS:
        return math.atan2(vy, vx), "velocity"
    if ball_pos is not None:
        dx = ball_pos.x - actor.pos_m.x
        dy = ball_pos.y - actor.pos_m.y
        if math.hypot(dx, dy) >= 1e-3:
            return math.atan2(dy, dx), "ball"
    return -1.571, "unknown"


def receiver_readiness(
    receiver: PressingActor,
    passer_pos: PitchPoint,
    nearest_presser: Optional[PressingActor] = None,
    presser_closing: bool = False,
    ball_pos: Optional[PitchPoint] = None,
) -> ReadinessResult:
    facing, source = resolve_facing(receiver, ball_pos)
    pass_angle = math.atan2(
        passer_pos.y - receiver.pos_m.y, passer_pos.x - receiver.pos_m.x
    )
    turn_latency = compute_hip_pivot_latency(facing, pass_angle)
    mult = compute_biomechanical_execution_penalty(facing, pass_angle)

    note = "open" if turn_latency <= 0.15 else "needs-turn"
    if nearest_presser is not None:
        shield_angle = math.atan2(
            nearest_presser.pos_m.y - receiver.pos_m.y,
            nearest_presser.pos_m.x - receiver.pos_m.x,
        )
        back_to_press = abs(wrap_angle_rad(shield_angle - facing)) > (
            math.pi - SHIELD_ANGLE_RAD
        )
        if back_to_press:
            mult *= SHIELD_BONUS
            note += "+shielded"
        elif presser_closing:
            mult *= EXPOSED_MULTIPLIER
            note += "+exposed"

    if source == "unknown":
        mult *= UNKNOWN_FACING_MULTIPLIER
        note += "+unknown-facing"
    reception_latency = round(RECEIVER_FIRST_TOUCH_LATENCY_S + turn_latency, 3)
    return ReadinessResult(
        receiver_track_id=receiver.track_id,
        readiness_mult=round(max(0.2, mult), 3),
        turn_latency_s=round(turn_latency, 3),
        facing_source=source,
        note=note,
        reception_latency_s=reception_latency,
    )
