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
    for i, level in enumerate(orderbook['asks']):
        decimal_orderbook['asks'][i] = [float_to_decimal(level[0]), float_to_decimal(level[1])]
    for i, level in enumerate(orderbook['bids']):
        decimal_orderbook['bids'][i] = [float_to_decimal(level[0]), float_to_decimal(level[1])]
    return decimal_orderbook


def convert_balance_float_to_decimal(balance: dict):
    decimal_balance = copy.deepcopy(balance)
    for asset, asset_balance in balance['assets'].items():
        for key, value in asset_balance.items():
            decimal_balance['assets'][asset][key] = float_to_decimal(value)
    return decimal_balance


def convert_order_float_to_decimal(order: dict):
    decimal_order = copy.deepcopy(order)
    decimal_order['amount'] = float_to_decimal(order['amount'])
    decimal_order['price'] = float_to_decimal(order['price'])
    decimal_order['filled'] = float_to_decimal(order['filled'])
    return decimal_order
