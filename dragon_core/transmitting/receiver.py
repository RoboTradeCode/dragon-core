import asyncio
import logging
from typing import Callable, NoReturn

import orjson
from aeron import Subscriber

logger = logging.getLogger(__name__)


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
        try:
            parsed_message = orjson.loads(message)
            self.handler(parsed_message)
        except orjson.JSONDecodeError as e:
            logger.error(f'Json decode error: {e}, on message: {message}')
        except Exception as e:
            logger.error(f'Exception: {e}')

    async def run_poll_loop(self, sleep_time_between_iterations: float = 0.0001) -> NoReturn:
        while True:
            try:
                self.poll()
                await asyncio.sleep(sleep_time_between_iterations)
            except Exception as e:
                logger.error(f'Exception in loop: {e}')
