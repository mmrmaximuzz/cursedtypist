"""
High-level module for typing game logic
"""

from abc import ABC, abstractmethod
from typing import Callable

from .params import PLAYER_OFFSET


class GameView(ABC):
    """Interface between game and underlying drawing system"""

    @abstractmethod
    def init_screen(self):
        """Draw the initial game scene"""

    @abstractmethod
    def death_screen(self, player_pos: int):
        """Draw the gameover screen in case of player loses"""

    @abstractmethod
    def win_screen(self):
        """Draw the victory screen in case of player wins"""

    @abstractmethod
    def game_screen(self, text: str) -> str:
        """Draw the screen scene with the text given.
        Returns the rest of the text that have not fit in the screen
        """

    @abstractmethod
    def clear_text_cell(self, pos: int):
        """Clear the cell with text under the position"""

    @abstractmethod
    def clear_floor_cell(self, pos: int):
        """Clear the floor with text under the position"""

    @abstractmethod
    def draw_player(self, pos: int):
        """Draw player in the given position"""

    @abstractmethod
    def refresh(self):
        """Refresh the screen if the drawing system uses incremental updates"""


class GameModel:
    """Cursed typist game model.

    Contains text to type and player/tracer positions.
    """

    view: GameView
    tracer: int
    player: int
    typepos: int
    typetext: str
    fulltext: str

    def __init__(self, view: GameView, text: str):
        """Creates the empty model with given text"""
        self.view = view
        self.tracer = 0
        self.player = PLAYER_OFFSET
        self.typepos = 0
        self.typetext = ""
        self.fulltext = text

        self.view.init_screen()
        self.state = "INIT"

    def _swap_gamescreen(self):
        if not self.fulltext:
            self.view.win_screen()
            raise RuntimeError  # FIXME: use own game exception

        # first clear the old game position
        self.view.clear_text_cell(self.player)

        # then refresh the text on the screen
        self.tracer = 0
        self.player = PLAYER_OFFSET
        displayed = self.view.game_screen(self.fulltext, self.player)
        self.typetext = self.fulltext[:displayed]
        self.fulltext = self.fulltext[displayed:]

    def player_move(self, key: str):
        """Process player input and try to move player further"""

        if self.state == "INIT":
            self.state = "GAME"
            self._swap_gamescreen()
            return

        if key == self.typetext[self.typepos]:
            self.view.clear_text_cell(self.player)
            self.view.draw_player(self.player + 1)
            self.player += 1
            self.typepos += 1

            if self.typepos == len(self.typetext):
                self.typepos = 0
                self._swap_gamescreen()

            self.view.refresh()

    def timer_fired(self):
        """Timer fired, crash the floor behind the player"""

        if self.state == "INIT":
            return

        self.tracer += 1
        self.view.clear_floor_cell(self.tracer)
        self.view.refresh()

        # check whether the game has ended
        if self.tracer == self.player:
            self.view.death_screen(self.player)
            raise RuntimeError  # FIXME: use own game exception


class GameController:
    """Interface between low-level events and game logic"""

    model: GameModel
    key_hook: Callable

    def __init__(self, model: GameModel, key_hook: Callable):
        """Create the game controller"""
        self.model = model
        self.key_hook = key_hook

    def keyboard_event(self):
        """Player pressed the button"""
        key = self.key_hook()
        self.model.player_move(key)

    def timer_event(self):
        """Timer fired event"""
        self.model.timer_fired()
