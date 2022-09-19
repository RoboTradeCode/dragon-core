from typing import Callable

from dragon_core.transmitting.receiver import Receiver
from dragon_core.transmitting.transmitter import Transmitter


class Gate(object):
    orderbooks_receiver: Receiver
    balances_receiver: Receiver
    orders_receiver: Receiver
    transmitter: Transmitter

    exchange_name: str

    def __init__(self, config: dict,
                 orderbooks_handler: Callable,
                 balances_handler: Callable,
                 orders_handler: Callable,
                 ):
        self.exchange_name = config['exchange']['name']
        self.orderbooks_receiver = Receiver(
            config['aeron']['subscribers']['orderbooks']['channel'],
            config['aeron']['subscribers']['orderbooks']['stream_id'],
            orderbooks_handler
        )
        self.balances_receiver = Receiver(
            config['aeron']['subscribers']['balances']['channel'],
            config['aeron']['subscribers']['balances']['stream_id'],
            balances_handler
        )
        self.orders_receiver = Receiver(
            config['aeron']['subscribers']['orders']['channel'],
            config['aeron']['subscribers']['orders']['stream_id'],
            orders_handler
        )
        self.transmitter = Transmitter(
            config['aeron']['publishers']['gate']['channel'],
            config['aeron']['publishers']['gate']['stream_id'],
        )

    def get_loops(self):
        return [
            self.orderbooks_receiver.run_poll_loop(),
            self.balances_receiver.run_poll_loop(),
            self.orders_receiver.run_poll_loop(),
        ]

    def send_to_gate(self, message: dict):
        self.transmitter.publish(message)
