"""Hunger / thirst / stamina survival stats for the RPG prototype.

Kept independent of pygame and of :mod:`rpg.game` so the depletion and
consequence rules can be unit tested without a display or an event loop,
matching the style of :mod:`rpg.combat`.

Each stat is a float in ``[0, max]`` that depletes over in-game time (seconds)
at its own rate, and is restored by a discrete action (eat / drink / rest).
Reaching zero on hunger or thirst starts draining health instead of going
negative; reaching zero on stamina blocks running (callers read
``can_run``/``can_sprint`` before applying a speed boost).
"""

from __future__ import annotations

from dataclasses import dataclass

# Depletion rates, in stat-points per second of elapsed game time.
HUNGER_DEPLETION_RATE = 1.0
THIRST_DEPLETION_RATE = 1.5
STAMINA_DEPLETION_RATE = 20.0  # only depletes while sprinting

# Restoration amounts for the discrete actions.
EAT_RESTORE_AMOUNT = 40.0
DRINK_RESTORE_AMOUNT = 40.0
REST_STAMINA_PER_SECOND = 30.0

# Health drained per second while hunger or thirst is at zero.
STARVATION_HEALTH_DRAIN_PER_SECOND = 2.0


@dataclass
class SurvivalStats:
    """Depleting hunger/thirst/stamina stats attached to a player-like entity."""

    hunger: float = 100.0
    thirst: float = 100.0
    stamina: float = 100.0
    max_hunger: float = 100.0
    max_thirst: float = 100.0
    max_stamina: float = 100.0

    @property
    def is_starving(self) -> bool:
        return self.hunger <= 0.0

    @property
    def is_dehydrated(self) -> bool:
        return self.thirst <= 0.0

    @property
    def can_sprint(self) -> bool:
        return self.stamina > 0.0

    def tick(self, dt: float, *, sprinting: bool = False) -> None:
        """Advance ``dt`` seconds of game time, depleting stats in place.

        ``dt`` must be non-negative; a non-positive value is a no-op rather
        than raising, since callers may pass a frame's elapsed time verbatim.
        """
        if dt <= 0.0:
            return

        self.hunger = max(0.0, self.hunger - HUNGER_DEPLETION_RATE * dt)
        self.thirst = max(0.0, self.thirst - THIRST_DEPLETION_RATE * dt)
        if sprinting:
            self.stamina = max(0.0, self.stamina - STAMINA_DEPLETION_RATE * dt)

    def apply_starvation_damage(self, dt: float, health: int) -> int:
        """Return ``health`` reduced for elapsed ``dt`` seconds of starvation/dehydration.

        Drains once per active condition (hunger *and* thirst at zero drains
        twice as fast as either alone), floored at zero. A no-op (returns
        ``health`` unchanged) unless hunger or thirst has actually hit zero.
        """
        if dt <= 0.0 or health <= 0:
            return health
        conditions = int(self.is_starving) + int(self.is_dehydrated)
        if conditions == 0:
            return health
        drain = STARVATION_HEALTH_DRAIN_PER_SECOND * conditions * dt
        return max(0, int(health - drain))

    def eat(self, amount: float = EAT_RESTORE_AMOUNT) -> None:
        """Restore hunger by ``amount``, clamped to ``max_hunger``."""
        self.hunger = min(self.max_hunger, self.hunger + amount)

    def drink(self, amount: float = DRINK_RESTORE_AMOUNT) -> None:
        """Restore thirst by ``amount``, clamped to ``max_thirst``."""
        self.thirst = min(self.max_thirst, self.thirst + amount)

    def rest(self, dt: float) -> None:
        """Restore stamina over ``dt`` seconds of resting, clamped to ``max_stamina``."""
        if dt <= 0.0:
            return
        self.stamina = min(self.max_stamina, self.stamina + REST_STAMINA_PER_SECOND * dt)
