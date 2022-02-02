"""Simple typing game.

Main entry point.
"""

import curses
import sys
from typing import Any, TYPE_CHECKING

from .events import run_event_loop
from .game import GameModel, GameController
from .screen import CursesView
from .params import DEFAULT_TEXT

# ugly hack required because curses module does not provide typing hints
if TYPE_CHECKING:
    from _curses import _CursesWindow
else:
    _CursesWindow = Any


def curses_main(screen: _CursesWindow, text: str) -> None:
    """Start the game in curses context."""
    class CursesController(GameController):
        """Derived class with curses-based read_key implementation."""

        def read_key(self) -> str:
            return screen.getkey()

    view = CursesView(screen)
    model = GameModel(view, text)
    controller = CursesController(model)

    # run until game over
    run_event_loop(controller)

    # refresh the screen now to not to lose last update
    screen.refresh()

    # waiting for quit key
    while True:
        key = screen.getkey()
        if key == "q":
            break


def prepare_text() -> str:
    """Prepare text for the game."""
    if len(sys.argv) == 1:
        # if no CLI arguments provided, use default text
        text = DEFAULT_TEXT
    elif len(sys.argv) == 2:
        # try to read the text under the path given
        try:
            with open(sys.argv[1], encoding='utf8') as file:
                text = file.read()
        except OSError as err:
            print(f"cannot open file: {err}")
            sys.exit(1)
    else:
        print("usage: python3 -m cursedtypist [PATH_TO_TEXT]")
        sys.exit(1)

    return " ".join(line.strip() for line in text.splitlines())


def main() -> None:
    """Start the game."""
    # get the text for playing
    text = prepare_text()

    # run the main function into curses wrapper
    curses.wrapper(curses_main, text)


if __name__ == "__main__":
    main()
