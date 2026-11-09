"""Arrival-time pressing core (team-agnostic, no CV)."""

from src.models.pressing.types import PressingActor, PressingSnapshot
from src.models.pressing.arrival import (
    arrival_margin,
    flight_time_s,
    lead_target,
    presser_arrival_s,
    presser_engagement_latency_s,
    ArrivalResult,
)
from src.models.pressing.readiness import receiver_readiness, ReadinessResult

__all__ = [
    "PressingActor",
    "PressingSnapshot",
    "arrival_margin",
    "flight_time_s",
    "lead_target",
    "presser_arrival_s",
    "presser_engagement_latency_s",
    "ArrivalResult",
    "receiver_readiness",
    "ReadinessResult",
]
