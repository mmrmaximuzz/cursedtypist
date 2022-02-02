"""The low level graphics component.

Provides the drawing subsystem via standard curses module.
"""

import curses
from typing import Any, Tuple, TYPE_CHECKING

from . import params
from .game import GameView


# ugly hack required because curses module does not provide typing hints
if TYPE_CHECKING:
    from _curses import _CursesWindow
else:
    _CursesWindow = Any


class CursesView(GameView):
    """Curses graphic implementation for the typing game"""

    screen: _CursesWindow

    def __init__(self, screen: _CursesWindow):
        """Prepare the curses window"""
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
    def _text_attr() -> int:
        return curses.color_pair(3) | curses.A_BOLD

    @staticmethod
    def _player_attr() -> int:
        return curses.color_pair(4) | curses.A_BOLD

    def init_screen(self) -> None:
        self.screen.clear()
        self.screen.border(0)
        self.screen.addstr(params.TITLE_LINE, 1, params.INIT_TITLE)
        self.screen.addstr(params.PROMPT_LINE, 1, params.INIT_PROMPT)
        self.screen.refresh()

    def death_screen(self, player_pos: int) -> None:
        self._clear_title_lines()
        self.screen.addstr(params.TITLE_LINE, 1, params.GAMEOVER_TITLE)
        self.screen.addstr(params.PROMPT_LINE, 1, params.GAMEOVER_PROMPT)
        self.screen.addstr(params.PLAYER_LINE, player_pos, " ")
        self.screen.addstr(params.LAVA_LINE, player_pos,
                           params.PLAYER_PIC, self._lava_attr())
        self.screen.refresh()

    def win_screen(self) -> None:
        self._clear_title_lines()
        self.screen.addstr(params.TITLE_LINE, 1, params.WIN_TITLE)
        self.screen.addstr(params.PROMPT_LINE, 1, params.WIN_PROMPT)
        self.screen.refresh()

    def game_screen(self, text: str, player_pos: int) -> int:
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
                           params.LAVA_PIC * xmax, self._lava_attr())
        self.screen.refresh()
        return to_display

    def clear_text_cell(self, pos: int) -> None:
        self.screen.addstr(params.PLAYER_LINE, pos, " ")

    def clear_floor_cell(self, pos: int) -> None:
        self.screen.addstr(params.FLOOR_LINE, pos, " ")

    def draw_player(self, pos: int) -> None:
        self.screen.addstr(params.PLAYER_LINE, pos,
                           params.PLAYER_PIC, self._player_attr())

    def refresh(self) -> None:
        self.screen.refresh()
