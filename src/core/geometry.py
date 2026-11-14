"""Canonical pitch coordinates (meters, corner origin, attack left-to-right).

All loaders map provider frames onto corner-origin meters: x in
[0, 105] attack left-to-right, y in [0, 68]. Code outside the loaders
never handles raw provider coordinates and never re-flips ends
(one exception: Metrica periods keep raw orientation, so direction
measurements like outlet_value progress are unreliable there — see
outlet_value).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# Canonical pitch dimensions (FIFA Laws of the Game: 105 x 68 m
# international standard). Corner origin, x attack left-to-right.
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
