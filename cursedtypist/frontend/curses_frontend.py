"""Frontend for cursedtypist based on builtin `curses` module."""

import curses
import random
from dataclasses import dataclass
from typing import Any, Tuple, TYPE_CHECKING

from . import Frontend

from .. import params
from ..events import run_event_loop
from ..game import GameModel, GameController, GameView

# ugly hack required because curses module does not provide typing hints
if TYPE_CHECKING:
    from _curses import _CursesWindow
else:
    _CursesWindow = Any


@dataclass
class CursesController(GameController):
    """Curses-based implementation for a cursedtypist game controller."""

    screen: _CursesWindow

    def read_key(self) -> str:
        """Read key is implemented via `getkey` in `curses`."""
        return self.screen.getkey()


class CursesView(GameView):
    """Curses graphic implementation for the typing game."""

    screen: _CursesWindow

    def __init__(self, screen: _CursesWindow):
        """Prepare the curses window."""
        curses.curs_set(False)
        self._setup_colors()
        self.screen = screen

    @staticmethod
    def _setup_colors() -> None:
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)

    def _get_limits(self) -> Tuple[int, int]:
        ymax, xmax = self.screen.getmaxyx()
        return ymax - 2, xmax - 2  # compensate borders

    def _clear_title_lines(self) -> None:
        _, xmax = self._get_limits()
        self.screen.addstr(params.TITLE_LINE, 1, " " * xmax)
        self.screen.addstr(params.PROMPT_LINE, 1, " " * xmax)

    @staticmethod
    def _lava_attr() -> int:
        return curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE

    @staticmethod
    def _floor_attr() -> int:
        return curses.color_pair(2) | curses.A_BOLD

    @staticmethod
    def _floor_active_attr() -> int:
        return curses.color_pair(2) | curses.A_BOLD | curses.A_REVERSE

    @staticmethod
    def _text_attr() -> int:
        return curses.color_pair(3) | curses.A_BOLD

    @staticmethod
    def _player_attr() -> int:
        return curses.color_pair(4) | curses.A_BOLD

    def init_screen(self) -> None:
        """Draw the initial screen.

        Draw the border and print the prompt.
        """
        self.screen.clear()
        self.screen.border(0)
        self.screen.addstr(params.TITLE_LINE, 1, params.INIT_TITLE)
        self.screen.addstr(params.PROMPT_LINE, 1, params.INIT_PROMPT)
        self.screen.refresh()

    def death_screen(self, player_pos: int) -> None:
        """Draw the death screen.

        Drop the player character into the lava and set the gameover title.
        """
        self._clear_title_lines()
        self.screen.addstr(params.TITLE_LINE, 1, params.GAMEOVER_TITLE)
        self.screen.addstr(params.PROMPT_LINE, 1, params.GAMEOVER_PROMPT)
        self.screen.addstr(params.PLAYER_LINE, player_pos, " ")
        self.screen.addstr(params.LAVA_LINE, player_pos,
                           params.PLAYER_PIC, self._lava_attr())
        self.screen.refresh()

    def win_screen(self) -> None:
        """Draw the winning screen.

        Just print the winning message.
        """
        self._clear_title_lines()
        self.screen.addstr(params.TITLE_LINE, 1, params.WIN_TITLE)
        self.screen.addstr(params.PROMPT_LINE, 1, params.WIN_PROMPT)
        self.screen.refresh()

    def game_screen(self, text: str, player_pos: int) -> int:
        """Draw/update the game screen.

        As curses windows is limited, just draw the part of the game text. The
        lava is just a random punctuatation characters, and the player char is
        a just a dollar sign.
        """
        self._clear_title_lines()
        self.screen.addstr(params.TITLE_LINE, 1, params.GAME_TITLE)
        self.screen.addstr(params.PROMPT_LINE, 1, params.GAME_PROMPT)
        self.screen.addstr(params.PLAYER_LINE, player_pos,
                           params.PLAYER_PIC, self._player_attr())

        _, xmax = self._get_limits()
        to_display = xmax - player_pos
        display = text[:to_display]
        self.screen.addstr(params.FLOOR_LINE, 1,
                           params.FLOOR_PIC * xmax, self._floor_attr())
        self.screen.addstr(params.PLAYER_LINE, player_pos + 1,
                           display, self._text_attr())
        self.screen.addstr(params.LAVA_LINE, 1,
                           "".join(random.choices(params.LAVA_CHARS, k=xmax)),
                           self._lava_attr())
        self.screen.refresh()
        return to_display

    def print_message(self, msg: str) -> None:
        """Print a new message.

        Print some new message to the special message region. When empty string
        provided, then the message region is cleared.
        """
        if not msg:
            _, xmax = self._get_limits()
            to_fill = xmax - params.MESSAGE_OFFSET
            self.screen.addstr(params.MESSAGE_LINE,
                               params.MESSAGE_OFFSET,
                               " " * to_fill)
        else:
            self.screen.addstr(params.MESSAGE_LINE,
                               params.MESSAGE_OFFSET,
                               msg, self._lava_attr())

    def clear_text_cell(self, pos: int) -> None:
        """Replace one character of text by empty space under `pos`."""
        self.screen.addstr(params.PLAYER_LINE, pos, " ")

    def clear_floor_cell(self, pos: int) -> None:
        """Crash one piece of the floor under `pos`."""
        self.screen.addstr(params.FLOOR_LINE, pos, " ")
        self.screen.addstr(params.FLOOR_LINE, pos + 1,
                           params.FLOOR_PIC, self._floor_active_attr())

    def draw_player(self, pos: int) -> None:
        """Draw the player character under `pos`."""
        self.screen.addstr(params.PLAYER_LINE, pos,
                           params.PLAYER_PIC, self._player_attr())

    def refresh(self) -> None:
        """Refresh the curses screen."""
        self.screen.refresh()


@dataclass
class CursesFrontend(Frontend):
    """Frontend based on `curses` python module."""

    def wrap_run(self, screen: _CursesWindow, text: str) -> bool:
        """Run the game in curses-wrapped environment."""
        view = CursesView(screen)
        model = GameModel(view, text)
        controller = CursesController(model, screen)

        # start the game
        result = run_event_loop(controller)

        # refresh the screen now to not to lose last update
        screen.refresh()

        # waiting for quit key
        while True:
            key = screen.getkey()
            if key == "q":
                break

        return result

    def run(self, text: str) -> bool:
        """Prepare the components and make `curses.wrapper` call."""
        return curses.wrapper(self.wrap_run, text)
