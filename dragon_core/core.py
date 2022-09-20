import asyncio
import logging
import time
import uuid
from decimal import Decimal

from dragon_core.gate import Gate
from dragon_core.strategy.spread_strategy import SpreadStrategy
from dragon_core.utils import time_us

logger = logging.getLogger(__name__)


class Core(object):
    def __init__(self, config):
        self.instance = config['instance']
        self.algo = config['algo']
        self.assets = [asset['common'] for asset in config['data']['assets_labels']]

        core_config = config['data']['configs']['core_config']
        self.exchange_1_name = core_config['exchanges'][0]['exchange']['name']
        self.exchange_2_name = core_config['exchanges'][1]['exchange']['name']

        self.gate_1 = Gate(
            config=core_config['exchanges'][0],
            orderbooks_handler=self.handle_orderbooks,
            orders_handler=self.handle_orders,
            balances_handler=self.handle_balances
        )
        self.gate_2 = Gate(
            core_config['exchanges'][1],
            orderbooks_handler=self.handle_orderbooks,
            orders_handler=self.handle_orders,
            balances_handler=self.handle_balances
        )
        self.strategy = SpreadStrategy(
            min_profit=Decimal(core_config['strategy']['min_profit']),
            balance_part_to_use=Decimal(core_config['strategy']['balance_part_to_use']),
            depth_limit=Decimal(core_config['strategy']['depth_limit']),
            exchange_1_name=self.exchange_1_name,
            exchange_2_name=self.exchange_2_name
        )

    async def execute(self):
        logger.info('Cancel all orders and request balances on exchanges.')
        self.send_initial_commands()

        logger.info('Starting core loops...')
        loops = self.get_loops()
        await asyncio.gather(*loops)

    def send_initial_commands(self):
        # cancel all orders
        cancel_all_orders_command = self.get_command_template()
        cancel_all_orders_command['action'] = 'cancel_all_orders'
        cancel_all_orders_command['exchange'] = self.exchange_1_name
        self.gate_1.send_to_gate(message=cancel_all_orders_command)
        cancel_all_orders_command['exchange'] = self.exchange_2_name
        self.gate_2.send_to_gate(message=cancel_all_orders_command)

        # get balance
        get_balance_command = self.get_command_template()
        get_balance_command['action'] = 'get_balance'
        get_balance_command['exchange'] = self.exchange_1_name
        self.gate_1.send_to_gate(message=get_balance_command)
        get_balance_command['exchange'] = self.exchange_2_name
        self.gate_2.send_to_gate(message=get_balance_command)



    def get_command_template(self) -> dict:
        return {
            "event_id": str(uuid.uuid4()),
            "event": "command",
            "exchange": None,
            "node": "core",
            "instance": self.instance,
            "algo": self.algo,
            "action": None,
            "message": None,
            "timestamp": time_us(),
            "data": None
        }

    def get_loops(self):
        loops = self.gate_1.get_loops() + self.gate_2.get_loops()
        return loops

    def handle_orderbooks(self, message: dict):
        commands = self.strategy.update_orderbook(exchange_name=message['exchange'], orderbook=message['data'])
        if commands:
            self.send_commands(commands)

    def handle_orders(self, message: dict):
        if message['action'] in ['orders_update', 'create_orders', 'get_orders', 'cancel_orders']:
            commands = self.strategy.update_orders(exchange_name=message['exchange'], orders=message['data'])
            if commands:
                self.send_commands(commands)
        else:
            logger.info(f'Received message: {message}')

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
