import json

import requests

from dragon_core.exceptions import InvalidConfigurationSource


def get_configuration_from_api(api_url: str, params: dict = None) -> dict:
    """Receive json from api and parse it to Configuration object"""
    response = requests.request(url=api_url, method='GET')
    json_data = response.json()
    return json_data


def get_configuration_from_file(file_path: str) -> dict:
    """Read json file with configuration and parse it to Configuration object"""
    with open(file_path) as file:
        json_data = json.load(file)
    return json_data


async def receive_configuration(basic_settings: dict) -> dict:
    """Receive full gate configuration from basic settings"""
    match basic_settings.get('type'):
        case 'api':
            if basic_settings.get('path') is None:
                raise InvalidConfigurationSource
            config = get_configuration_from_api(api_url=basic_settings['path'])
        case 'file':
            if basic_settings.get('path') is None:
                raise InvalidConfigurationSource
            config = get_configuration_from_file(file_path=basic_settings['path'])
        case _:
            raise InvalidConfigurationSource
    return config
