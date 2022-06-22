import psutil
import asyncio
from db_interactions import write_CPU_load
import sys


class Timer:
    def __init__(self, timeout, callback, args):
        self._timeout = timeout
        self._callback = callback
        self._args = args
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback(self._args)
        self._task = asyncio.ensure_future(self._job())


def main(db_name, timeout):
    timer = Timer(timeout, write_CPU_load, db_name)


def start_load_checking(db_name, timeout):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.call_soon(main, db_name, timeout)
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()