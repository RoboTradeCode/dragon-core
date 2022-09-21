import logging
import uuid
from decimal import Decimal

from dragon_core.command_creating import cancel_order, create_order
from dragon_core.strategy.exchanger_state import ExchangeState
from dragon_core.strategy.market_order_price_prediction import predict_price_of_market_sell, predict_price_of_market_buy

logger = logging.getLogger(__name__)


def get_balance_base_asset(exchange_state, symbol):
    """
    Получает баланс базового ассета
    """
    balance = exchange_state.balance['assets'].get(symbol.split('/')[0])
    free_balance = Decimal(str(balance['free']))
    return free_balance


def get_balance_quote_asset(exchange_state, symbol):
    """
    Получает баланс котируемого ассета
    """
    balance = exchange_state.balance['assets'].get(symbol.split('/')[1])
    free_balance = Decimal(str(balance['free']))
    return free_balance


def calculate_profit(base_amount, buy_price, sell_price):
    """
    Вычисляет профит от сделки (в виде коэффициента, например 1.1, в процентах это 10%)
    """
    buy_amount = base_amount * buy_price
    sell_amount = base_amount * sell_price
    profit = sell_amount / buy_amount
    return profit


class SpreadStrategy(object):
    min_profit: Decimal
    balance_part_to_use: Decimal
    depth_limit: Decimal
    order_amount_coefficient: Decimal

    exchange_1: ExchangeState
    exchange_2: ExchangeState

    def __init__(self,
                 min_profit: Decimal,
                 balance_part_to_use: Decimal,
                 depth_limit: Decimal,
                 exchange_1_name,
                 exchange_2_name):
        """
        :param min_profit: минимальный желаемый доход (в процентах, например 2.5, 10, 1000)
        :param balance_part_to_use: какая часть от доступного баланса будет использоваться (в процентах)
        :param depth_limit: коэффициент изменения цены для “углубление” ордера в ордербук (в процентах)
        """
        # перевожу в коэффициент для удобного использования
        self.min_profit = min_profit / 100 + 1
        self.balance_part_to_use = balance_part_to_use / 100 + 1
        self.depth_limit = depth_limit / 100 + 1

        self.exchange_1 = ExchangeState(name=exchange_1_name, limit_orders={}, orderbook={})
        self.exchange_2 = ExchangeState(name=exchange_2_name, limit_orders={}, orderbook={})

    def update_orderbook(self, exchange_name: str, orderbook: dict) -> list:
        """
        Обновить ордербук на бирже
        """
        commands = []
        match exchange_name:
            case self.exchange_1.name:
                self.exchange_1.orderbook[orderbook['symbol']] = orderbook
            case self.exchange_2.name:
                self.exchange_2.orderbook[orderbook['symbol']] = orderbook
            case _:
                print(f'Unexpected exchange: {exchange_name}')
                return []

        if self.exchange_2.limit_orders != {}:
            commands += self.check_positions_to_actual(self.exchange_2, self.exchange_1)
        if self.exchange_1.limit_orders != {}:
            commands += self.check_positions_to_actual(self.exchange_1, self.exchange_2)
        if self.exchange_1.limit_orders == {} or self.exchange_2.limit_orders == {}:
            commands += self.execute_spread_strategy()
        return commands

    def update_orders(self, exchange_name: str, orders: list[dict]) -> list[dict]:
        """
        Обновить ордера на бирже
        """
        commands = []
        if orders and orders is not None:
            for order in orders:
                # маркет ордер не нужно специально обрабатывать, просто логгирую его
                if order['type'] == 'market':
                    print(f'Market order: {order}')
                    continue
                # для лимит ордера нужно пересчитать стратегию
                order_id = self.exchange_1.limit_orders.get('client_order_id', '')
                client_order_id = order.get('client_order_id', '')
                if self.exchange_1.limit_orders.get(client_order_id) is not None:
                    self.exchange_1.limit_orders[client_order_id] = order
                    commands += self.monitor_orders(self.exchange_1, self.exchange_2)
                    if order['status'] != 'open':
                        del self.exchange_1.limit_orders[client_order_id]
                elif self.exchange_2.limit_orders.get(client_order_id) is not None:
                    self.exchange_2.limit_orders[client_order_id] = order
                    commands += self.monitor_orders(self.exchange_2, self.exchange_1)
                    if order['status'] != 'open':
                        del self.exchange_2.limit_orders[client_order_id]
                else:
                    print(f'Unexpected order: {order}')
        return commands

    def update_balances(self, exchange_name, balances):
        """
        Обновить балансы на бирже
        """
        commands = []
        match exchange_name:
            case self.exchange_1.name:
                self.exchange_1.balance = balances
            case self.exchange_2.name:
                self.exchange_2.balance = balances
        return commands

    def monitor_orders(self, exchange_for_limit_order: ExchangeState, exchange_for_market_order: ExchangeState):
        """
        Проверить текущие лимитные ордера на актуальность (прибыльность при условии создания обратного маркет ордера)
        """
        commands = []
        for client_order_id, order in exchange_for_limit_order.limit_orders.items():
            if order['filled'] > 0:
                # создать маркет ордер
                commands.append(create_order(
                    exchange=exchange_for_market_order.name,
                    client_order_id=f'{uuid.uuid4()}|spread_end',
                    symbol=order['symbol'],
                    amount=order['filled'],
                    price=order['price'],
                    type='market',
                    side='buy' if order['side'] == 'sell' else 'sell'
                ))
            if not self.check_order_to_actual(exchange_for_limit_order=exchange_for_limit_order,
                                              exchange_for_market_order=exchange_for_market_order,
                                              client_order_id=client_order_id):
                # отменить ордер
                commands.append(cancel_order(
                    exchange=exchange_for_limit_order.name,
                    symbol=order['symbol'],
                    client_order_id=client_order_id
                ))
        return commands

    def execute_spread_strategy(self) -> list[dict]:
        """
        Запустить просчет создания лимитных ордеров в соответствии со стратегией.
        """
        if not self.exchange_1.balance or not self.exchange_2.balance:
            return []
        commands = []

        for symbol in self.exchange_1.orderbook.keys():
            if symbol not in list(self.exchange_2.orderbook.keys()):
                continue

            commands += self.calculate_buy_limit_order(self.exchange_1, self.exchange_2, symbol)
            commands += self.calculate_sell_limit_order(self.exchange_1, self.exchange_2, symbol)
            commands += self.calculate_buy_limit_order(self.exchange_2, self.exchange_1, symbol)
            commands += self.calculate_sell_limit_order(self.exchange_2, self.exchange_1, symbol)
        return commands

    def calculate_buy_limit_order(self,
                                  exchange_to_market: ExchangeState,
                                  exchange_to_limit: ExchangeState,
                                  symbol: str) -> list:
        """
        Попытка создать прибыльный лимит-ордер (прибыль считается с учетом закрытия ордера обратным маркет ордером)
        :param exchange_to_market: состояние биржи для маркет ордера
        :param exchange_to_limit: состояние биржи для лимит ордера
        :return: список команд
        """
        commands = []
        # если найден аналогичный ордер, то не буду выставлять дублирующий
        for order in exchange_to_limit.limit_orders.values():
            if order['side'] == 'buy':
                return []

        # получаю цену лучшего бида в ордербуке
        limit_order_price = exchange_to_limit.orderbook[symbol]['bids'][0][0]

        # получаю объем, который могу использовать для совершения ордеров на двух биржах
        amount_in_base_token = self.get_available_amount_to_buy_first(exchange_to_limit, exchange_to_market, symbol)

        # получаю цену исполнения маркет-ордера в текущем ордербуке
        market_order_price = predict_price_of_market_sell(amount_in_base_token, exchange_to_market.orderbook[symbol])

        # получаю профит от сделки (в процентах)
        profit = calculate_profit(amount_in_base_token, limit_order_price, market_order_price)

        # проверяю, что профит от сделки больше минимального
        if profit > self.min_profit:
            logger.debug(f'Прибыль: '
                         f'{profit * 100 - 100}% > {self.min_profit * 100 - 100}%')
            # создаю ордер
            client_order_id = f'{uuid.uuid4()}|spread_start'
            order = create_order(
                exchange=exchange_to_limit.name,
                client_order_id=client_order_id,
                symbol=symbol,
                amount=amount_in_base_token,
                price=limit_order_price,
                side='buy',
                type='limit'
            )
            commands.append(order)
            exchange_to_limit.limit_orders[client_order_id] = order['data'][0]
        return commands

    def calculate_sell_limit_order(self,
                                   exchange_to_market: ExchangeState,
                                   exchange_to_limit: ExchangeState,
                                   symbol: str) -> list:
        """
        Попытка создать прибыльный лимит-ордер (прибыль считается с учетом закрытия ордера обратным маркет ордером)
        :param exchange_to_market: состояние биржи для маркет ордера
        :param exchange_to_limit: состояние биржи для лимит ордера
        :param symbol: торговая пара
        :return: список команд
        """
        commands = []
        # если найден аналогичный ордер, то не буду выставлять дублирующий
        for order in exchange_to_limit.limit_orders.values():
            if order['side'] == 'sell':
                return []

        if not exchange_to_limit.balance:
            return []

        # получаю баланс, который можно использовать в ордере
        amount_in_base_token = self.get_available_amount_to_sell_first(exchange_to_limit, exchange_to_market, symbol)

        # получаю цену лучшего аска в ордербуке
        limit_order_price = exchange_to_limit.orderbook[symbol]['asks'][0][0]

        # получаю цену исполнения маркет-ордера в текущем ордербуке
        market_order_price = predict_price_of_market_buy(amount_in_base_token, exchange_to_market.orderbook[symbol])

        # получаю профит от сделки (в процентах)
        profit = calculate_profit(amount_in_base_token, limit_order_price, market_order_price)

        # проверяю, что профит от сделки больше минимального
        if profit > self.min_profit:
            logger.debug(f'Прибыль: '
                         f'{profit * 100 - 100}% > {self.min_profit * 100 - 100}%')
            client_order_id = f'{uuid.uuid4()}|spread_start'
            order = create_order(
                exchange=exchange_to_limit.name,
                client_order_id=client_order_id,
                symbol=symbol,
                amount=amount_in_base_token,
                price=limit_order_price,
                side='sell',
                type='limit'
            )
            commands.append(order)
            exchange_to_limit.limit_orders[client_order_id] = order['data'][0]
        return commands

    def check_positions_to_actual(self, exchange_for_limit_order, exchange_for_market_order) -> list:
        """
        Проверить, что ордера, которые выставлены на бирже, принесут прибыль, если будут исполнены (с учетом
        исполнения маркет ордеров по текущему ордербуку). Для ордеров, которые уже не выгодны, будут возвращены
        команды отмены
        """
        commands = []
        for client_order_id, order in exchange_for_limit_order.limit_orders.items():
            if not self.check_order_to_actual(exchange_for_limit_order=exchange_for_limit_order,
                                              exchange_for_market_order=exchange_for_market_order,
                                              client_order_id=client_order_id):
                # отменить ордер
                commands.append(cancel_order(
                    exchange=exchange_for_limit_order.name,
                    symbol=order['symbol'],
                    client_order_id=order['client_order_id']
                ))
        return commands

    def check_order_to_actual(self,
                              exchange_for_limit_order: ExchangeState,
                              exchange_for_market_order: ExchangeState,
                              client_order_id: str):
        """
        Проверить, что ордер всё ещё будет выгодным, когда исполнится (с учетом, что будет исполнен маркет ордер).
        """
        if order := exchange_for_limit_order.limit_orders.get(client_order_id):
            symbol = order['symbol']
            orderbook_of_exchange_for_limit_order = exchange_for_limit_order.orderbook[symbol]
            orderbook_of_exchange_for_market_order = exchange_for_market_order.orderbook[symbol]
            order_price = order['price']
            base_amount = order['amount']
            quote_amount = order_price * base_amount
            if order['side'] == 'sell':
                # проверка, что сделка выгодная
                predict_price = predict_price_of_market_buy(quote_amount, orderbook_of_exchange_for_limit_order)
                if order_price / predict_price < self.min_profit:
                    return False
                # проверка на достаточный баланс для совершения завершающей сделки
                if quote_amount < get_balance_quote_asset(exchange_for_market_order, symbol):
                    return False
                # проверка на уход вглубь ордербука`
                if orderbook_of_exchange_for_limit_order[symbol]['bids'][0][0] / order_price > self.depth_limit:
                    return False
            else:
                # проверка, что сделка выгодная
                predict_price = predict_price_of_market_sell(base_amount, orderbook_of_exchange_for_market_order)
                if predict_price / order_price < self.min_profit:
                    return False
                # проверка на достаточный баланс для совершения завершающей сделки
                if base_amount < get_balance_base_asset(exchange_for_market_order, symbol):
                    return False
                # проверка на уход вглубь ордербука
                if abs(order_price / orderbook_of_exchange_for_limit_order['asks'][0][0] - 1) > self.depth_limit:
                    return False
            return True
        else:
            logger.error(f'Unexpected client_order_id: {client_order_id}')
            return False

    def get_available_amount_to_sell_first(self, exchange_to_limit, exchange_to_market, symbol: str):
        """
        Функция вычисляет максимальный объем ордера.
        Максимальный объем ордера - объем ордера, который можно исполнить на двух биржах, т.е. выполнив лимитный
        ордер на бирже exchange_to_limit и маркет ордер на exchange_to_market.
        Функция возвращает объем с учетом balance_part_to_use.
        """
        # Получаю цену, по которой будет исполнен маркет ордер
        limit_order_price = exchange_to_limit.orderbook[symbol]['asks'][0][0]
        # получаю баланс на бирже, на которой буду выставлять лимит ордер (quote - в паре BTC/USDT это USDT)
        amount_in_exchange_to_limit = get_balance_quote_asset(exchange_to_limit, symbol) / limit_order_price
        # получаю баланс на бирже, на которой буду выставлять маркет ордер
        amount_in_exchange_to_market = get_balance_base_asset(exchange_to_limit, symbol)

        min_amount = min(amount_in_exchange_to_market, amount_in_exchange_to_limit) * self.balance_part_to_use
        return min_amount

    def get_available_amount_to_buy_first(self, exchange_to_limit, exchange_to_market, symbol: str):
        """
        Функция вычисляет максимальный объем ордера.
        Максимальный объем ордера - объем ордера, который можно исполнить на двух биржах, т.е. выполнив лимитный
        ордер на бирже exchange_to_limit и маркет ордер на exchange_to_market.
        Функция возвращает объем с учетом balance_part_to_use.
        """
        # получаю баланс на бирже, на которой буду выставлять лимит ордер (quote token - в паре BTC/USDT это USDT)
        amount_in_quote_token = get_balance_quote_asset(exchange_to_market, symbol)
        # получаю цену, по которой будет совершен маркет ордер
        predict_price = predict_price_of_market_buy(amount_in_quote_token, exchange_to_market.orderbook[symbol])
        # перевожу из котируемого токена в базовый, чтобы сравнивать два баланса
        amount_in_exchange_to_market = amount_in_quote_token / predict_price
        # получаю баланс базового токена для совершения продажи
        amount_in_exchange_to_limit = get_balance_base_asset(exchange_to_limit, symbol)

        min_amount = min(amount_in_exchange_to_market, amount_in_exchange_to_limit) * self.balance_part_to_use
        return min_amount
