import dataclasses
from decimal import Decimal

import simplejson


@dataclasses.dataclass
class ExchangeState:
    """
    Снимок состояния биржи, включающий всю необходимую актуальную информацию, но без исторической информации.
    """
    name: str
    limit_orders: dict[str, dict] = None
    orderbook: dict = None
    balance: dict = None
    sell_market_order_price: Decimal = None
    buy_limit_order_price: Decimal = None
    buy_market_order_price: Decimal = None
    sell_limit_order_price: Decimal = None
    buy_profit: Decimal = None
    sell_profit: Decimal = None

