import orjson as orjson
from aeron import Publisher


class Transmitter(object):
    _channel: str
    _stream_id: int
    _publisher: Publisher

    def __init__(self, channel: str, stream_id: int):
        self._publisher = Publisher(channel=channel, stream_id=stream_id)

    def publish(self, message: dict):
        message_as_str = str(orjson.dumps(message))
        self._publisher.offer(message_as_str)

