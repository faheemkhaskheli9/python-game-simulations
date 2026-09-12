"""Pygame wiring for the RPG prototype: rendering + input around the pure-Python
tile map and player.

pygame is imported lazily inside :meth:`RPGGame._ensure_backend` so the module
(and the unit tests that touch only movement logic) import fine on machines
without pygame installed. Set ``SDL_VIDEODRIVER=dummy`` in the environment to run
the loop with no real window (CI / headless smoke test) together with
``max_frames``.
"""

from __future__ import annotations

from .combat import Enemy, resolve_attack
from .entity import Player
from .survival import SurvivalStats
from .tilemap import TileMap

# Sprinting (held Shift) moves faster but drains stamina; it is silently
# downgraded to a normal walk once stamina hits zero.
SPRINT_SPEED_MULTIPLIER = 1.8

_BG = (18, 18, 22)
_WALL_COLOR = (68, 68, 92)
_FLOOR_COLOR = (38, 38, 46)
_PLAYER_COLOR = (222, 184, 64)
_ENEMY_COLOR = (200, 64, 64)
_ENEMY_DEFEATED_COLOR = (80, 80, 80)


class RPGGame:
    def __init__(
        self,
        tile_map: TileMap,
        *,
        caption: str = "2D RPG Prototype",
        max_frames: int | None = None,
    ) -> None:
        self.tile_map = tile_map
        start_x, start_y = tile_map.player_start_px()
        inset = max(0, (tile_map.tile_size - 24) // 2)
        self.player = Player(x=start_x + inset, y=start_y + inset)
        self.survival = SurvivalStats()
        self.enemies: list[Enemy] = self._spawn_enemies()
        self.caption = caption
        self.max_frames = max_frames

        self.running = False
        self.frames = 0
        self._pg = None
        self._screen = None
        self._clock = None
        self._attack_key_was_down = False

    def _spawn_enemies(self) -> list[Enemy]:
        """Place one enemy on the tile furthest (by tile distance) from the player start."""
        px, py = self.tile_map.player_start_px()
        best = None
        best_dist = -1.0
        ts = self.tile_map.tile_size
        for row in range(self.tile_map.n_rows):
            for col in range(self.tile_map.cols):
                if self.tile_map.is_blocked(col, row):
                    continue
                x, y = col * ts, row * ts
                dist = (x - px) ** 2 + (y - py) ** 2
                if dist > best_dist:
                    best_dist = dist
                    best = (x, y)
        if best is None:
            return []
        inset = max(0, (ts - 24) // 2)
        return [Enemy(x=best[0] + inset, y=best[1] + inset)]

    # -- lifecycle -----------------------------------------------------------
    def _ensure_backend(self):
        import pygame  # lazy: not needed for headless logic tests

        self._pg = pygame
        pygame.init()
        self._screen = pygame.display.set_mode(
            (self.tile_map.pixel_width, self.tile_map.pixel_height)
        )
        pygame.display.set_caption(self.caption)
        self._clock = pygame.time.Clock()
        return pygame

    def run(self, fps: int = 60) -> int:
        pg = self._ensure_backend()
        self.running = True
        while self.running:
            dt = self._clock.tick(fps) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()
            self.frames += 1
            if self.max_frames is not None and self.frames >= self.max_frames:
                self.running = False
        pg.quit()
        return self.frames

    # -- per-frame steps ---------------------------------------------------
    def _handle_events(self) -> None:
        pg = self._pg
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.running = False

    def input_vector(self, pressed) -> tuple[int, int]:
        """Map the held-keys sequence to a direction. Arrows and WASD."""
        pg = self._pg
        right = pressed[pg.K_RIGHT] or pressed[pg.K_d]
        left = pressed[pg.K_LEFT] or pressed[pg.K_a]
        down = pressed[pg.K_DOWN] or pressed[pg.K_s]
        up = pressed[pg.K_UP] or pressed[pg.K_w]
        return (int(bool(right)) - int(bool(left)), int(bool(down)) - int(bool(up)))

    def _update(self, dt: float) -> None:
        pg = self._pg
        pressed = pg.key.get_pressed()

        resting = bool(pressed[pg.K_r])
        sprinting = bool(pressed[pg.K_LSHIFT] or pressed[pg.K_RSHIFT]) and self.survival.can_sprint
        if resting:
            self.survival.rest(dt)
        else:
            self.survival.tick(dt, sprinting=sprinting)
        self.player.health = self.survival.apply_starvation_damage(dt, self.player.health)

        if pressed[pg.K_e]:
            self.survival.eat()
        if pressed[pg.K_q]:
            self.survival.drink()

        dx, dy = self.input_vector(pressed)
        if dx or dy:
            original_speed = self.player.speed
            if sprinting:
                self.player.speed = original_speed * SPRINT_SPEED_MULTIPLIER
            try:
                self.player.move(dx, dy, self.tile_map, dt)
            finally:
                self.player.speed = original_speed

        attack_key_down = bool(pressed[pg.K_SPACE])
        if attack_key_down and not self._attack_key_was_down:
            self.try_player_attack()
        self._attack_key_was_down = attack_key_down

    def try_player_attack(self) -> None:
        """Player attacks the nearest living enemy in range, if any."""
        if not self.player.is_alive:
            return
        for enemy in self.enemies:
            if enemy.is_alive:
                resolve_attack(self.player, enemy)
                break

        for enemy in self.enemies:
            if enemy.is_alive:
                resolve_attack(enemy, self.player)

    def _render(self) -> None:
        pg = self._pg
        ts = self.tile_map.tile_size
        self._screen.fill(_BG)
        for row in range(self.tile_map.n_rows):
            for col in range(self.tile_map.cols):
                color = _WALL_COLOR if self.tile_map.is_blocked(col, row) else _FLOOR_COLOR
                pg.draw.rect(self._screen, color, (col * ts, row * ts, ts - 1, ts - 1))
        for enemy in self.enemies:
            ex, ey, ew, eh = enemy.rect
            color = _ENEMY_COLOR if enemy.is_alive else _ENEMY_DEFEATED_COLOR
            pg.draw.rect(self._screen, color, (int(ex), int(ey), ew, eh))
        px, py, pw, ph = self.player.rect
        pg.draw.rect(self._screen, _PLAYER_COLOR, (int(px), int(py), pw, ph))
        pg.display.flip()
