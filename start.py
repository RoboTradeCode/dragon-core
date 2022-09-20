#!./venv/bin/python
# -*- coding: UTF-8 -*-

import asyncio
import logging
import os
import subprocess

import tomli

from dragon_core.core import Core
from dragon_core.receive_configuration import get_configuration_from_api, receive_configuration

# проверяю запущен ли aeron media driver
if subprocess.run('ps -A | grep aeron', shell=True, stdout=None).returncode != 0 and \
        subprocess.run('systemctl is-active --quiet aeron', shell=True, stdout=None).returncode != 0:
    print('Critical: Aeron service is not launched. Please launch Aeron before launching application.')
    exit(1)

# путь до начальной конфигурации (в ней указан способ получения полной конфигурации)
BASIC_SETTINGS_PATH = 'settings.toml'

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


async def load_config():
    # Загрузка начальной конфигурации (в ней указан способ получения полной конфигурации)
    if not os.path.isfile(BASIC_SETTINGS_PATH):
        logger.critical(f'Could not find file with basic settings.'
                        f' Specified file path: "{BASIC_SETTINGS_PATH}".'
                        f' Please make sure the file exists.')
        exit(1)
    with open(BASIC_SETTINGS_PATH, "rb") as f:
        basic_settings = tomli.load(f)
    logger.info('Loaded basic settings for core.')

    # получение полной конфигурации и создание объекта ядра
    config = await receive_configuration(basic_settings=basic_settings['configuration'])
    return config


async def start_core():
    try:
        logger.info('Starting strategy mt_py')
        config = await load_config()
        logger.info('Received configuration')
        core = Core(config=config)
        logger.info('Core created')
        await core.execute()
    except Exception as exception:
        logger.critical(f'Critical error: {exception}.', exc_info=True)
        exit(1)


if __name__ == '__main__':
    asyncio.run(start_core())
