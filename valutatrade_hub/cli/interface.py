import shlex

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import (
    buy,
    get_rate,
    login,
    print_help,
    register,
    sell,
    show_portfolio,
    show_rates,
    update_rates,
)
from valutatrade_hub.core.utils import parse_args


def cli():
    """
    Основной цикл командного интерфейса.
    """

    print_help()

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

        try:
            if cmd == "register":
                params = parse_args(args, ["--username", "--password"])
                username = params.get("--username")
                password = params.get("--password")
                if username and password:
                    print(register(username, password))
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
                params = parse_args(args, {"--from", "--to"})
                from_code = params.get("--from")
                to_code = params.get("--to")
                if not from_code or not to_code:
                    print("Использование: get-rate --from USD --to BTC")
                else:
                    get_rate(from_code, to_code)

            elif cmd == "update-rates":
                parts = parse_args(args, ["--source"])
                update_rates(parts.get("--source"))

            elif cmd == "show-rates":
                parts = parse_args(args, ["--currency", "--top", "--base"])
                show_rates(
                    currency=parts.get("--currency"),
                    top=int(parts.get("--top")) if parts.get("--top") else None,
                    base=parts.get("--base") or "USD"
                )    
            elif cmd in ("--help", "help"):
                print_help()


            elif cmd in ("exit", "quit"):
                print("Выход из CLI")
                break

            else:
                print("Неизвестная команда")

        except InsufficientFundsError as e:           
            print(e)

        except CurrencyNotFoundError as e:            
            print(e)
            print(
                "Используйте 'get-rate --help' "
                "или выведите список поддерживаемых валют."
            )

        except ApiRequestError as e:
            print(f"Ошибка при обращении к внешнему API: {e}")
            print("Повторите попытку позже или "
                  "проверьте подключение к сети.")

        except ValueError as e:        
            print(e)

        except Exception as e:         
            print(f"Неизвестная ошибка: {e}")
