"""Tests for the risk surface: structure, pace ordering, bounds."""


from src.core.geometry import PitchPoint
from src.models.pressing.types import PressingActor
from src.models.risk_surface import risk_surface


def _actor(tid, x, y, team="opp"):
    return PressingActor(track_id=tid, team_id=team, pos_m=PitchPoint(x, y))


def test_surface_covers_grid_and_bounds_risk():
    cells = risk_surface(PitchPoint(52.5, 34.0), [_actor(1, 70.0, 34.0)], nx=7, ny=4)
    assert len(cells) == 28
    assert all(0.0 <= c.risk <= 1.0 for c in cells)
    assert all(c.margin_s > -99.0 for c in cells)


def test_pace_k_shifts_levels_not_order():
    base = risk_surface(PitchPoint(52.5, 34.0), [_actor(1, 70.0, 34.0)], nx=7, ny=4)
    fast = risk_surface(
        PitchPoint(52.5, 34.0), [_actor(1, 70.0, 34.0)], nx=7, ny=4, pace_k=1.5
    )
    assert len(base) == len(fast)
    # same ordering: sort by one, check other is monotone
    order = sorted(range(len(base)), key=lambda i: base[i].risk)
    fr = [fast[i].risk for i in order]
    assert all(fr[i] <= fr[i + 1] + 1e-9 for i in range(len(fr) - 1))
    # levels shift up (capped at 1.0)
    assert sum(f.risk for f in fast) >= sum(b.risk for b in base)


def test_no_opponents_yields_zero_risk_everywhere():
    cells = risk_surface(PitchPoint(52.5, 34.0), [], nx=5, ny=3)
    assert cells and all(c.risk <= 0.01 for c in cells)
