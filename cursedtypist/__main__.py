"""Simple typing game.

Main entry point.
"""

import curses
import sys

from .events import run_event_loop
from .game import GameModel, GameController
from .screen import CursesView
from .params import DEFAULT_TEXT


def main(screen, text: str):
    def key_hook():
        """Ugly hack used to extract keys directly from curses window"""
        return screen.getkey()

    view = CursesView(screen)
    model = GameModel(view, text)
    controller = GameController(model, key_hook)

    try:
        run_event_loop(controller)
    except RuntimeError:
        screen.refresh()

    # waiting for quit key
    while True:
        key = screen.getkey()
        if key == "q":
            break


if __name__ == "__main__":
    # try to read the text under the path
    try:
        with open(sys.argv[1]) as file:
            text = file.read()
    except Exception:
        # cannot get the text from user so use default text
        text = DEFAULT_TEXT

    text = text.replace("\n", " ").strip()

    # run the main function into curses wrapper
    curses.wrapper(main, text)
