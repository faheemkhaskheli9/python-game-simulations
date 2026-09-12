from rpg.survival import (
    EAT_RESTORE_AMOUNT,
    SurvivalStats,
)


def test_stats_deplete_over_time():
    s = SurvivalStats()
    s.tick(dt=10.0)
    assert s.hunger == 90.0
    assert s.thirst == 85.0
    # stamina does not deplete unless sprinting
    assert s.stamina == 100.0


def test_stamina_only_depletes_while_sprinting():
    s = SurvivalStats()
    s.tick(dt=1.0, sprinting=True)
    assert s.stamina == 80.0


def test_depletion_floors_at_zero_not_negative():
    s = SurvivalStats(hunger=5.0, thirst=5.0, stamina=5.0)
    s.tick(dt=100.0, sprinting=True)
    assert s.hunger == 0.0
    assert s.thirst == 0.0
    assert s.stamina == 0.0


def test_non_positive_dt_is_a_no_op():
    s = SurvivalStats()
    s.tick(dt=0.0)
    s.tick(dt=-5.0)
    assert (s.hunger, s.thirst, s.stamina) == (100.0, 100.0, 100.0)


def test_eating_restores_hunger_clamped_to_max():
    s = SurvivalStats(hunger=50.0)
    s.eat()
    assert s.hunger == 50.0 + EAT_RESTORE_AMOUNT

    s.eat(amount=1000.0)
    assert s.hunger == s.max_hunger


def test_drinking_restores_thirst_clamped_to_max():
    s = SurvivalStats(thirst=50.0)
    s.drink(amount=1000.0)
    assert s.thirst == s.max_thirst


def test_resting_restores_stamina_over_time_clamped_to_max():
    s = SurvivalStats(stamina=10.0)
    s.rest(dt=1.0)
    assert s.stamina == 40.0

    s.rest(dt=100.0)
    assert s.stamina == s.max_stamina


def test_can_sprint_false_when_stamina_depleted():
    s = SurvivalStats(stamina=0.0)
    assert s.can_sprint is False
    assert SurvivalStats(stamina=0.1).can_sprint is True


def test_zero_hunger_or_thirst_is_a_defined_consequence_health_drain():
    s = SurvivalStats(hunger=0.0, thirst=50.0)
    assert s.is_starving is True
    assert s.is_dehydrated is False

    health = s.apply_starvation_damage(dt=1.0, health=100)
    assert health == 98  # one condition active: 2.0/sec drain


def test_starvation_and_dehydration_stack():
    s = SurvivalStats(hunger=0.0, thirst=0.0)
    health = s.apply_starvation_damage(dt=1.0, health=100)
    assert health == 96  # both conditions active: 4.0/sec drain


def test_starvation_damage_floors_at_zero_health():
    s = SurvivalStats(hunger=0.0, thirst=0.0)
    health = s.apply_starvation_damage(dt=1000.0, health=5)
    assert health == 0


def test_no_starvation_damage_when_stats_healthy():
    s = SurvivalStats()
    assert s.apply_starvation_damage(dt=10.0, health=100) == 100
