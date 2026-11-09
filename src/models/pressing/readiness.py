"""Receiver readiness: can this body take the ball on the front foot?

Open (facing upfield, pass into stride) is ready now. Back-to-passer prices
in a turn via the hip-pivot curve instead of a veto. Facing is pose or
unknown; unknown notes, it does not discount through an unmeasured prior.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from src.core.geometry import PitchPoint
from src.models.pressing.types import PressingActor
from src.physics.biomechanics import (
    compute_biomechanical_execution_penalty,
    compute_hip_pivot_latency,
)
from src.physics.gk_constraints import (
    RECEIVER_FIRST_TOUCH_LATENCY_S,
    RETENTION_CRITICAL_CUSHION_S,
    RETENTION_LOGISTIC_STEEPNESS_K,
)


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


def resolve_facing(actor: PressingActor) -> Tuple[float, str]:
    """Body orientation or unknown. Pose measurement only: velocity
    direction is travel, not facing, and ball-oriented facing assumed a
    ball-watching receiver we never measured. Unknown pays full price.
    """
    if actor.facing_rad is not None:
        return actor.facing_rad, actor.facing_source or "pose"
    return -1.571, "unknown"


def receiver_readiness(
    receiver: PressingActor,
    passer_pos: PitchPoint,
) -> ReadinessResult:
    facing, source = resolve_facing(receiver)
    pass_angle = math.atan2(
        passer_pos.y - receiver.pos_m.y, passer_pos.x - receiver.pos_m.x
    )
    turn_latency = compute_hip_pivot_latency(facing, pass_angle)
    mult = compute_biomechanical_execution_penalty(facing, pass_angle)

    note = "open" if turn_latency <= 0.15 else "needs-turn"
    if source == "unknown":
        note += "+unknown-facing"
    reception_latency = round(RECEIVER_FIRST_TOUCH_LATENCY_S + turn_latency, 3)
    return ReadinessResult(
        receiver_track_id=receiver.track_id,
        readiness_mult=round(mult, 3),
        turn_latency_s=round(turn_latency, 3),
        facing_source=source,
        note=note,
        reception_latency_s=reception_latency,
    )
