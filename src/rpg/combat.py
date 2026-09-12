"""Basic melee combat: an enemy entity plus pure attack-resolution logic.

Kept independent of pygame and of :mod:`rpg.game` so the combat rules can be
unit tested without a display or an event loop.
"""

from __future__ import annotations

from dataclasses import dataclass

# Attacks only land within this many pixels of the defender's center.
ATTACK_RANGE_PX = 40.0


@dataclass
class Enemy:
    """A square actor with health, positioned by its top-left pixel corner."""

    x: float
    y: float
    size: int = 24
    health: int = 40
    max_health: int = 40
    attack_power: int = 8

    @property
    def rect(self) -> tuple[float, float, int, int]:
        return (self.x, self.y, self.size, self.size)

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.size / 2, self.y + self.size / 2)

    @property
    def is_alive(self) -> bool:
        return self.health > 0


@dataclass(frozen=True)
class AttackResult:
    """Outcome of one resolved attack."""

    damage_dealt: int
    defender_health: int
    defender_defeated: bool


def _distance(a, b) -> float:
    (ax, ay), (bx, by) = a.center, b.center
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def in_range(attacker, defender, *, max_range: float = ATTACK_RANGE_PX) -> bool:
    """True if defender's center is within melee range of attacker's center."""
    return _distance(attacker, defender) <= max_range


def resolve_attack(attacker, defender, *, max_range: float = ATTACK_RANGE_PX) -> AttackResult | None:
    """Apply ``attacker``'s damage to ``defender`` if in range and both alive.

    Returns ``None`` (no-op) if the attacker is dead, the defender is already
    dead, or the defender is out of range. Health never drops below zero.
    """
    if not attacker.is_alive or not defender.is_alive:
        return None
    if not in_range(attacker, defender, max_range=max_range):
        return None

    damage = max(0, attacker.attack_power)
    defender.health = max(0, defender.health - damage)
    return AttackResult(
        damage_dealt=damage,
        defender_health=defender.health,
        defender_defeated=not defender.is_alive,
    )
