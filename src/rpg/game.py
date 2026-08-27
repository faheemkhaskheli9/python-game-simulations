"""Pygame wiring for the RPG prototype: rendering + input around the pure-Python
tile map and player.

pygame is imported lazily inside :meth:`RPGGame._ensure_backend` so the module
(and the unit tests that touch only movement logic) import fine on machines
without pygame installed. Set ``SDL_VIDEODRIVER=dummy`` in the environment to run
the loop with no real window (CI / headless smoke test) together with
``max_frames``.
"""

from __future__ import annotations

from .entity import Player
from .tilemap import TileMap

_BG = (18, 18, 22)
_WALL_COLOR = (68, 68, 92)
_FLOOR_COLOR = (38, 38, 46)
_PLAYER_COLOR = (222, 184, 64)


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
        self.caption = caption
        self.max_frames = max_frames

        self.running = False
        self.frames = 0
        self._pg = None
        self._screen = None
        self._clock = None

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
        dx, dy = self.input_vector(pg.key.get_pressed())
        if dx or dy:
            self.player.move(dx, dy, self.tile_map, dt)

    def _render(self) -> None:
        pg = self._pg
        ts = self.tile_map.tile_size
        self._screen.fill(_BG)
        for row in range(self.tile_map.n_rows):
            for col in range(self.tile_map.cols):
                color = _WALL_COLOR if self.tile_map.is_blocked(col, row) else _FLOOR_COLOR
                pg.draw.rect(self._screen, color, (col * ts, row * ts, ts - 1, ts - 1))
        px, py, pw, ph = self.player.rect
        pg.draw.rect(self._screen, _PLAYER_COLOR, (int(px), int(py), pw, ph))
        pg.display.flip()
