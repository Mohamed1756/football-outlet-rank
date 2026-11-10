"""Canonical pitch coordinates (meters, origin at center, attack left-to-right)."""

from __future__ import annotations

import math
from dataclasses import dataclass


# Canonical pitch dimensions (FIFA Laws of the Game: 105 x 68 m
# international standard; origin at center, attack left-to-right).
PITCH_LENGTH_M: float = 105.0
PITCH_WIDTH_M: float = 68.0


@dataclass(frozen=True)
class PitchPoint:
    """A 2D coordinate on the normalized pitch (meters)."""

    x: float
    y: float

    def distance_to(self, other: PitchPoint) -> float:
        """Euclidean distance to another point."""
        return math.hypot(self.x - other.x, self.y - other.y)
