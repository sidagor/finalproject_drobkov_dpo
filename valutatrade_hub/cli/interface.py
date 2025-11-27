import shlex
from valutatrade_hub.core.utils import parse_args
from valutatrade_hub.core.usecases import (
    register, login, show_portfolio, 
    buy, sell, get_rate
)

def cli():
    """
    Основной цикл командного интерфейса.
    Пользователь вводит команды, CLI разбирает аргументы и вызывает соответствующие функции.
    """
    while True:
        raw = input("> ")
        if not raw.strip():
            continue

        try:
            parts = shlex.split(raw)
        except ValueError:
            print("Ошибка парсинга команды")
            continue

        cmd = parts[0]
        args = parts[1:]

        if cmd == "register":
            params = parse_args(args, ["--username", "--password"])
            username = params.get("--username")
            password = params.get("--password")
            if username and password:
                try:
                    print(register(username, password))
                except ValueError as e:
                    print(e)
            else:
                print("Укажите --username и --password")

        elif cmd == "login":
            login(args)

        elif cmd == "show-portfolio":
            show_portfolio(args)

        elif cmd == "buy":
            buy(args)

        elif cmd == "sell":
            sell(args)

        elif cmd == "get-rate":
            get_rate(args)

        elif cmd in ("exit", "quit"):
            print("Выход из CLI")
            break

        else:
            print("Неизвестная команда")
