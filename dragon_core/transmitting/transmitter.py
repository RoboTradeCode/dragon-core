import logging

import orjson as orjson
from aeron import Publisher, AeronPublicationNotConnectedError, AeronPublicationAdminActionError, AeronPublicationError

logger = logging.getLogger(__name__)


class Transmitter(object):
    _channel: str
    _stream_id: int
    _publisher: Publisher

    def __init__(self, channel: str, stream_id: int):
        self._publisher = Publisher(channel=channel, stream_id=stream_id)

    def publish(self, message: dict):
        is_successful = False
        message_as_str = str(orjson.dumps(message))
        while not is_successful:
            try:
                self._publisher.offer(message_as_str)
                is_successful = True

            # обработка случая, когда нет подписчика
            except AeronPublicationNotConnectedError:
                logger.warning(f'Subscriber is not connected. Message: {message_as_str}')
                break
            # обработка случая admin actin (сообщение будет отправлено снова)
            except AeronPublicationAdminActionError:
                continue
            # обработка прочих ошибок aeron
            except AeronPublicationError as e:
                logger.warning(f'Error on aeron publishing: {e}')
                break

