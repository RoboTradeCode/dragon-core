from decimal import Decimal


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


def get_market_sell_order_price(amount_in_base_token, orderbook):
    market_order_price = predict_price_of_market_sell(amount_in_base_token, orderbook)
    market_order_price = market_order_price
    return market_order_price


def get_price_of_buy_market_order(amount_in_base_token, orderbook):
    market_order_price = predict_price_of_market_buy(amount_in_base_token, orderbook)
    market_order_price = market_order_price
    return market_order_price
