import time
from decimal import Decimal
from unittest import TestCase

from dragon_core.strategy.market_order_price_prediction import predict_price_of_market_sell, predict_price_of_market_buy
from dragon_core.utils import time_us


class TestPricePrediction(TestCase):
    def test_predict_price_of_market_sell(self):
        order_amount = Decimal('1.5')
        orderbook = {
            'bids': [
                [18000, 0.5],
                [17000, 2],
                [17500, 5.5]
            ],
            'asks': [
                [19000, 1],
                [19500, 1.5],
                [20000, 3]
            ],
            'symbol': 'BTC/USDT',
            'timestamp': time_us()
        }
        result = predict_price_of_market_sell(order_amount, orderbook)
        self.assertAlmostEqual(result, 17333, delta=1)

    def test_predict_price_of_market_buy(self):
        order_amount = Decimal('91000')
        orderbook = {
            'bids': [
                [16500, 0.5],
                [16000, 2],
                [15000, 5.5]
            ],
            'asks': [
                [17000, 1],
                [18000, 2],
                [19000, 6],
                [20000, 10]
            ],
            'symbol': 'BTC/USDT',
            'timestamp': time_us()
        }
        result = predict_price_of_market_buy(order_amount, orderbook)
        self.assertAlmostEqual(result, 18200, delta=1)
