from aeron import Subscriber


class Receiver(object):
    _channel: str
    _stream_id: int
    _subscriber: Subscriber

    def __init__(self, channel: str, stream_id: int):
        self._subscriber = Subscriber(handler=self._handle, channel=channel, stream_id=stream_id)

    def poll(self):
        self._subscriber.poll()

    def _handle(self):
        ...
