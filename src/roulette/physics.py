"""Standalone roulette wheel physics simulation (issue #4).

Lives in its own subfolder (``src/roulette/``), independent of the RPG
prototype under ``src/rpg/`` -- a self-contained sub-experiment per
README.md Section 4 ("Roulette physics simulation").

The ball's angular position is a discrete-time, friction-decelerated
simulation (NumPy vectorized) rather than a closed-form-only solve, so the
trajectory is inspectable at every timestep, not just the final resting
angle. The wheel keeps spinning throughout (friction may be zero -- a real
croupier keeps it turning at roughly constant speed); only the ball's speed
must decay to a stop, since that stop is what determines the resting pocket.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

DEFAULT_POCKET_COUNT = 37  # European single-zero wheel: pockets 0..36
DEFAULT_DT = 0.01  # seconds per simulation step

TWO_PI = 2.0 * np.pi


class RouletteError(ValueError):
    """Raised for an invalid simulation configuration."""


@dataclass(frozen=True)
class SpinParameters:
    ball_initial_speed: float  # rad/s
    ball_friction: float  # rad/s^2 deceleration; the ball must reach zero
    wheel_initial_speed: float = 0.0  # rad/s
    wheel_friction: float = 0.0  # rad/s^2 deceleration; 0 = constant speed
    ball_initial_angle: float = 0.0
    wheel_initial_angle: float = 0.0
    pocket_count: int = DEFAULT_POCKET_COUNT
    dt: float = DEFAULT_DT

    def __post_init__(self) -> None:
        if self.ball_initial_speed <= 0:
            raise RouletteError(f"ball_initial_speed must be > 0, got {self.ball_initial_speed}")
        if self.ball_friction <= 0:
            raise RouletteError(
                f"ball_friction must be > 0 (the ball must come to rest), got {self.ball_friction}"
            )
        if self.wheel_friction < 0:
            raise RouletteError(f"wheel_friction must be >= 0, got {self.wheel_friction}")
        if self.pocket_count <= 0:
            raise RouletteError(f"pocket_count must be > 0, got {self.pocket_count}")
        if self.dt <= 0:
            raise RouletteError(f"dt must be > 0, got {self.dt}")


@dataclass(frozen=True)
class SpinResult:
    pocket: int
    resting_ball_angle: float
    resting_wheel_angle: float
    stop_time: float
    ball_trajectory: np.ndarray  # cumulative ball angle at each timestep
    wheel_trajectory: np.ndarray  # cumulative wheel angle at each timestep


def _cumulative_angle(initial_speed: float, friction: float, times: np.ndarray, dt: float) -> np.ndarray:
    """Angle traveled at each of `times`, decelerating at `friction` from
    `initial_speed` (never going negative -- a body doesn't spin backward
    just because the naive kinematic formula would extrapolate past zero)."""
    speeds = np.clip(initial_speed - friction * times, 0.0, None)
    return np.cumsum(speeds * dt)


def spin(params: SpinParameters) -> SpinResult:
    """Simulate one spin from `params` and return the resting pocket."""
    stop_time = params.ball_initial_speed / params.ball_friction
    times = np.arange(0.0, stop_time, params.dt)

    ball_trajectory = _cumulative_angle(params.ball_initial_speed, params.ball_friction, times, params.dt)
    wheel_trajectory = _cumulative_angle(params.wheel_initial_speed, params.wheel_friction, times, params.dt)

    resting_ball_angle = params.ball_initial_angle + float(ball_trajectory[-1])
    resting_wheel_angle = params.wheel_initial_angle + float(wheel_trajectory[-1])

    relative_angle = (resting_ball_angle - resting_wheel_angle) % TWO_PI
    pocket_width = TWO_PI / params.pocket_count
    pocket = int(relative_angle // pocket_width) % params.pocket_count

    return SpinResult(
        pocket=pocket,
        resting_ball_angle=resting_ball_angle,
        resting_wheel_angle=resting_wheel_angle,
        stop_time=stop_time,
        ball_trajectory=ball_trajectory,
        wheel_trajectory=wheel_trajectory,
    )


def random_spin(
    rng: np.random.Generator,
    *,
    pocket_count: int = DEFAULT_POCKET_COUNT,
    dt: float = DEFAULT_DT,
) -> SpinResult:
    """Simulate one spin with randomized-but-physically-plausible initial
    conditions -- the "many simulated spins" input for the distribution
    sanity check (issue #4 acceptance criterion #2)."""
    params = SpinParameters(
        ball_initial_speed=float(rng.uniform(15.0, 30.0)),
        ball_friction=float(rng.uniform(0.5, 1.5)),
        wheel_initial_speed=float(rng.uniform(2.0, 5.0)),
        wheel_friction=0.0,
        ball_initial_angle=float(rng.uniform(0.0, TWO_PI)),
        wheel_initial_angle=float(rng.uniform(0.0, TWO_PI)),
        pocket_count=pocket_count,
        dt=dt,
    )
    return spin(params)
