import orjson

from dragon_core.transmitting.transmitter import Transmitter


class LogServer(object):
    def __init__(self, config: dict):
        self.transmitter = Transmitter(
            channel=config['aeron']['publishers']['logs']['channel'],
            stream_id=config['aeron']['publishers']['logs']['stream_id']
        )

    def send(self, message: dict | str):
        self.transmitter.publish(message)
