"""Standalone 2D RPG prototype (Phase 1).

Run it directly:

    python src/rpg_prototype.py
    python src/rpg_prototype.py --config configs/rpg_prototype.yaml

Controls: arrow keys or WASD to move, Esc / window-close to quit.

Headless smoke test (no window, exits after N frames):

    SDL_VIDEODRIVER=dummy python src/rpg_prototype.py --max-frames 5
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Support being launched as a loose script: `python src/rpg_prototype.py`.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from rpg.game import RPGGame
    from rpg.tilemap import TileMap
else:  # imported as `src.rpg_prototype`
    from .rpg.game import RPGGame
    from .rpg.tilemap import TileMap

DEFAULT_MAP = """\
################
#@.....#.......#
#......#...##..#
#..##......##..#
#..##..#.......#
#......#..###..#
#..#........#..#
#..#..####..#..#
#.............##
################
"""


def load_tile_map(config_path: str | None) -> TileMap:
    if config_path is None:
        return TileMap.from_text(DEFAULT_MAP)
    import yaml

    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    if "map" not in data:
        raise ValueError(f"{config_path} has no 'map' key")
    return TileMap.from_text(data["map"], tile_size=int(data.get("tile_size", 32)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="2D RPG prototype with basic movement")
    parser.add_argument("--config", default=None, help="YAML file with 'map' and optional 'tile_size'")
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="stop after N frames (headless smoke test)",
    )
    parser.add_argument("--fps", type=int, default=60)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tile_map = load_tile_map(args.config)
    game = RPGGame(tile_map, max_frames=args.max_frames)
    game.run(fps=args.fps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
