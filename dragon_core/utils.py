import copy
import time
from decimal import Decimal


def time_us() -> int:
    """ Функция для получения текущего timestamp в микросекундах
    :return: int - timestamp в микросекундах
    """
    return round(time.time() * 1_000_000)


def float_to_decimal(f: float):
    return Decimal(str(f))


def convert_orderbook_float_to_decimal(orderbook: dict):
    decimal_orderbook = copy.deepcopy(orderbook)
    for level in orderbook['asks']:
        decimal_orderbook['asks'].append([float_to_decimal(level[0]), float_to_decimal(level[1])])
    for level in orderbook['bids']:
        decimal_orderbook['bids'].append([float_to_decimal(level[0]), float_to_decimal(level[1])])
    return decimal_orderbook


def convert_balance_float_to_decimal(balance: dict):
    decimal_balance = copy.deepcopy(balance)
    for key, value in balance['assets'].items():
        decimal_balance['assets'][key] = float_to_decimal(value)
    return decimal_balance


def convert_order_float_to_decimal(order: dict):
    decimal_order = copy.deepcopy(order)
    decimal_order['amount'] = float_to_decimal(order['amount'])
    decimal_order['price'] = float_to_decimal(order['price'])
    decimal_order['filled'] = float_to_decimal(order['filled'])
    return decimal_order
