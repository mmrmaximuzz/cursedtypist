"""Frontend for cursedtypist based on builtin `curses` module."""

import asyncio
import curses
import random
import sys
from dataclasses import dataclass
from typing import Any, Tuple, TYPE_CHECKING

from . import Frontend

from ..game import GameModel, GameController, GameView
from ..params import PLAYER_INIT_OFFSET

# ugly hack required because curses module does not provide typing hints
if TYPE_CHECKING:
    from _curses import _CursesWindow
else:
    _CursesWindow = Any


class Params:
    """Specific params for curses frontend."""

    TITLE_LINE = 1
    INIT_TITLE = "WELCOME TO 'CURSED TYPIST' - STUPID TYPING GAME!"
    GAME_TITLE = "RUN FROM THE LAVA!"
    GAMEOVER_TITLE = "OUCH, YOU HAVE FALLEN INTO THE LAVA!"
    WIN_TITLE = "YOU WIN!"

    PROMPT_LINE = 2
    INIT_PROMPT = "Press any key to start playing"
    GAME_PROMPT = "Type the text to run forward"
    GAMEOVER_PROMPT = "Press q to quit"
    WIN_PROMPT = "You have successfully escaped from lava. Press q to quit"

    PLAYER_LINE = 4
    PLAYER_PIC = "$"

    FLOOR_LINE = 5
    FLOOR_PIC = "="

    # reserve some characters to print floor lag value
    FLOOR_LAG_WIDTH = 6  # minus sign + 4 digits + space
    DRAW_OFFSET = max(FLOOR_LAG_WIDTH, PLAYER_INIT_OFFSET) - PLAYER_INIT_OFFSET

    LAVA_LINE = 6
    LAVA_CHARS = "~#@_+-:?*"

    MESSAGE_LINE = 8
    MESSAGE_COLUMN = 12


@dataclass
class CursesController(GameController):
    """Curses-based implementation for a cursedtypist game controller."""

    screen: _CursesWindow

    async def wait_key(self) -> str:
        """Wait for the data in stdin and get key using `curses`."""
        # first downgrade the stdin stream to corresponding file descriptior
        stdinfd = sys.stdin.fileno()

        # then register the dumb reader for this fd which does nothing
        future: asyncio.Future[None] = asyncio.Future()
        loop = asyncio.get_event_loop()
        loop.add_reader(stdinfd, future.set_result, None)

        # and then put this dumb reader into oneshot mode
        future.add_done_callback(lambda f: loop.remove_reader(stdinfd))

        # await for stdin events
        await future

        # now there is some data in stdin, `getkey` will not block
        return self.screen.getkey()


