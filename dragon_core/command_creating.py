import time


def cancel_order(exchange: str, client_order_id, symbol):
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


def create_order(exchange: str, client_order_id, symbol, amount, price, side, type: str):
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
