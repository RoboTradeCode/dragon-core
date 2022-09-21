import uuid
from decimal import Decimal

from dragon_core.utils import float_to_decimal, time_us, convert_orderbook_float_to_decimal, \
    convert_order_float_to_decimal, convert_balance_float_to_decimal


def test_float_to_decimal():
    assert float_to_decimal(1.2) == Decimal('1.2')


def test_convert_orderbook_float_to_decimal():
    timestamp = time_us()
    decimal_orderbook = {
        'bids': [
            [Decimal('17000'), Decimal('5')],
            [Decimal('16500'), Decimal('7')],
            [Decimal('16000'), Decimal('10.5')]
        ],
        'asks': [
            [Decimal('19000'), Decimal('10')],
            [Decimal('19500'), Decimal('15')],
            [Decimal('20000'), Decimal('30')]
        ],
        'symbol': 'BTC/USDT',
        'timestamp': timestamp
    }
    float_orderbook = {
        'bids': [
            [17000, 5],
            [16500, 7],
            [16000, 10.5]
        ],
        'asks': [
            [19000, 10],
            [19500, 15],
            [20000, 30]
        ],
        'symbol': 'BTC/USDT',
        'timestamp': timestamp
    }
    assert convert_orderbook_float_to_decimal(float_orderbook) == decimal_orderbook


def test_convert_balance_float_to_decimal():
    timestamp = time_us()
    decimal_balance = {'assets': {
        'BTC': {
            'free': Decimal('1.5'),
            'used': Decimal('0'),
            'total': Decimal('1.5')
        },
        'USDT': {
            'free': Decimal('25000'),
            'used': Decimal('0'),
            'total': Decimal('25000')
        }
    }}
    float_balance = {'assets': {
        'BTC': {
            'free': 1.5,
            'used': 0,
            'total': 1.5
        },
        'USDT': {
            'free': 25000,
            'used': 0,
            'total': 25000
        }
    }}
    assert convert_balance_float_to_decimal(float_balance) == decimal_balance


def test_convert_order_float_to_decimal():
    client_order_id = str(uuid.uuid4())
    decimal_order = {
        'client_order_id': client_order_id,
        'symbol': 'BTC/USDT',
        'amount': Decimal('1.2'),
        'price': Decimal('17000'),
        'filled': Decimal('1.2'),
        'status': 'closed',
        'side': 'buy',
        'type': 'limit',
        'info': None
    }


    float_order = {
            'client_order_id': client_order_id,
            'symbol': 'BTC/USDT',
            'amount': 1.2,
            'price': 17000,
            'filled': 1.2,
            'status': 'closed',
            'side': 'buy',
            'type': 'limit',
            'info': None
        }
    assert convert_order_float_to_decimal(float_order) == decimal_order
