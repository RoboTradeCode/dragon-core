# Dragon-Core

## v1.0

### Настройки стратегии

- `min_profit` - минимальная прибыль, которую должна получить стратегия за цикл. Указывается в процентах.

- `balance_part_to_use` - какую часть доступного баланса должна использовать стратегия для сделки. Указывается в
  процентах.

- `depth_limit` - процент ухода лимитного ордера вглубь ордербука. Регулирует, как сильно может отклоняться цена ордера
  от цены лучшего предложения в ордербуке.

  **Например**, `depth_limit` равен `1.02`. Ордер на продажу выставлен по цене `18 500`. Цена лучшего предложения (бид с
  самой большой ценой) поднялась до `18 950`. Изменение цены `1.024`, что превысило `depth_limit`, ордер будет отменен.
  Это нужно затем, что при уходе вглубь ордербука ордер может не исполниться.

## Установка

1. Установка python 3.10:
    ```bash
    sudo apt update && sudo apt upgrade -y
    sudo apt install software-properties-common -y
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt install python3.10 python3.10-dev python3.10-venv
    ```

2. Клонирование репозитория с исходным кодом ядра:
   ```bash
   git clone https://github.com/RoboTradeCode/test-core-python.git
   ```

3. Установка виртуального окружения venv:
   ```bash
   cd test-core-python
   python3.10 -m venv venv
   ```
4. Активация виртуального окружения:
   ```bash
   source venv/bin/activate
   ```

5. Установка зависимостей ядра:
   ```bash
   pip install -r requirements.txt
   ```
6. Добавление права на запуск:

   ```bash
   sudo chmod +x start.py
   ```

7. Конфигурация ядра. В файле settings.toml нужно написать путь для получения конфигурации. Также на сервере
   конфигуратора (или в файле) должна быть конфигурация с нужными полями для ядра. Пример конфигурации есть в разделе **
   Конфигурация**.

8. Основные этапы установки завершены. Также для работы ядра потребуется Aeron. На момент запуска должен быть запущен
   Media Drive Aeron. Он может быть запущен как в качестве systemd, так и в качестве процесса (т.е. запущен в терминале)
   . Инстркуции по сборке и запуску Aeron можно найти в
   вики [aeron-python](https://github.com/RoboTradeCode/aeron-python/wiki/%D0%A3%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0-Aeron)
   .

9. Рекомендую запустить ядро в целях проверки:
   ```bash
   ./start.py
   ```

## Конфигурация

Способ получения конфигурации указан в файле `settings.toml`. Его вид должен быть примерно следующим:

```toml
[configuration]
type = 'api'
path = 'https://configurator.robotrade.io/binance/sandbox?only_new=false'
```

Файл содержит способ получения полной конфигурации торгового сервера. Файл JSON, специфичный для ядра, находится на
сервере конфигуратора и должен иметь следующую структуру:

```json
{
  "strategy": {
    "min_profit": 5,
    "balance_part_to_use": 25,
    "depth_limit": 2
  },
  "exchanges": [
    {
      "exchange": {
        "name": "binance"
      },
      "aeron": {
        "no_subscriber_log_delay": 300,
        "publishers": {
          "gate": {
            "channel": "aeron:ipc",
            "stream_id": 1004
          },
          "logs": {
            "channel": "aeron:ipc",
            "stream_id": 1008
          }
        },
        "subscribers": {
          "orderbooks": {
            "channel": "aeron:ipc",
            "stream_id": 1006
          },
          "balances": {
            "channel": "aeron:ipc",
            "stream_id": 1005
          },
          "orders": {
            "channel": "aeron:ipc",
            "stream_id": 1007
          }
        }
      }
    },
    {
      "exchange": {
        "name": "exmo"
      },
      "aeron": {
        "no_subscriber_log_delay": 300,
        "publishers": {
          "gate": {
            "channel": "aeron:ipc",
            "stream_id": 1004
          },
          "logs": {
            "channel": "aeron:ipc",
            "stream_id": 1008
          }
        },
        "subscribers": {
          "orderbooks": {
            "channel": "aeron:ipc",
            "stream_id": 1006
          },
          "balances": {
            "channel": "aeron:ipc",
            "stream_id": 1005
          },
          "orders": {
            "channel": "aeron:ipc",
            "stream_id": 1007
          }
        }
      }
    }
  ],
  "aeron": {
    "publishers": {
      "logs": {
        "channel": "aeron:ipc",
        "stream_id": 1008
      }
    }
  }
}
```

