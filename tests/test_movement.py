"""Movement + collision resolution, exercised without any rendering backend."""

from src.rpg.entity import Player
from src.rpg.tilemap import TileMap

# Border walls plus a single interior wall at tile (col=2, row=2).
ROOM = """\
#####
#...#
#.#.#
#...#
#####
"""

OPEN_FIELD = """\
.....
.....
.....
"""


def room():
    return TileMap.from_text(ROOM, tile_size=10)


def test_moves_freely_across_floor():
    p = Player(x=11, y=11, size=6, speed=1.0)
    result = p.move(1, 0, room(), dt=3)
    assert result == (14, 11)
    assert (p.x, p.y) == (14, 11)


def test_step_into_interior_wall_is_cancelled():
    m = room()
    p = Player(x=11, y=21, size=6, speed=1.0)
    p.move(1, 0, m, dt=7)  # would land on x=18, overlapping wall tile (2, 2)
    assert p.x == 11  # blocked, no partial move
    # a smaller step that stays inside the floor tile is allowed
    p.move(1, 0, m, dt=2)
    assert p.x == 13


def test_slides_along_wall_when_one_axis_blocked():
    m = room()
    p = Player(x=11, y=21, size=6, speed=1.0)
    p.move(1, -1, m, dt=7)  # up-right into the wall corner
    assert p.x == 11  # horizontal component blocked
    assert p.y == 14  # vertical component still applied -> slide


def test_clamped_inside_map_bounds():
    m = TileMap.from_text(OPEN_FIELD, tile_size=10)  # no border walls
    p = Player(x=11, y=11, size=6, speed=1.0)
    p.move(1, 0, m, dt=1000)
    assert p.x == m.pixel_width - p.size  # 44, not off the map
    p.move(-1, 0, m, dt=1000)
    assert p.x == 0


def test_border_wall_stops_player_before_edge():
    m = room()
    p = Player(x=11, y=11, size=6, speed=1.0)
    p.move(-1, 0, m, dt=1000)
    assert p.x == 11  # can't enter the border wall column
