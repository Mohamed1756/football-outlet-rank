"""Unit tests for canonical pitch coordinates."""

import pytest

from src.core.geometry import PitchPoint


def test_pitch_point_distance():
    p1 = PitchPoint(0.0, 0.0)
    p2 = PitchPoint(3.0, 4.0)
    assert p1.distance_to(p2) == pytest.approx(5.0)
