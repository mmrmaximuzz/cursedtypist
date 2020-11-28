"""The low level events module.

Provides the event loop via asyncio
"""

import asyncio
import sys
from typing import Callable

from .params import TIMER_PERIOD_SEC
from .game import GameController


async def timer_watch():
    """Stupid async waiter for the game engine"""
    await asyncio.sleep(TIMER_PERIOD_SEC)


async def stdin_watch():
    """Stupid hack to perform async reading from stdin"""

    # first downgrade the stdin stream to corresponding file descriptior
    stdinfd = sys.stdin.fileno()

    # then register the dumb reader for this fd which does nothing
    future = asyncio.Future()
    loop = asyncio.get_event_loop()
    loop.add_reader(stdinfd, future.set_result, None)

    # and then put this dumb reader into oneshot mode
    future.add_done_callback(lambda f: loop.remove_reader(stdinfd))

    await future


async def event_main_loop(controller: GameController):
    """Main event cycle.

    Start timer and create a watcher to process stdin events asynchonously.
    """
    stdin = asyncio.create_task(stdin_watch())
    timer = asyncio.create_task(timer_watch())
    pending = {stdin, timer}

    while True:
        done, pending = await asyncio.wait(pending,
                                           return_when=asyncio.FIRST_COMPLETED)

        reschedule = set()
        if stdin in done:
            controller.keyboard_event()
            stdin = asyncio.create_task(stdin_watch())
            reschedule.add(stdin)
        if timer in done:
            controller.timer_event()
            timer = asyncio.create_task(timer_watch())
            reschedule.add(timer)

        pending |= reschedule


def run_event_loop(controller: GameController):
    """Transform the current flow into asyncio event loop"""
    asyncio.get_event_loop().run_until_complete(event_main_loop(controller))
