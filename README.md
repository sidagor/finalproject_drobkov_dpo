# Установка
make install
make build
make package-install
для работы сервиса Парсинга установите ключ в виртуальное окружение
export EXCHANGERATE_API_KEY=

## Запуск
make project

## Команды:
help
Список доступных команд            

register --username <имя> --password <пароль>
Регистрация нового пользователя

login --username <имя> --password <пароль>
Вход в систему

show-portfolio
Показать текущий портфель пользователя

buy --currency <валюта> --amount <сумма>
Покупка валюты

sell --currency <валюта> --amount <сумма>
Продажа валюты

get-rate --from <валюта> --to <валюта>
Получить текущий курс валют

update-rates
Обновить курсы валют

show-rates [--currency <валюта>] [--top N] [--base <валюта>]
Показать актуальные курсы из локального кеша с фильтрацией

## Пример использования

> register --username alice --password 1234
Пользователь 'alice' зарегистрирован (id=1)
> login --username alice --password 1234
Вы вошли как 'alice'

> show-portfolio
Портфель пользователя 'alice' (база: USD):
- BTC: 0.4900 → 45449.46 USD
- USD: 3300.1684 → 3300.17 USD
---------------------------------
ИТОГО: 48,749.63 USD

> buy --currency BTC --amount 0.05
Покупка выполнена: 0.0500 BTC по курсу 92754.00 USD/BTC
- BTC: было 0.4900 → стало 0.5400

> sell --currency USD --amount 100
Продажа: 100.0000 USD по курсу 1.00 USD/USD
- USD: было 3500.1684 → стало 3400.1684

> get-rate --from USD --to BTC
Внимание: курс устарел (TTL)
Курс USD→BTC: 0.00001113 (обновлено: 2026-01-08T13:09:02Z)
Обратный курс BTC→USD: 89835.00000

> update-rates
2026-01-08T16:43:52 [INFO] Starting rates update...
2026-01-08T16:43:52 [INFO] Fetching from CoinGecko... OK (3 rates)
2026-01-08T16:43:52 [INFO] Fetching from ExchangeRate-API... OK (3 rates)
2026-01-08T16:43:52 [INFO] Writing 6 rates to data/rates.json
Update successful. Total rates updated: 6. Last refresh: 2026-01-08T13:43:52

> show-rates --top 2
Rates from cache (updated at 2026-01-08T13:43:52Z):
- BTC_USD: 89901.000000 (updated: 2026-01-08T13:43:52Z)
- ETH_USD: 3094.840000 (updated: 2026-01-08T13:43:52Z)
2026-01-08T16:44:21 [INFO] Displayed 2 rates

## Демонстрация полного цикла команд 

https://asciinema.org/a/6AkLf7mruCKXh2ZH

## Демонстрация команд обновления и вывода курса валют    

https://asciinema.org/a/oJt4uHLcc2Ju6sBK

## Демонстрация обработки ошибок 

https://asciinema.org/a/laJCyUzJ8IAEDfrW






