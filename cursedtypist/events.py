"""The low level events module.

Provides the event loop via asyncio.
"""

import asyncio
import sys

from .params import TIMER_PERIOD_SEC
from .game import GameController


async def timer_actor(controller: GameController) -> None:
    """Generate timer events and notify controller."""
    while True:
        await asyncio.sleep(TIMER_PERIOD_SEC)

        # check exit condition
        if not controller.running():
            break

        controller.timer_event()


async def stdin_actor(controller: GameController) -> None:
    """Perform async reading from stdin with dirty hack."""
    # first downgrade the stdin stream to corresponding file descriptior
    stdinfd = sys.stdin.fileno()

    while True:
        # then register the dumb reader for this fd which does nothing
        future: asyncio.Future[None] = asyncio.Future()
        loop = asyncio.get_event_loop()
        loop.add_reader(stdinfd, future.set_result, None)

        # and then put this dumb reader into oneshot mode
        future.add_done_callback(lambda f: loop.remove_reader(stdinfd))

        # await for stdin events
        await future

        # check exit condition
        if not controller.running():
            break

        # got keystroke, notify
        controller.keyboard_event()


async def event_main_loop(controller: GameController) -> bool:
    """Run the main event cycle.

    Start timer and create a watcher to process stdin events asynchonously.
    """
    asyncio.create_task(stdin_actor(controller))
    asyncio.create_task(timer_actor(controller))
    return await controller.wait_for_completion()


def run_event_loop(controller: GameController) -> bool:
    """Transform the current flow into asyncio event loop."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(event_main_loop(controller))
