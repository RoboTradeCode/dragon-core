import dataclasses


@dataclasses.dataclass
class ExchangeState:
    """
    Снимок состояния биржи, включающий всю необходимую актуальную информацию, но без исторической информации.
    """
    name: str
    limit_orders: dict[str, dict] = None
    orderbook: dict = None
    balance: dict = None
