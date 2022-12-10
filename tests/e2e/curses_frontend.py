"""End-to-end test for curses frontend.

Simply replays the text with huge speed.
"""

import asyncio
from dataclasses import dataclass, field

from cursedtypist import game
from cursedtypist import params
from cursedtypist.frontend import curses_frontend as cf


@dataclass
class CursesReplayController(game.GameController):
    """This controller replays the text automatically with very high speed."""

    text: str
    pos: int = field(default=0)
    cnt: int = field(default=0)

    async def wait_key(self) -> str:
        """Return the next key from the text."""
        # imitate some delay in typing
        await asyncio.sleep(0.015)

        self.cnt += 1
        if self.cnt % 10:
            # get key and advance the pointer
            key = self.text[self.pos]
            self.pos += 1
        else:
            # imitate typos
            key = chr(0)

        return key


@dataclass
class CursesReplayFrontend(cf.CursesFrontend):
    """Frontend with replaying controller."""

    def wrap_run(self, screen: cf._CursesWindow, text: str) -> bool:
        """Run simplified game (without additional screens) in fast tempo."""
        view = cf.CursesView(screen)
        model = game.GameModel(view, text)
        controller = CursesReplayController(model, text)
        return asyncio.get_event_loop().run_until_complete(controller.loop())


def main() -> None:
    """Run replay test."""
    text = (params.DEFAULT_TEXT * 3).replace("\n", " ")
    CursesReplayFrontend().run(text)


if __name__ == "__main__":
    main()
