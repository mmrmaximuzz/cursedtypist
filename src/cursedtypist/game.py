"""High-level module for typing game logic."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .params import PLAYER_INIT_OFFSET, TIMER_PERIOD_SEC


class GameView(ABC):
    """Interface between game and underlying drawing system."""

    @abstractmethod
    def init_screen(self) -> None:
        """Draw the initial game scene."""

    @abstractmethod
    def game_screen(self, text: str) -> None:
        """Draw the game screen with the text given."""

    @abstractmethod
    def death_screen(self) -> None:
        """Draw the gameover screen in case of player loses."""

    @abstractmethod
    def win_screen(self) -> None:
        """Draw the victory screen in case of player wins."""

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

    def start(self) -> None:
        """Push the text to the view and start."""
        self.view.game_screen(self.text)

    def player_move(self, key: str) -> None:
        """Process player input and try to move player further."""
        if key == self.text[self.player]:
            self.player += 1
            self.view.print_message("")
            self.view.move_player()

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

    def running(self) -> bool:
        """Check whether the game is running."""
        return not self.model.finished.done()

    @abstractmethod
    async def wait_key(self) -> str:
        """Process keystrokes."""

    async def stdin_actor(self) -> None:
        """Perform async reading from stdin with dirty hack."""
        while True:
            key = await self.wait_key()

            # check exit condition
            if not self.running():
                break

            self.model.player_move(key)

    async def timer_actor(self) -> None:
        """Generate timer events and notify controller."""
        while True:
            await asyncio.sleep(TIMER_PERIOD_SEC)

            # check exit condition
            if not self.running():
                break

            self.model.timer_fired()

    async def loop(self) -> bool:
        """Start the game in asyncio context."""
        self.model.start()
        asyncio.create_task(self.stdin_actor())
        asyncio.create_task(self.timer_actor())
        return await self.model.finished
