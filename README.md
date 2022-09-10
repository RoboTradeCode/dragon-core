# Dragon-Core
## v1.0
	
## Архитектура ядра

Основные компоненты: 

- Strategy - абстрактный класс, реализации которого пишет пользователь (алготрейдер). В нём описан алгоритм торговой стратегии, который использует Trader для получения данных и выставления ордеров. Будет использоваться для написания тестовых сценариев.
- Trader - отвечает за взаимодействие с Gate. Хранит и обновляет данные, отправляет команды. Логгирует действия стратегии.
- Communicator - класс, который используется для взаимодействия с лог-сервером и Gate. 


![Core Architecture(2)(3)(1)(1)-Page-1](https://user-images.githubusercontent.com/66905267/182893172-c8dba1de-622f-4dfe-bfbe-1c98e87ad0b1.jpg)


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
 
7. Конфигурация ядра. В файле settings.toml нужно написать путь для получения конфигурации. Также на сервере конфигуратора (или в файле) должна быть конфигурация с нужными полями для ядра. Пример конфигурации есть в разделе **Конфигурация**.

8. Основные этапы установки завершены. Также для работы ядра потребуется Aeron. На момент запуска должен быть запущен Media Drive Aeron. Он может быть запущен как в качестве systemd, так и в качестве процесса (т.е. запущен в терминале). Инстркуции по сборке и запуску Aeron можно найти в вики [aeron-python](https://github.com/RoboTradeCode/aeron-python/wiki/%D0%A3%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0-Aeron).

9. Рекомендую запустить ядро в целях проверки:
	```bash
	./start.py orderbook-testing
	```
	
## Использование
Ядро реализует несложный интерфейс команной строки. Запуск ядра в определенном режиме (см. типы тестирования) можно выполнить с помощью команд такого формата:

```bash
./start.py <тип тестирования>
```

Например:
```bash
./start.py fast-testing 
```
```bash
./start.py breaking-testing
```

Вызов справки по стратегии:
```bash
./start.py breaking-testing --help
```

При выполнении такой команды в терминале, будет запущена стратегия ядра. Вывод логов будет осуществляться в этот же терминал. Остановить ядро можно с помощью прерывания Ctrl + C.


## Конфигурация
Способ получения конфигурации указан в файле `settings.toml`. Его вид должен быть примерно следующим:

```toml
[configuration]
    type = 'api'
    path = 'https://configurator.robotrade.io/binance/sandbox?only_new=false'
```
Файл содержит способ получения полной конфигурации торгового сервера. Файл JSON, специфичный для ядра, находится на сервере конфигуратора и должен иметь следующую структуру:

```json
{
  "aeron": {
    "no_subscriber_log_delay": 300,
    "publishers": {
      "gate_input": {
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
      "core_input": {
        "channel": "aeron:ipc",
        "stream_id": 1007
      }
    }
  }
}
```
Описание каналов Aeron:

* gate_input - канал для отправления команд гейту;
* logs - канал для постинга логов;
* orderbooks - канал для получения ордербуков;
* balances - канал для получения балансов;
* core_input - канал для получения статусов ордеров и ошибок;

### 
