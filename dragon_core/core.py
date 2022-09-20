import asyncio
import logging
import uuid
from decimal import Decimal

from dragon_core.gate import Gate
from dragon_core.strategy.spread_strategy import SpreadStrategy

logger = logging.getLogger(__name__)


class Core(object):
    def __init__(self, config):
        self.instance = None
        self.algo = None
        self.gate_1 = Gate(
            config=config['exchanges'][0],
            orderbooks_handler=self.handle_orderbooks,
            orders_handler=self.handle_orders,
            balances_handler=self.handle_balances
        )
        self.gate_2 = Gate(
            config['exchanges'][1],
            orderbooks_handler=self.handle_orderbooks,
            orders_handler=self.handle_orders,
            balances_handler=self.handle_balances
        )
        self.strategy = SpreadStrategy(
            min_profit=Decimal(config['strategy']['min_profit']),
            balance_part_to_use=Decimal(config['strategy']['reserve']),
            depth_limit=Decimal(config['strategy']['depth_limit']),
            exchange_1_name='binance',
            exchange_2_name='exmo'
        )

    async def execute(self):
        loops = self.get_loops()
        await asyncio.gather(*loops)

    def get_loops(self):
        loops = self.gate_1.get_loops() + self.gate_2.get_loops()
        return loops

    def handle_orderbooks(self, message: dict):
        commands = self.strategy.update_orderbook(exchange_name=message['exchange'], orderbook=message['data'])
        if commands:
            self.send_commands(commands)

    def handle_orders(self, message: dict):
        commands = self.strategy.update_orders(exchange_name=message['exchange'], orders=message['data'])
        if commands:
            self.send_commands(commands)

    def handle_balances(self, message: dict):
        commands = self.strategy.update_balances(exchange_name=message['exchange'], balances=['data'])
        if commands:
            self.send_commands(commands)

    def send_commands(self, commands):
        for command in commands:
            command['event_id'] = str(uuid.uuid4()),
            command['event'] = 'command',
            command['node'] = 'core',
            command['algo'] = self.algo,
            command['message'] = None,
            command['instance'] = self.instance

            if command['exchange'] == self.gate_1.exchange_name:
                self.gate_1.send_to_gate(command)
            elif command['exchange'] == self.gate_2.exchange_name:
                self.gate_1.send_to_gate(command)
            else:
                logger.error(f'Unexpected exchange: {command}')
