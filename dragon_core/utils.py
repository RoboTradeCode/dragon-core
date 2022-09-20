import time


def time_us() -> int:
    """ Функция для получения текущего timestamp в микросекундах
    :return: int - timestamp в микросекундах
    """
    return round(time.time() * 1_000_000)