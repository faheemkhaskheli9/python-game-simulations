"""Reusable pieces for the 2D RPG prototype (Phase 1).

`tilemap` and `entity` are pure Python (no pygame) so the movement/collision
logic can be unit-tested headlessly. `game` wires them to pygame for rendering
and input and imports pygame lazily.
"""

from .entity import Player
from .tilemap import FLOOR, PLAYER_START, WALL, TileMap

__all__ = ["TileMap", "Player", "WALL", "FLOOR", "PLAYER_START"]
