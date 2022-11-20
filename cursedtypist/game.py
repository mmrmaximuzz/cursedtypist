"""High-level module for typing game logic."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .params import PLAYER_INIT_OFFSET


class GameView(ABC):
    """Interface between game and underlying drawing system."""

    @abstractmethod
    def init_screen(self) -> None:
        """Draw the initial game scene."""

    @abstractmethod
    def death_screen(self) -> None:
        """Draw the gameover screen in case of player loses."""

    @abstractmethod
    def win_screen(self) -> None:
        """Draw the victory screen in case of player wins."""

    @abstractmethod
    def update_text(self, text: str) -> int:
        """Draw the screen scene with the text given and player offset.

        Return how many symbols have been printed on the screen.
        """

    @abstractmethod
    def print_message(self, msg: str) -> None:
        """Print the game message."""

    @abstractmethod
    def drop_floor(self) -> None:
        """Drop one floor cell."""

    @abstractmethod
    def move_player(self) -> None:
        """Move player one step futher."""

    @abstractmethod
    def refresh(self) -> None:
        """Refresh the screen."""


class GameModel:
    """Cursed typist game model.

    Contains text to type and player/tracer positions.
    """

    view: GameView
    tracer: int
    player: int
    text: str
    border: int
    finished: asyncio.Future

    def __init__(self, view: GameView, text: str):
        """Create the empty model with given text."""
        self.view = view
        self.tracer = -PLAYER_INIT_OFFSET
        self.player = 0
        self.text = text
        self.finished = asyncio.Future()
        self.view.init_screen()

    def _swap_gamescreen(self) -> None:
        displayed = self.view.update_text(self.text[self.player:])
        self.border = self.player + displayed

    def player_move(self, key: str) -> None:
        """Process player input and try to move player further."""
        if key == self.text[self.player]:
            self.player += 1
            self.view.print_message("")
            self.view.move_player()

            # check whether we should update the text
            if self.player == self.border:
                self._swap_gamescreen()

            # check whether the player wins
            if self.player == len(self.text):
                self.view.win_screen()
                self.finished.set_result(True)
        else:
            self.tracer += 1
            self.view.print_message("WRONG KEY")
            self.view.drop_floor()

            # check whether the player loses
            if self.tracer == self.player:
                self.view.death_screen()
                self.finished.set_result(False)

        self.view.refresh()

    def timer_fired(self) -> None:
        """Crash the floor behind the player."""
        self.tracer += 1
        self.view.drop_floor()

        # check whether the game has ended
        if self.tracer == self.player:
            self.view.death_screen()
            self.finished.set_result(False)

        self.view.refresh()


@dataclass
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

    async def wait_for_completion(self) -> bool:
        """Block until the game is finished."""
        return await self.model.finished
