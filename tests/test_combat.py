"""Combat resolution tests — pure logic, no pygame/display involved."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rpg.combat import Enemy, resolve_attack
from rpg.entity import Player


def _player(**kwargs) -> Player:
    return Player(x=0.0, y=0.0, **kwargs)


def _enemy(**kwargs) -> Enemy:
    return Enemy(x=0.0, y=0.0, **kwargs)


def test_attack_reduces_defender_health():
    attacker = _player(attack_power=15)
    defender = _enemy(health=40, max_health=40)

    result = resolve_attack(attacker, defender)

    assert result is not None
    assert result.damage_dealt == 15
    assert defender.health == 25
    assert result.defender_health == 25
    assert result.defender_defeated is False


def test_attack_out_of_range_is_a_no_op():
    attacker = _player(attack_power=15)
    defender = _enemy(health=40)
    defender.x, defender.y = 1000.0, 1000.0

    result = resolve_attack(attacker, defender)

    assert result is None
    assert defender.health == 40


def test_enemy_defeat_condition():
    attacker = _player(attack_power=25)
    defender = _enemy(health=20, max_health=20)

    result = resolve_attack(attacker, defender)

    assert result.defender_defeated is True
    assert defender.health == 0
    assert defender.is_alive is False


def test_health_never_drops_below_zero():
    attacker = _player(attack_power=999)
    defender = _enemy(health=10, max_health=10)

    resolve_attack(attacker, defender)

    assert defender.health == 0


def test_attacking_an_already_defeated_enemy_is_a_no_op():
    attacker = _player(attack_power=15)
    defender = _enemy(health=0, max_health=40)

    result = resolve_attack(attacker, defender)

    assert result is None
    assert defender.health == 0


def test_player_defeat_condition():
    attacker = _enemy(attack_power=999)
    defender = _player(health=10)

    result = resolve_attack(attacker, defender)

    assert result.defender_defeated is True
    assert defender.is_alive is False


def test_dead_attacker_cannot_attack():
    attacker = _player(health=0, attack_power=15)
    defender = _enemy(health=40)

    result = resolve_attack(attacker, defender)

    assert result is None
    assert defender.health == 40
