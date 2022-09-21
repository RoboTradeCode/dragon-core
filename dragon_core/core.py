import asyncio
import logging
import uuid
from decimal import Decimal

from dragon_core.gate import Gate
from dragon_core.log_server import LogServer
from dragon_core.strategy.spread_strategy import SpreadStrategy
from dragon_core.utils import time_us, convert_orderbook_float_to_decimal, convert_balance_float_to_decimal, \
    convert_order_float_to_decimal

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
        self.log_server = LogServer(config=core_config)

    async def execute(self):
        # сон на 1 секунду чтобы успели создаться каналы aeron
        await asyncio.sleep(1)

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
        orderbook = convert_orderbook_float_to_decimal(orderbook=message['data'])
        commands = self.strategy.update_orderbook(exchange_name=message['exchange'], orderbook=orderbook)
        if commands:
            self.send_commands(commands)

    def handle_orders(self, message: dict):
        if message['event'] in ['data']:
            logger.debug(f'Received orders: {message}')
            orders = [convert_order_float_to_decimal(order) for order in message['data']]
            commands = self.strategy.update_orders(exchange_name=message['exchange'], orders=orders)
            if commands:
                self.send_commands(commands)
        else:
            # todo временное решение, чтобы не засорять логи этими сообщениями от гейта
            if message.get('message') in ["'NoneType' object has no attribute 'assets'",
                                          "'NoneType' object is not iterable"]:
                return
            logger.warning(f'Received unspecified message: {message}')

    def handle_balances(self, message: dict):
        logger.debug(f'Received balance: {message}')
        balances = convert_balance_float_to_decimal(balance=message['data'])
        commands = self.strategy.update_balances(exchange_name=message['exchange'], balances=balances)
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
