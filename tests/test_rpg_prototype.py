"""The standalone entrypoint's non-rendering parts: map loading + CLI parsing."""

import pytest

from src import rpg_prototype


def test_default_map_loads_with_player_start():
    m = rpg_prototype.load_tile_map(None)
    assert m.tile_size == 32
    # default map has an '@' marker
    assert m.player_start_px() == (32, 32)


def test_loads_map_from_yaml_config(tmp_path):
    cfg = tmp_path / "map.yaml"
    cfg.write_text("tile_size: 8\nmap: |\n  ####\n  #@.#\n  ####\n", encoding="utf-8")
    m = rpg_prototype.load_tile_map(str(cfg))
    assert m.tile_size == 8
    assert (m.cols, m.n_rows) == (4, 3)


def test_config_without_map_key_is_rejected(tmp_path):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("tile_size: 8\n", encoding="utf-8")
    with pytest.raises(ValueError):
        rpg_prototype.load_tile_map(str(cfg))


def test_cli_parses_headless_flags():
    args = rpg_prototype.build_parser().parse_args(["--config", "c.yaml", "--max-frames", "5"])
    assert args.config == "c.yaml"
    assert args.max_frames == 5
    assert args.fps == 60
