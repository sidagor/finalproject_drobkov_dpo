# Установка
make install
make build
make package-install

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