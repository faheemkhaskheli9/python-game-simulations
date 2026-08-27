"""Player entity and axis-separated collision resolution.

Movement is continuous (pixels), the world is a tile grid. Collision uses an
axis-by-axis sweep so that sliding along a wall works: if the horizontal step
would overlap a blocked tile it is dropped, then the vertical step is tried
independently.
"""

from __future__ import annotations

from dataclasses import dataclass

from .tilemap import TileMap


def _aabb_hits_wall(tile_map: TileMap, x: float, y: float, w: int, h: int) -> bool:
    """True if the axis-aligned box at (x, y) overlaps any blocked tile."""
    ts = tile_map.tile_size
    left = int(x // ts)
    right = int((x + w - 1) // ts)
    top = int(y // ts)
    bottom = int((y + h - 1) // ts)
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if tile_map.is_blocked(col, row):
                return True
    return False


@dataclass
class Player:
    """A square actor positioned by its top-left pixel corner."""

    x: float
    y: float
    size: int = 24
    speed: float = 120.0  # pixels per second at full input

    @property
    def rect(self) -> tuple[float, float, int, int]:
        return (self.x, self.y, self.size, self.size)

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.size / 2, self.y + self.size / 2)

    def move(self, dx: float, dy: float, tile_map: TileMap, dt: float = 1.0) -> tuple[float, float]:
        """Attempt to move by direction (dx, dy), each in roughly [-1, 1].

        Returns the resulting (x, y). Blocked axes are cancelled independently,
        and the actor is always clamped inside the map bounds.
        """
        max_x = tile_map.pixel_width - self.size
        max_y = tile_map.pixel_height - self.size

        step_x = dx * self.speed * dt
        candidate_x = _clamp(self.x + step_x, 0.0, max_x)
        if not _aabb_hits_wall(tile_map, candidate_x, self.y, self.size, self.size):
            self.x = candidate_x

        step_y = dy * self.speed * dt
        candidate_y = _clamp(self.y + step_y, 0.0, max_y)
        if not _aabb_hits_wall(tile_map, self.x, candidate_y, self.size, self.size):
            self.y = candidate_y

        return (self.x, self.y)


def _clamp(value: float, low: float, high: float) -> float:
    if high < low:
        return low
    return max(low, min(value, high))
