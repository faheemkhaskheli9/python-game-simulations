"""Tests for the standalone roulette wheel physics simulation (issue #4).

Uses ``from src.roulette...`` imports (not ``from roulette...``) so this
file's collection doesn't depend on another test module having already
patched sys.path -- see test_combat.py for that side effect.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.roulette.physics import (
    DEFAULT_POCKET_COUNT,
    RouletteError,
    SpinParameters,
    random_spin,
    spin,
)


def test_spin_produces_a_valid_pocket():
    params = SpinParameters(ball_initial_speed=20.0, ball_friction=1.0)
    result = spin(params)
    assert 0 <= result.pocket < DEFAULT_POCKET_COUNT


def test_spin_is_deterministic_given_the_same_parameters():
    params = SpinParameters(ball_initial_speed=20.0, ball_friction=1.0, ball_initial_angle=0.3)
    a = spin(params)
    b = spin(params)
    assert a.pocket == b.pocket
    assert a.resting_ball_angle == b.resting_ball_angle


def test_ball_trajectory_is_monotonically_increasing_then_flat():
    params = SpinParameters(ball_initial_speed=20.0, ball_friction=1.0)
    result = spin(params)
    diffs = np.diff(result.ball_trajectory)
    assert np.all(diffs >= -1e-9)  # never spins backward


def test_stop_time_matches_speed_over_friction():
    params = SpinParameters(ball_initial_speed=20.0, ball_friction=2.0)
    result = spin(params)
    assert result.stop_time == pytest.approx(10.0)


def test_higher_friction_stops_the_ball_sooner():
    slow_friction = spin(SpinParameters(ball_initial_speed=20.0, ball_friction=1.0))
    fast_friction = spin(SpinParameters(ball_initial_speed=20.0, ball_friction=4.0))
    assert fast_friction.stop_time < slow_friction.stop_time


def test_zero_wheel_friction_means_wheel_keeps_constant_speed():
    params = SpinParameters(
        ball_initial_speed=20.0, ball_friction=1.0, wheel_initial_speed=3.0, wheel_friction=0.0
    )
    result = spin(params)
    # Constant speed over stop_time seconds -> angle == speed * time.
    assert result.resting_wheel_angle == pytest.approx(3.0 * result.stop_time, rel=1e-3)


@pytest.mark.parametrize(
    "kwargs,bad_field",
    [
        ({"ball_initial_speed": 0.0, "ball_friction": 1.0}, "ball_initial_speed"),
        ({"ball_initial_speed": -1.0, "ball_friction": 1.0}, "ball_initial_speed"),
        ({"ball_initial_speed": 20.0, "ball_friction": 0.0}, "ball_friction"),
        ({"ball_initial_speed": 20.0, "ball_friction": -1.0}, "ball_friction"),
        ({"ball_initial_speed": 20.0, "ball_friction": 1.0, "wheel_friction": -1.0}, "wheel_friction"),
        ({"ball_initial_speed": 20.0, "ball_friction": 1.0, "pocket_count": 0}, "pocket_count"),
        ({"ball_initial_speed": 20.0, "ball_friction": 1.0, "dt": 0.0}, "dt"),
    ],
)
def test_invalid_parameters_are_rejected(kwargs, bad_field):
    with pytest.raises(RouletteError, match=bad_field):
        SpinParameters(**kwargs)


# --- Distribution sanity check over many simulated spins ------------------


def test_random_spin_outcome_distribution_is_reasonable():
    rng = np.random.default_rng(seed=42)
    n_spins = 3000
    pockets = [random_spin(rng).pocket for _ in range(n_spins)]

    counts = np.bincount(pockets, minlength=DEFAULT_POCKET_COUNT)
    assert len(counts) == DEFAULT_POCKET_COUNT
    assert all(0 <= p < DEFAULT_POCKET_COUNT for p in pockets)

    # Coverage: with 3000 spins across 37 pockets (~81 expected per pocket),
    # every pocket should come up at least once if the mapping is behaving
    # like a real wheel rather than collapsing onto a handful of outcomes.
    assert np.all(counts > 0), f"some pockets never hit: {np.where(counts == 0)[0]}"

    # Rough uniformity: no single pocket should dominate far past what
    # random variation could plausibly produce (expected ~81/pocket).
    expected = n_spins / DEFAULT_POCKET_COUNT
    assert counts.max() < expected * 3


def test_random_spin_uses_the_given_rng_deterministically():
    a = random_spin(np.random.default_rng(seed=7))
    b = random_spin(np.random.default_rng(seed=7))
    assert a.pocket == b.pocket
