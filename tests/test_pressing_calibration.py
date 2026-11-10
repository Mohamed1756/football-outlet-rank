"""Tests for rank-space calibration (fitted constants, structural asserts)."""

import pytest

from src.models.pressing.calibration import (
    DECILE_EDGES_S,
    DECILE_INCOMPLETION_RATE,
    RANK_INCOMPLETION_RATE,
    decile_risk,
    margin_decile,
    outlet_value,
    rank_outlets,
    rank_risk,
)


def test_rank_outlets_safest_first():
    ranks = rank_outlets([1.0, 2.5, 1.8])
    assert [r.rank for r in ranks] == [2, 0, 1]
    assert all(r.n_outlets == 3 for r in ranks)
    assert ranks[1].margin_s == 2.5


def test_margin_decile_edges():
    assert margin_decile(-1.56) == 1
    assert margin_decile(1.01) == 1
    assert margin_decile(1.02) == 2
    assert margin_decile(5.13) == 10
    assert margin_decile(99.0) == 10


def test_decile_risk_monotone_fitted_gradient():
    # ~100x failure gradient, monotone across all 10 deciles (WC2022 fit)
    assert DECILE_INCOMPLETION_RATE[0] == pytest.approx(0.204, abs=1e-3)
    assert DECILE_INCOMPLETION_RATE[-1] == pytest.approx(0.002, abs=1e-3)
    for i in range(len(DECILE_INCOMPLETION_RATE) - 1):
        assert DECILE_INCOMPLETION_RATE[i] > DECILE_INCOMPLETION_RATE[i + 1]
    assert decile_risk(1) == DECILE_INCOMPLETION_RATE[0]
    assert decile_risk(10) == DECILE_INCOMPLETION_RATE[-1]
    with pytest.raises(ValueError):
        decile_risk(0)


def test_decile_risk_pace_scales_level_not_order():
    # Default is the WC2022 rate; WWC k=1.5 reproduces the observed level
    # shift (0.27 vs 0.20 bottom) without touching edges or order.
    assert decile_risk(1) == pytest.approx(0.204, abs=1e-3)
    assert decile_risk(1, 1.5) == pytest.approx(0.306, abs=1e-3)
    assert decile_risk(1, 99.0) == 1.0


def test_outlet_value_prefers_progressive_safety():
    # Same retention, farther forward wins; identical geometry ties.
    assert outlet_value(0.9, 80.0) > outlet_value(0.9, 30.0)
    assert outlet_value(0.9, 80.0) == pytest.approx(0.9 * 80.0 / 105.0, abs=1e-4)
    # Safer backward ball loses to decent forward ball.
    assert outlet_value(0.99, 20.0) < outlet_value(0.8, 80.0)


def test_outlet_value_clamps_off_pitch():
    assert outlet_value(0.9, 200.0) == pytest.approx(0.9, abs=1e-4)
    assert outlet_value(0.9, -10.0) == 0.0


def test_rank_risk_monotone_to_pool():
    # Passers choose rank 0 44% of the time; failure rises with rank, 6+ pooled
    assert RANK_INCOMPLETION_RATE[0] == pytest.approx(0.024, abs=1e-3)
    for i in range(6):
        assert RANK_INCOMPLETION_RATE[i] < RANK_INCOMPLETION_RATE[i + 1]
    assert rank_risk(0) == RANK_INCOMPLETION_RATE[0]
    assert rank_risk(7) == rank_risk(99)
    with pytest.raises(ValueError):
        rank_risk(-1)


def test_decile_edges_sorted_and_covering():
    assert list(DECILE_EDGES_S) == sorted(DECILE_EDGES_S)
    assert len(DECILE_EDGES_S) == len(DECILE_INCOMPLETION_RATE) == 10
