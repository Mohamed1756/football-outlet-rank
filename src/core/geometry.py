"""Canonical pitch coordinates (meters, origin at center, attack left-to-right)."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PitchPoint:
    """A 2D coordinate on the normalized pitch (meters)."""

    x: float
    y: float

    def distance_to(self, other: PitchPoint) -> float:
        """Euclidean distance to another point."""
        return math.hypot(self.x - other.x, self.y - other.y)
