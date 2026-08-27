import pytest

from src.rpg.tilemap import WALL, TileMap

MAP_TEXT = """\
####
#@.#
#..#
####
"""


def test_dimensions_and_pixel_size():
    m = TileMap.from_text(MAP_TEXT, tile_size=16)
    assert (m.cols, m.n_rows) == (4, 4)
    assert (m.pixel_width, m.pixel_height) == (64, 64)


def test_walls_and_floor_lookup():
    m = TileMap.from_text(MAP_TEXT, tile_size=16)
    assert m.is_blocked(0, 0) is True
    assert m.is_blocked(3, 3) is True
    assert m.is_blocked(1, 1) is False  # '@' is walkable
    assert m.is_blocked(2, 2) is False


def test_out_of_bounds_reads_as_wall():
    m = TileMap.from_text(MAP_TEXT, tile_size=16)
    assert m.is_blocked(-1, 0)
    assert m.is_blocked(0, 99)
    assert m.tile_at(50, 50) == WALL


def test_player_start_from_marker():
    m = TileMap.from_text(MAP_TEXT, tile_size=16)
    assert m.player_start_px() == (16, 16)


def test_player_start_falls_back_to_first_floor():
    m = TileMap.from_text("###\n#.#\n###", tile_size=10)
    assert m.player_start_px() == (10, 10)


def test_ragged_rows_padded_with_walls():
    m = TileMap.from_text("#####\n#@\n#####", tile_size=8)
    assert m.cols == 5
    assert m.is_blocked(3, 1)  # padding cell
    assert m.is_blocked(4, 1)


def test_blocked_tiles_lists_every_wall():
    m = TileMap.from_text("###\n#.#\n###", tile_size=8)
    assert (1, 1) not in m.blocked_tiles()
    assert len(m.blocked_tiles()) == 8


def test_empty_and_bad_tile_size_rejected():
    with pytest.raises(ValueError):
        TileMap.from_text("\n\n")
    with pytest.raises(ValueError):
        TileMap.from_text("###\n#.#\n###", tile_size=0)
