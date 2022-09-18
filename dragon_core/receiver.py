import asyncio
from typing import Callable, NoReturn

import orjson
from aeron import Subscriber


class Receiver(object):
    _channel: str
    _stream_id: int
    _subscriber: Subscriber
    handler: Callable

    def __init__(self, channel: str, stream_id: int, handler: Callable):
        self.handler = handler
        self._subscriber = Subscriber(handler=self._base_handler, channel=channel, stream_id=stream_id)

    def poll(self):
        self._subscriber.poll()

    def _base_handler(self, message: str):
        parsed_message = orjson.loads(message)
        self.handler(parsed_message)

    async def run_poll_loop(self, sleep_time_between_iterations: float = 0.0001) -> NoReturn:
        while True:
            self.poll()
            await asyncio.sleep(sleep_time_between_iterations)
