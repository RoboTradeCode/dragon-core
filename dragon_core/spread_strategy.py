import dataclasses
from decimal import Decimal


@dataclasses.dataclass
class ExchangeState:
    name: str
    limit_order: dict = None
    market_order: dict = None
    orderbook: dict = None
    balance: dict = None


def predict_price_of_market_sell(base_asset_amount: Decimal, orderbook: dict):
    """
    Вычислить, по какой цене будет исполнен маркет-ордер на продажу;
    :param base_asset_amount: объем маркет-ордера;
    :param orderbook: текущий ордербук;
    :return: ожидаемая средняя цена исполнения ордера.
    """
    filled_amount_in_base_asset = Decimal('0')
    filled_amount_in_quote_asset = Decimal('0')
    for bid in orderbook['bids']:
        bid_price = Decimal(str(bid[0]))
        bid_amount = Decimal(str(bid[1]))
        remainder = base_asset_amount - filled_amount_in_base_asset
        # Если бида хватает, чтобы заполнить остаток ордера
        if bid_amount > remainder:
            filled_amount_in_quote_asset += bid_price * remainder
            filled_amount_in_base_asset += remainder
        # Если полностью заполняю бид
        else:
            filled_amount_in_quote_asset += bid_price * bid_amount
            filled_amount_in_base_asset += bid_amount

    return filled_amount_in_quote_asset / filled_amount_in_base_asset


def predict_price_of_market_buy(quote_asset_amount: Decimal, orderbook: dict):
    """
    Вычислить, по какой цене будет исполнен маркет-ордер на покупку;
    :param quote_asset_amount: объем маркет-ордера;
    :param orderbook: текущий ордербук;
    :return: ожидаемая средняя цена исполнения ордера.
    """
    filled_amount_in_base_asset = 0
    filled_amount_in_quote_asset = 0
    for ask in orderbook['asks']:
        ask_price = Decimal(str(ask[0]))
        ask_amount = Decimal(str(ask[1]))
        remainder = quote_asset_amount - filled_amount_in_quote_asset
        # Если бида хватает, чтобы заполнить остаток ордера
        if ask_amount * ask_price > remainder:
            filled_amount_in_quote_asset += remainder
            filled_amount_in_base_asset += remainder / ask_price
        # Если полностью заполняю бид
        else:
            filled_amount_in_quote_asset += ask_price * ask_amount
            filled_amount_in_base_asset += ask_amount

    return filled_amount_in_quote_asset / filled_amount_in_base_asset


def check_order_actual(order, orderbook, limit):
    order_price = order['price']
    predict_price = predict_price_of_market_buy(order['price'] * order['amount'], orderbook)
    if abs(order_price / predict_price - 1) > limit:
        return False
    else:
        return True


class SpreadStrategy(object):
    min_profit: Decimal
    reserve: Decimal
    slippage_limit: Decimal

    _orders_to_monitor_1: []
    _orders_to_monitor_2: []

    def __init__(self, min_profit: Decimal, reserve: Decimal, slippage_limit: Decimal):
        """
        :param min_profit: минимальный желаемый доход
        :param reserve: коэффициент резерва ликвидности (от 1)
        :param slippage_limit: коэффициент изменения цены для “углубление” ордера в ордербук (от 1)
        """
        self.min_profit = min_profit
        self.reserve = reserve
        self.slippage_limit = slippage_limit

    def execute(self, exchange_1: ExchangeState, exchange_2: ExchangeState) -> list[dict]:
        """
        Просчитать стратегию. Принимает на вход состояние биржи (балансы, ордербуки, ордера),
        Возвращает список команд;
        :param exchange_1: Состояние биржи 1;
        :param exchange_2: Состояние биржи 2;
        :return: список команд;
        """
        self.monitor_orders(self._orders_to_monitor_1, exchange_1.orderbook)
        self.monitor_orders(self._orders_to_monitor_2, exchange_2.orderbook)

        if not self._orders_to_monitor_1:
            # получаем лимитный ордер
            limit_order_to_buy_on_exchange_1 = self.calculate_buy_limit_order(exchange_1, exchange_2)
            if limit_order_to_buy_on_exchange_1 is not None:
                self._orders_to_monitor_2.append(limit_order_to_buy_on_exchange_1)
                # todo создать лимитный ордер

        if not self._orders_to_monitor_2:
            limit_order_to_buy_on_exchange_2 = self.calculate_buy_limit_order(exchange_1, exchange_2)
            if limit_order_to_buy_on_exchange_2 is not None:
                self._orders_to_monitor_1.append(limit_order_to_buy_on_exchange_2)
                # todo создать лимитный ордер

    def monitor_orders(self, orders_to_monitor: list[dict], orderbook: dict):
        for order in orders_to_monitor:
            if order['filled'] > 0:
                # todo создать маркет ордер
                ...
            if not check_order_actual(order, orderbook, self.slippage_limit):
                # todo отменить ордер
                ...

    def calculate_buy_limit_order(self,
                                  exchange_to_market: ExchangeState,
                                  exchange_to_limit: ExchangeState,
                                  amount_in_base_token: Decimal) -> dict | None:
        # - размер расчетного ордера в base_amount (btc)
        amount_in_base_token = Decimal('1.5')
        # - лучшая цена в ордербуке
        limit_order_price = exchange_to_limit.orderbook['bids'][0][0]
        #  - учет на “дрожание” ликвидности
        amount_in_base_token = amount_in_base_token * self.reserve
        # Находим ликвидность в ордербуке Binance
        market_order_price = predict_price_of_market_sell(amount_in_base_token, exchange_to_market.orderbook)
        market_order_price = market_order_price * self.slippage_limit

        limit_order_amount_in_quote = amount_in_base_token * limit_order_price
        market_order_amount_in_quote = amount_in_base_token * market_order_price
        # Проверяем, что ожидаемый доход от сделки будет больше желаемого (без учета комиссии):
        if limit_order_amount_in_quote / market_order_amount_in_quote < self.min_profit:
            print(f'Недостаточная прибыль: '
                  f'{limit_order_amount_in_quote / market_order_amount_in_quote} < {self.min_profit}')
            return None
        # Ставим Buy_Limit_Order на Exmo
        return {
            'symbol': exchange_to_limit.orderbook['symbol'],
            'amount': amount_in_base_token,
            'price': limit_order_price,
            'side': 'buy',
            'type': 'limit'
        }
