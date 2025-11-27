import json
import shlex
import hashlib
import secrets
from datetime import datetime
from valutatrade_hub.core.models import User, Portfolio, Wallet

DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.json"
PORTFOLIOS_FILE = f"{DATA_DIR}/portfolios.json"
RATES_FILE = f"{DATA_DIR}/rates.json"

SESSION = {"current_user": None}


def load_json(path):
    """Загружает JSON-файл по указанному пути."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_json(path, data):
    """Сохраняет данные в JSON-файл по указанному пути."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def parse_args(arg_list, allowed):
    """Разбирает список аргументов командной строки."""
    result = {}
    key = None
    for item in arg_list:
        if item in allowed:
            key = item
        else:
            if key:
                result[key] = item
                key = None
    return result


def get_user_by_username(username):
    """Получает словарь данных пользователя по его username."""
    users = load_json(USERS_FILE)
    for u in users:
        if u["username"] == username:
            return u
    return None


def load_portfolio(user_id):
    """Загружает портфель пользователя:"""
    portfolios = load_json(PORTFOLIOS_FILE)
    for p in portfolios:
        if p["user_id"] == user_id:
            wallets = {
                code: Wallet(code, w["balance"])
                for code, w in p.get("wallets", {}).items()
            }
            return {"user_id": user_id, "wallets": wallets}
    return None


def save_portfolios():
    """Сохраняет текущее состояние портфеля"""
    users_portfolios = load_json(PORTFOLIOS_FILE)
    result = []
    for p in users_portfolios:
        if p["user_id"] == SESSION["current_user"].user_id:
            portfolio = SESSION["current_user"].portfolio
            data = {code: {"balance": w.balance} for code, w in portfolio.wallets.items()}
            result.append({"user_id": p["user_id"], "wallets": data})
        else:
            result.append(p)
    save_json(PORTFOLIOS_FILE, result)


