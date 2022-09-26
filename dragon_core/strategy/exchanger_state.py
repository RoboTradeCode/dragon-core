import dataclasses
from decimal import Decimal

import simplejson


@dataclasses.dataclass
class CoreOrder:
    sell_market_order_price: Decimal = None
    buy_limit_order_price: Decimal = None
    buy_market_order_price: Decimal = None
    sell_limit_order_price: Decimal = None
    buy_profit: Decimal = None
    sell_profit: Decimal = None


@dataclasses.dataclass
class ExchangeState:
    """
    Снимок состояния биржи, включающий всю необходимую актуальную информацию, но без исторической информации.
    """
    name: str
    limit_orders: dict[str, dict] = None
    orderbook: dict = None
    balance: dict = None
    core_orders: dict[str, CoreOrder] = None

    def to_dict(self):
        return {
            'name': self.name,
            'limit_orders': self.limit_orders,
            'orderbook': self.orderbook,
            'balance': self.balance,
            'core_orders': list(self.core_orders.values())
        }
