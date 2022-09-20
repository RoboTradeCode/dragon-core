import time
from decimal import Decimal
from unittest import TestCase

from dragon_core.strategy.spread_strategy import SpreadStrategy
from dragon_core.utils import time_us


class TestSpreadStrategy(TestCase):
    def test_strategy_creating(self):
        strategy = SpreadStrategy(
            min_profit=Decimal('5'),
            balance_part_to_use=Decimal('100'),
            depth_limit=Decimal('10'),
            exchange_1_name='binance',
            exchange_2_name='exmo'
        )

    def test_strategy_update_orderbook(self):
        strategy = SpreadStrategy(
            min_profit=Decimal('5'),
            balance_part_to_use=Decimal('100'),
            depth_limit=Decimal('10'),
            exchange_1_name='binance',
            exchange_2_name='exmo'
        )
        orderbook = {
            'bids': [
                [Decimal('18000'), Decimal('0.5')],
                [Decimal('17000'), Decimal('2')],
                [Decimal('17500'), Decimal('5.5')]
            ],
            'asks': [
                [Decimal('19000'), Decimal('1')],
                [Decimal('19500'), Decimal('1.5')],
                [Decimal('20000'), Decimal('3')]
            ],
            'symbol': 'BTC/USDT',
            'timestamp': time_us()
        }
        result = []
        result += strategy.update_orderbook('binance', orderbook)
        self.assertListEqual(result, [], 'Commands present, although not enough data for strategy')
        self.assertEqual(strategy.exchange_1.orderbook['BTC/USDT'], orderbook)

    def test_limit_order_creating(self):
        strategy = SpreadStrategy(
            min_profit=Decimal('5'),
            balance_part_to_use=Decimal('100'),
            depth_limit=Decimal('10'),
            exchange_1_name='binance',
            exchange_2_name='exmo'
        )
        balance = {'assets': {
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
        orderbook_1 = {
            'bids': [
                [Decimal('18400'), Decimal('5')],
                [Decimal('18300'), Decimal('20')],
                [Decimal('182500'), Decimal('55')]
            ],
            'asks': [
                [Decimal('18500'), Decimal('10')],
                [Decimal('18700'), Decimal('15')],
                [Decimal('18900'), Decimal('30')]
            ],
            'symbol': 'BTC/USDT',
            'timestamp': time_us()
        }
        orderbook_2 = {
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
            'timestamp': time_us()
        }
        result = []
        result += strategy.update_balances('binance', balance)
        result += strategy.update_balances('exmo', balance)
        result += strategy.update_orderbook('binance', orderbook_1)
        result += strategy.update_orderbook('binance', orderbook_1)
        result += strategy.update_orderbook('exmo', orderbook_2)
        self.assertEqual(len(result), 1, 'there must be one command from the strategy')
        self.assertEqual(result[0].get('action'), 'create_orders', 'there must be create_orders command action')

    def test_cancel_orders(self):
        strategy = SpreadStrategy(
            min_profit=Decimal('5'),
            balance_part_to_use=Decimal('100'),
            depth_limit=Decimal('10'),
            exchange_1_name='binance',
            exchange_2_name='exmo'
        )
        balance = {'assets': {
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
        orderbook_1 = {
            'bids': [
                [Decimal('18400'), Decimal('5')],
                [Decimal('18300'), Decimal('20')],
                [Decimal('182500'), Decimal('55')]
            ],
            'asks': [
                [Decimal('18500'), Decimal('10')],
                [Decimal('18700'), Decimal('15')],
                [Decimal('18900'), Decimal('30')]
            ],
            'symbol': 'BTC/USDT',
            'timestamp': time_us()
        }
        orderbook_2 = {
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
            'timestamp': time_us()
        }
        result = []
        result += strategy.update_balances('binance', balance)
        result += strategy.update_balances('exmo', balance)
        result += strategy.update_orderbook('binance', orderbook_1)
        result += strategy.update_orderbook('exmo', orderbook_2)
        result += strategy.update_orderbook('binance', orderbook_2)
        self.assertEqual(len(result), 2, 'there must be two command from the strategy')
        self.assertEqual(result[1].get('action'), 'cancel_orders', 'there must be cancel_orders command action')

    def test_market_order(self):
        strategy = SpreadStrategy(
            min_profit=Decimal('5'),
            balance_part_to_use=Decimal('100'),
            depth_limit=Decimal('10'),
            exchange_1_name='binance',
            exchange_2_name='exmo'
        )
        balance = {'assets': {
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
        orderbook_1 = {
            'bids': [
                [Decimal('18400'), Decimal('5')],
                [Decimal('18300'), Decimal('20')],
                [Decimal('182500'), Decimal('55')]
            ],
            'asks': [
                [Decimal('18500'), Decimal('10')],
                [Decimal('18700'), Decimal('15')],
                [Decimal('18900'), Decimal('30')]
            ],
            'symbol': 'BTC/USDT',
            'timestamp': time_us()
        }
        orderbook_2 = {
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
            'timestamp': time_us()
        }
        result = []
        result += strategy.update_balances('binance', balance)
        result += strategy.update_balances('exmo', balance)
        result += strategy.update_orderbook('binance', orderbook_1)
        result += strategy.update_orderbook('exmo', orderbook_2)
        result += strategy.update_orders(
            'binance',
            [
                {
                    'client_order_id': result[0]['data'][0]['client_order_id'],
                    'symbol': 'BTC/USDT',
                    'amount': result[0]['data'][0]['amount'],
                    'price': Decimal('17000'),
                    'filled': result[0]['data'][0]['amount'],
                    'status': 'closed',
                    'side': 'buy',
                    'type': 'limit',
                    'info': None
                }
            ]
        )

        self.assertEqual(len(result), 2, 'there must be two command from the strategy')
        self.assertEqual(result[1].get('action'), 'create_orders', 'there must be create_orders action')
        self.assertEqual(result[1]['data'][0].get('type'), 'market', 'there must be market order')
        self.assertEqual(result[1]['data'][0].get('amount'), result[0]['data'][0].get('amount'), 'order amount must be equal')
        self.assertEqual(strategy.exchange_2.limit_orders, {})

