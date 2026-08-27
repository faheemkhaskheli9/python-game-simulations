"""Tile map parsing and blocked-tile lookup for the RPG prototype.

The map is an ASCII grid:

    '#' -> wall / obstacle (blocks movement)
    '.' -> walkable floor
    '@' -> player start (also walkable)

Anything outside the grid bounds counts as a wall, so a map without a solid
border still keeps the player contained.
"""

from __future__ import annotations

from dataclasses import dataclass

WALL = "#"
FLOOR = "."
PLAYER_START = "@"

_WALKABLE = {FLOOR, PLAYER_START}


@dataclass(frozen=True)
class TileMap:
    """An immutable ASCII tile grid.

    Rows are padded to equal width with walls so ragged input is still a
    rectangle.
    """

    rows: tuple[str, ...]
    tile_size: int = 32

    @classmethod
    def from_text(cls, text: str, tile_size: int = 32) -> "TileMap":
        raw = [line.rstrip("\r\n") for line in text.splitlines() if line != ""]
        if not raw:
            raise ValueError("map text contains no rows")
        width = max(len(line) for line in raw)
        rows = tuple(line.ljust(width, WALL) for line in raw)
        if tile_size <= 0:
            raise ValueError("tile_size must be positive")
        return cls(rows, tile_size)

    @property
    def cols(self) -> int:
        return len(self.rows[0])

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @property
    def pixel_width(self) -> int:
        return self.cols * self.tile_size

    @property
    def pixel_height(self) -> int:
        return self.n_rows * self.tile_size

    def tile_at(self, col: int, row: int) -> str:
        """Return the tile char at (col, row); out-of-bounds reads as a wall."""
        if row < 0 or row >= self.n_rows or col < 0 or col >= self.cols:
            return WALL
        return self.rows[row][col]

    def is_blocked(self, col: int, row: int) -> bool:
        return self.tile_at(col, row) not in _WALKABLE

    def blocked_tiles(self) -> list[tuple[int, int]]:
        return [
            (col, row)
            for row in range(self.n_rows)
            for col in range(self.cols)
            if self.is_blocked(col, row)
        ]

    def player_start_px(self) -> tuple[int, int]:
        """Top-left pixel of the player-start tile.

        Falls back to the first walkable tile if the map has no '@'.
        """
        for row, line in enumerate(self.rows):
            col = line.find(PLAYER_START)
            if col != -1:
                return (col * self.tile_size, row * self.tile_size)
        for row, line in enumerate(self.rows):
            for col, char in enumerate(line):
                if char in _WALKABLE:
                    return (col * self.tile_size, row * self.tile_size)
        raise ValueError("map has no walkable tile for the player to start on")
