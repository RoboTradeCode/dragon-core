import logging

import simplejson as simplejson
from aeron import Publisher, AeronPublicationNotConnectedError, AeronPublicationAdminActionError, AeronPublicationError

logger = logging.getLogger(__name__)


class Transmitter(object):
    _channel: str
    _stream_id: int
    _publisher: Publisher

    def __init__(self, channel: str, stream_id: int):
        self._publisher = Publisher(channel=channel, stream_id=stream_id)

    def publish(self, message: dict | str):
        if isinstance(message, dict):
            message_as_str = simplejson.dumps(message, use_decimal=True)
        else:
            message_as_str = message

        logger.info(f'Send command: {message_as_str}')

        is_successful = False
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