class CursesView(GameView):
    """Curses graphic implementation for the typing game."""

    screen: _CursesWindow
    player: int
    floor: int

    def __init__(self, screen: _CursesWindow):
        """Prepare the curses window."""
        curses.curs_set(False)
        self._setup_colors()
        self.screen = screen
        self.player = PLAYER_INIT_OFFSET + Params.DRAW_OFFSET
        self.floor = 1 + Params.DRAW_OFFSET

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

    def _clear_title_prompt_lines(self) -> None:
        _, xmax = self._get_limits()
        self.screen.addstr(Params.TITLE_LINE, 1, " " * xmax)
        self.screen.addstr(Params.PROMPT_LINE, 1, " " * xmax)

    def _clear_player_line(self) -> None:
        _, xmax = self._get_limits()
        self.screen.addstr(Params.PLAYER_LINE, 1, " " * xmax)

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

    def _draw_floor_lag(self) -> None:
        fmt = "{:" + str(Params.FLOOR_LAG_WIDTH) + "}"
        self.screen.addstr(Params.FLOOR_LINE, 1, fmt.format(self.floor),
                           self._floor_active_attr())

    def init_screen(self) -> None:
        """Draw the initial screen.

        Draw the border and print the prompt.
        """
        self.screen.clear()
        self.screen.border(0)
        self.screen.addstr(Params.TITLE_LINE, 1, Params.INIT_TITLE)
        self.screen.addstr(Params.PROMPT_LINE, 1, Params.INIT_PROMPT)
        self.screen.refresh()

    def death_screen(self) -> None:
        """Draw the death screen.

        Drop the player character into the lava and set the gameover title.
        """
        self._clear_title_prompt_lines()
        self.screen.addstr(Params.TITLE_LINE, 1, Params.GAMEOVER_TITLE)
        self.screen.addstr(Params.PROMPT_LINE, 1, Params.GAMEOVER_PROMPT)
        self.screen.addstr(Params.PLAYER_LINE, self.player, " ")
        self.screen.addstr(Params.LAVA_LINE, self.player,
                           Params.PLAYER_PIC, self._lava_attr())
        self.screen.refresh()

    def win_screen(self) -> None:
        """Draw the winning screen.

        Just print the winning message.
        """
        self._clear_title_prompt_lines()
        self.screen.addstr(Params.TITLE_LINE, 1, Params.WIN_TITLE)
        self.screen.addstr(Params.PROMPT_LINE, 1, Params.WIN_PROMPT)
        self.screen.refresh()

    def update_text(self, text: str) -> int:
        """Draw/update the game screen.

        As curses window is limited, just draw the part of the game text. The
        lava is random punctuation, and the player char is just a dollar sign.
        """
        self._clear_title_prompt_lines()
        self._clear_player_line()

        old_offset = self.player - self.floor
        self.player = PLAYER_INIT_OFFSET + Params.DRAW_OFFSET
        self.floor = self.player - old_offset

        _, xmax = self._get_limits()
        to_display = xmax - self.player
        display = text[:to_display]

        self.screen.addstr(Params.TITLE_LINE, 1, Params.GAME_TITLE)
        self.screen.addstr(Params.PROMPT_LINE, 1, Params.GAME_PROMPT)
        self.screen.addstr(Params.PLAYER_LINE, self.player,
                           Params.PLAYER_PIC, self._player_attr())
        self.screen.addstr(Params.FLOOR_LINE, max(1, self.floor),
                           Params.FLOOR_PIC * (xmax - max(1, self.floor) + 1),
                           self._floor_attr())
        self.screen.addstr(Params.PLAYER_LINE, self.player + 1,
                           display, self._text_attr())
        self.screen.addstr(Params.LAVA_LINE, 1,
                           "".join(random.choices(Params.LAVA_CHARS, k=xmax)),
                           self._lava_attr())
        if self.floor < 1:
            self._draw_floor_lag()

        self.screen.refresh()
        return to_display

    def print_message(self, msg: str) -> None:
        """Print a new message.

        Print some new message to the special message region. When empty string
        provided, then the message region is cleared.
        """
        if not msg:
            _, xmax = self._get_limits()
            to_fill = xmax - Params.MESSAGE_COLUMN
            self.screen.addstr(Params.MESSAGE_LINE,
                               Params.MESSAGE_COLUMN,
                               " " * to_fill)
        else:
            self.screen.addstr(Params.MESSAGE_LINE,
                               Params.MESSAGE_COLUMN,
                               msg, self._lava_attr())

    def drop_floor(self) -> None:
        """Drop one floor cell."""
        if self.floor < 0:
            self._draw_floor_lag()
        elif self.floor == 0:
            # refill the initial part of the floor
            self.screen.addstr(Params.FLOOR_LINE, 1,
                               Params.FLOOR_PIC * Params.FLOOR_LAG_WIDTH,
                               self._floor_attr())
        else:
            self.screen.addstr(Params.FLOOR_LINE, self.floor, " ")
            self.screen.addstr(Params.FLOOR_LINE, self.floor + 1,
                               Params.FLOOR_PIC, self._floor_active_attr())

        self.floor += 1

    def move_player(self) -> None:
        """Move player one step futher."""
        self.screen.addstr(Params.PLAYER_LINE, self.player, " ")
        self.screen.addstr(Params.PLAYER_LINE, self.player + 1,
                           Params.PLAYER_PIC, self._player_attr())
        self.player += 1

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

        # wait any key to start the game
        _ = screen.getkey()
        model._swap_gamescreen()

        # start the game
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(controller.loop())

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
