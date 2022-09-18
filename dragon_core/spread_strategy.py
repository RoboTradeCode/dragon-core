import dataclasses
import logging
import time
import uuid
from decimal import Decimal


logger = logging.getLogger(__name__)

@dataclasses.dataclass
class ExchangeState:
    name: str
    limit_order: dict = None
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


def predict_price_of_market_buy(quote_asset_amount: Decimal, orderbook: dict) -> Decimal:
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
    quote_amount = order['price'] * order['amount']
    if order['side'] == 'sell':
        predict_price = predict_price_of_market_buy(quote_amount, orderbook)
        if order_price / predict_price < limit:
            return False
    else:
        predict_price = predict_price_of_market_sell(quote_amount, orderbook)
        if predict_price / order_price < limit:
            return False
    return True


class SpreadStrategy(object):
    min_profit: Decimal
    reserve: Decimal
    slippage_limit: Decimal
    order_amount_coefficient: Decimal

    exchange_1: ExchangeState
    exchange_2: ExchangeState


    def __init__(self,
                 min_profit: Decimal,
                 reserve: Decimal,
                 slippage_limit: Decimal,
                 order_amount_coefficient: Decimal,
                 exchange_1_name,
                 exchange_2_name):
        """
        :param min_profit: минимальный желаемый доход
        :param reserve: коэффициент резерва ликвидности (от 1)
        :param slippage_limit: коэффициент изменения цены для “углубление” ордера в ордербук (от 1)
        """
        self.min_profit = min_profit
        self.reserve = reserve
        self.slippage_limit = slippage_limit
        self.order_amount_coefficient = order_amount_coefficient

        self.exchange_1 = ExchangeState(name=exchange_1_name, limit_order={})
        self.exchange_2 = ExchangeState(name=exchange_2_name, limit_order={})

    def update_orderbook(self, exchange_name: str, orderbook: dict) -> list:
        commands = []
        match exchange_name:
            case self.exchange_1.name:
                self.exchange_1.orderbook = orderbook
            case self.exchange_2.name:
                self.exchange_2.orderbook = orderbook
            case _:
                print(f'Unexpected exchange: {exchange_name}')
                return []

        if self.exchange_2.limit_order != {}:
            commands += self.check_position_to_actual(self.exchange_2)
        if self.exchange_1.limit_order != {}:
            commands += self.check_position_to_actual(self.exchange_1)
        if self.exchange_1.limit_order == {} or self.exchange_2.limit_order == {}:
            commands += self.execute_spread_strategy()
        return commands

    def update_orders(self, exchange_name: str, orders: list[dict]) -> list[dict]:
        commands = []
        for order in orders:
            # маркет ордер не нужно специально обрабатывать, просто логгирую его
            if order['type'] == 'market':
                print(f'Market order: {order}')
                continue
            # для лимит ордера нужно пересчитать стратегию
            order_id = self.exchange_1.limit_order.get('client_order_id', '')
            client_order_id = order.get('client_order_id', '')
            if client_order_id == self.exchange_1.limit_order.get('client_order_id', ''):
                self.exchange_1.limit_order = order
                commands += self.monitor_orders(self.exchange_1, self.exchange_2)
            elif client_order_id == self.exchange_2.limit_order.get('client_order_id', ''):
                self.exchange_2.limit_order = order
                commands += self.monitor_orders(self.exchange_2, self.exchange_1)
            else:
                print(f'Unexpected order: {order}')
        return commands

    def update_balances(self, exchange_name, balances):
        match exchange_name:
            case self.exchange_1.name:
                self.exchange_1.balance = balances
            case self.exchange_2.name:
                self.exchange_2.balance = balances

    def monitor_orders(self, exchange_for_limit_order: ExchangeState, exchange_for_market_order: ExchangeState):
        commands = []
        order = exchange_for_limit_order.limit_order
        if order['filled'] > 0:
            # создать маркет ордер
            commands.append(self.create_order(
                exchange=exchange_for_market_order.name,
                client_order_id=f'{uuid.uuid4()}|spread_end',
                symbol=order['symbol'],
                amount=order['filled'],
                price=order['price'],
                type='market',
                side='buy' if order['side'] == 'sell' else 'sell'
            ))
        if not check_order_actual(order, exchange_for_market_order.orderbook, self.slippage_limit):
            # отменить ордер
            commands.append(self.cancel_order(
                exchange=exchange_for_limit_order.name,
                symbol=order['symbol'],
                client_order_id=order['client_order_id']
            ))
        return commands
    def execute_spread_strategy(self) -> list[dict]:
        if self.exchange_1.orderbook is None or self.exchange_2.orderbook is None:
            return []
        commands = []
        start_time = time.time()
        commands += self.calculate_buy_limit_order(self.exchange_1, self.exchange_2, Decimal('1.5'))
        commands += self.calculate_sell_limit_order(self.exchange_1, self.exchange_2, Decimal('1.5'))
        commands += self.calculate_buy_limit_order(self.exchange_2, self.exchange_1, Decimal('1.5'))
        commands += self.calculate_sell_limit_order(self.exchange_2, self.exchange_1, Decimal('1.5'))
        print(f'time: {time.time() - start_time:.9f}')
        return commands

    def calculate_buy_limit_order(self,
                                  exchange_to_market: ExchangeState,
                                  exchange_to_limit: ExchangeState,
                                  amount_in_base_token: Decimal) -> list:
        """

        :param exchange_to_market: состояние биржи для маркет ордера
        :param exchange_to_limit: состояние биржи для лимит ордера
        :param amount_in_base_token: размер расчетного ордера в base_amount (btc)
        :return: список команд
        """
        commands = []

        amount_in_base_token = amount_in_base_token * self.reserve

        limit_order_price = exchange_to_limit.orderbook['bids'][0][0]

        market_order_price = predict_price_of_market_sell(amount_in_base_token, exchange_to_market.orderbook)
        market_order_price = market_order_price * self.slippage_limit

        profit = self.calculate_profit(amount_in_base_token, limit_order_price, market_order_price)

        if profit > self.min_profit:
            order = self.create_order(
                exchange=exchange_to_limit.name,
                client_order_id=f'{uuid.uuid4()}|spread_start',
                symbol=exchange_to_limit.orderbook['symbol'],
                amount=amount_in_base_token,
                price=limit_order_price,
                side='buy',
                type='limit'
            )
            commands.append(order)
            exchange_to_limit.limit_order = order['data'][0]
        return commands

    def calculate_sell_limit_order(self,
                                  exchange_to_market: ExchangeState,
                                  exchange_to_limit: ExchangeState,
                                  amount_in_base_token: Decimal) -> list:
        """

        :param exchange_to_market: состояние биржи для маркет ордера
        :param exchange_to_limit: состояние биржи для лимит ордера
        :param amount_in_base_token: размер расчетного ордера в base_amount (btc)
        :return: список команд
        """
        commands = []

        amount_in_base_token = amount_in_base_token * self.reserve

        limit_order_price = exchange_to_limit.orderbook['asks'][0][0]

        market_order_price = predict_price_of_market_buy(amount_in_base_token, exchange_to_market.orderbook)
        market_order_price = market_order_price * self.slippage_limit

        profit = self.calculate_profit(amount_in_base_token, limit_order_price, market_order_price)

        if profit < self.min_profit:
            logger.debug(f'Недостаточная прибыль: '
                  f'{profit} < {self.min_profit}')
        else:
            order = self.create_order(
                exchange=exchange_to_limit.name,
                client_order_id=f'{uuid.uuid4()}|spread_start',
                symbol=exchange_to_limit.orderbook['symbol'],
                amount=amount_in_base_token,
                price=limit_order_price,
                side='sell',
                type='limit'
            )
            commands.append(order)
            exchange_to_limit.limit_order = order['data'][0]
        return commands

    def calculate_profit(self, base_amount, buy_price, sell_price):
        buy_amount = base_amount * buy_price
        sell_amount = base_amount * sell_price
        profit = sell_amount / buy_amount
        return profit

    def get_market_sell_order_price(self, amount_in_base_token, exchange):
        market_order_price = predict_price_of_market_sell(amount_in_base_token, exchange.orderbook)
        market_order_price = market_order_price * self.slippage_limit
        return market_order_price

    def get_price_of_buy_market_order(self, amount_in_base_token, exchange):
        market_order_price = predict_price_of_market_buy(amount_in_base_token, exchange.orderbook)
        market_order_price = market_order_price * self.slippage_limit
        return market_order_price

    def cancel_order(self, exchange: str, client_order_id, symbol):
        order = {
            'client_order_id': client_order_id,
            'symbol': symbol,
        }
        command = {
            "exchange": exchange,
            "action": "cancel_orders",
            "timestamp": time.time_ns(),
            "data": [order]
        }
        return command
    def create_order(self, exchange: str, client_order_id, symbol, amount, price, side, type: str):
        order = {
            'client_order_id': client_order_id,
            'symbol': symbol,
            'amount': amount,
            'price': price,
            'side': side,
            'type': type
        }
        command = {
            "exchange": exchange,
            "action": "create_orders",
            "timestamp": time.time_ns(),
            "data": [order]
        }
        return command

    def check_position_to_actual(self, exchange_state) -> list:
        commands = []
        if not check_order_actual(exchange_state.limit_order, exchange_state.orderbook, self.slippage_limit):
            # отменить ордер
            commands.append(self.cancel_order(
                exchange=exchange_state.name,
                symbol=exchange_state.limit_order['symbol'],
                client_order_id=exchange_state.limit_order['client_order_id']
            ))
        return commands

