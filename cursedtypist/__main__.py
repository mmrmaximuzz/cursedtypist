"""Simple typing game.

Main entry point.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .params import DEFAULT_TEXT
from .frontend import Frontend


def get_game_text(path: Optional[Path]) -> str:
    """Get the game text by given path."""
    if path is None:
        # if no text provided, use default text
        return DEFAULT_TEXT

    # try to read the text under the path given
    try:
        return path.read_text(errors="strict")
    except OSError as err:
        print(f"cannot open file: {err}")
        sys.exit(1)


def prepare_game_text(path: Optional[Path]) -> str:
    """Prepare text for the game."""
    text = get_game_text(path)
    return " ".join(line.strip() for line in text.splitlines())


def prepare_frontend(frontend: str) -> Frontend:
    """Choose the frontend for the cursedtypist game."""
    if frontend == "curses":
        from .frontend.curses_frontend import CursesFrontend
        return CursesFrontend()

    # unreachable because of argparse choices
    raise AssertionError(frontend)


def cli_parser() -> argparse.ArgumentParser:
    """Create a CLI argument parser for the cursedtypist game."""
    parser = argparse.ArgumentParser(prog="cursedtypist")
    parser.add_argument("--text", dest="path", type=Path, default=None,
                        help="path to text to play")
    parser.add_argument("--frontend", choices=["curses"],
                        default="curses", help="frontend for the game")
    return parser


def main() -> None:
    """Start the game."""
    args = cli_parser().parse_args()

    # do some customization based on CLI args
    text = prepare_game_text(args.path)
    frontend = prepare_frontend(args.frontend)

    # run the game
    frontend.run(text)


if __name__ == "__main__":
    main()
