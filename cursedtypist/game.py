"""High-level module for typing game logic."""

import asyncio
from abc import ABC, abstractmethod

from .params import PLAYER_OFFSET


class GameView(ABC):
    """Interface between game and underlying drawing system."""

    @abstractmethod
    def init_screen(self) -> None:
        """Draw the initial game scene."""

    @abstractmethod
    def death_screen(self, player_pos: int) -> None:
        """Draw the gameover screen in case of player loses."""

    @abstractmethod
    def win_screen(self) -> None:
        """Draw the victory screen in case of player wins."""

    @abstractmethod
    def game_screen(self, text: str, player_pos: int) -> int:
        """Draw the screen scene with the text given.

        Return how many symbols have been drawn of the screen.
        """

    @abstractmethod
    def print_message(self, msg: str) -> None:
        """Print the game message."""

    @abstractmethod
    def clear_text_cell(self, pos: int) -> None:
        """Clear the cell with text under the position."""

    @abstractmethod
    def clear_floor_cell(self, pos: int) -> None:
        """Clear the floor with text under the position."""

    @abstractmethod
    def draw_player(self, pos: int) -> None:
        """Draw player in the given position."""

    @abstractmethod
    def refresh(self) -> None:
        """Refresh the screen."""


class GameModel:
    """Cursed typist game model.

    Contains text to type and player/tracer positions.
    """

    view: GameView
    state: str
    tracer: int
    player: int
    typepos: int
    typetext: str
    fulltext: str
    finished: asyncio.Future

    def __init__(self, view: GameView, text: str):
        """Create the empty model with given text."""
        self.view = view
        self.tracer = 0
        self.player = PLAYER_OFFSET
        self.typepos = 0
        self.typetext = ""
        self.fulltext = text
        self.finished = asyncio.Future()

        self.view.init_screen()
        self.state = "INIT"

    def _swap_gamescreen(self) -> None:
        if not self.fulltext:
            self.view.win_screen()
            self.finished.set_result(None)
            return

        # first clear the old game position
        self.view.clear_text_cell(self.player)

        # then refresh the text on the screen
        self.tracer = 0
        self.player = PLAYER_OFFSET
        displayed = self.view.game_screen(self.fulltext, self.player)
        self.typetext = self.fulltext[:displayed]
        self.fulltext = self.fulltext[displayed:]

    def player_move(self, key: str) -> None:
        """Process player input and try to move player further."""
        if self.state == "INIT":
            self.state = "GAME"
            self._swap_gamescreen()
            return

        if key == self.typetext[self.typepos]:
            self.view.print_message("")
            self.view.clear_text_cell(self.player)
            self.view.draw_player(self.player + 1)
            self.player += 1
            self.typepos += 1

            if self.typepos == len(self.typetext):
                self.typepos = 0
                self._swap_gamescreen()

            self.view.refresh()
        else:
            self.tracer += 1
            self.view.print_message("WRONG KEY")
            self.view.clear_floor_cell(self.tracer)
            self.view.refresh()
            # check whether the game has ended
            if self.tracer == self.player:
                self.view.death_screen(self.player)
                self.finished.set_result(None)
                return

    def timer_fired(self) -> None:
        """Crash the floor behind the player."""
        if self.state == "INIT":
            return

        self.tracer += 1
        self.view.clear_floor_cell(self.tracer)
        self.view.refresh()

        # check whether the game has ended
        if self.tracer == self.player:
            self.view.death_screen(self.player)
            self.finished.set_result(None)
            return


class GameController(ABC):
    """Interface between low-level events and game logic."""

    model: GameModel

    def __init__(self, model: GameModel):
        """Create the game controller."""
        self.model = model

    @abstractmethod
    def read_key(self) -> str:
        """Process keystrokes."""

    def keyboard_event(self) -> None:
        """Handle keypress."""
        key = self.read_key()
        self.model.player_move(key)

    def timer_event(self) -> None:
        """Handle timer event."""
        self.model.timer_fired()

    def running(self) -> bool:
        """Check whether the game is running."""
        return not self.model.finished.done()

    async def wait_for_completion(self) -> None:
        """Block until the game is finished."""
        await self.model.finished