def load_rates():
    """Загружает таблицу курсов валют из rates.json."""
    try:
        with open(RATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_rate(a, b):
    """Получает обменный курс"""
    rates = load_rates()
    if a in rates and b in rates[a]:
        return rates[a][b]
    return None

def register(username: str, password: str):
    """Регистрация нового пользователя"""
    users = load_json(USERS_FILE)

    for u in users:
        if u["username"] == username:
            raise ValueError(f"Имя пользователя '{username}' уже занято")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    user_id = max([u["user_id"] for u in users], default=0) + 1

    salt = secrets.token_hex(8)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()

    new_user = {
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed,
        "salt": salt,
        "registration_date": datetime.utcnow().isoformat(),
    }

    users.append(new_user)
    save_json(USERS_FILE, users)

    portfolios = load_json(PORTFOLIOS_FILE)
    portfolios.append({"user_id": user_id, "wallets": {}})
    save_json(PORTFOLIOS_FILE, portfolios)

    return f"Пользователь '{username}' зарегистрирован (id={user_id})."


def login(args):
    """Авторизация пользователя."""
    parts = parse_args(args, ["--username", "--password"])
    username = parts.get("--username")
    password = parts.get("--password")

    if not username or not password:
        print("Укажите --username и --password")
        return

    user_data = get_user_by_username(username)
    if not user_data:
        print(f"Пользователь '{username}' не найден")
        return

    user = User(
        user_id=user_data["user_id"],
        username=user_data["username"],
        hashed_password=user_data["hashed_password"],
        salt=user_data["salt"],
        registration_date=datetime.fromisoformat(user_data["registration_date"]),
    )

    if not user.verify_password(password):
        print("Неверный пароль")
        return

    portfolio = load_portfolio(user.user_id)
    user.portfolio = Portfolio(user_id=user.user_id, wallets=portfolio["wallets"])

    SESSION["current_user"] = user
    print(f"Вы вошли как '{username}'")


def show_portfolio(args):
    """Показывает портфель пользователя"""
    if SESSION["current_user"] is None:
        print("Сначала выполните login")
        return

    parts = parse_args(args, ["--base"])
    base = parts.get("--base", "USD").upper()
    user = SESSION["current_user"]

    portfolio = user.portfolio
    if not portfolio.wallets:
        print("У вас пока нет кошельков")
        return

    rates = load_rates()
    if base not in rates:
        print(f"Неизвестная базовая валюта '{base}'")
        return

    print(f"Портфель пользователя '{user.username}' (база: {base}):")

    total = 0
    for code, wallet in portfolio.wallets.items():
        bal = wallet.balance
        if code == base:
            conv = bal
        else:
            r = get_rate(code, base)
            conv = bal * r if r else 0

        total += conv
        print(f"- {code}: {bal:.4f} → {conv:.2f} {base}")

    print("---------------------------------")
    print(f"ИТОГО: {total:.2f} {base}")


def buy(args):
    """покупка валюты"""
    user = SESSION["current_user"]
    if not user:
        print("Сначала выполните login")
        return

    params = parse_args(args, {"--currency", "--amount"})
    currency = params.get("--currency")
    amount = params.get("--amount")

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except:
        print("'amount' должен быть положительным числом")
        return

    currency = currency.upper()
    portfolio = user.portfolio

    if currency not in portfolio.wallets:
        portfolio.add_currency(currency)

    wallet = portfolio.wallets[currency]
    before = wallet.balance
    wallet.balance += amount

    rate = get_rate(currency, "USD")
    if rate is None:
        print(f"Не удалось получить курс для {currency}→USD")
        return

    cost = amount * rate
    save_portfolios()

    print(f"Покупка выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}")
    print("Изменения в портфеле:")
    print(f"- {currency}: было {before:.4f} → стало {wallet.balance:.4f}")
    print(f"Оценочная стоимость покупки: {cost:,.2f} USD")


def sell(args):
    """Продажа валюты"""
    user = SESSION["current_user"]
    if not user:
        print("Сначала выполните login")
        return

    params = parse_args(args, {"--currency", "--amount"})
    currency = params.get("--currency")
    amount = params.get("--amount")

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except:
        print("'amount' должен быть положительным числом")
        return

    currency = currency.upper()
    portfolio = user.portfolio

    if currency not in portfolio.wallets:
        print(f"У вас нет кошелька '{currency}'. Добавьте валюту покупкой.")
        return

    wallet = portfolio.wallets[currency]

    if wallet.balance < amount:
        print(f"Недостаточно средств: доступно {wallet.balance:.4f} {currency}, требуется {amount:.4f} {currency}")
        return

    before = wallet.balance
    wallet.balance -= amount

    rate = get_rate(currency, "USD")
    if rate is None:
        print(f"Не удалось получить курс для {currency}→USD")
        return

    revenue = amount * rate

    if "USD" not in portfolio.wallets:
        portfolio.add_currency("USD")

    portfolio.wallets["USD"].balance += revenue
    save_portfolios()

    print(f"Продажа: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}")
    print("Изменения в портфеле:")
    print(f"- {currency}: было {before:.4f} → стало {wallet.balance:.4f}")
    print(f"Оценочная выручка: {revenue:,.2f} USD")


def get_rate_cmd(args):
    """получает текущий курс одной валюты к другой."""
    params = parse_args(args, {"--from", "--to"})
    c_from = params.get("--from", "").upper()
    c_to = params.get("--to", "").upper()

    if not c_from or not c_to:
        print("Использование: get-rate --from USD --to BTC")
        return

    rate = get_rate(c_from, c_to)
    if rate is None:
        print(f"Курс {c_from}→{c_to} недоступен. Повторите попытку позже.")
        return

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"Курс {c_from}→{c_to}: {rate} (обновлено: {ts})")
    if rate != 0:
        print(f"Обратный курс {c_to}→{c_from}: {1 / rate:.5f}")

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
            get_rate_cmd(args)

        elif cmd in ("exit", "quit"):
            print("Выход из CLI")
            break

        else:
            print("Неизвестная команда")
