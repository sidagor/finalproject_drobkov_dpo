import hashlib
from datetime import datetime

from valutatrade_hub.logging_config import parser_logger as logger
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater

from ..decorators import log_action
from .currencies import get_currency
from .exceptions import ApiRequestError, CurrencyNotFoundError, InsufficientFundsError
from .models import Portfolio, User, Wallet
from .utils import DB, SESSION, parse_args


def register(username: str, password: str):
    """Регистрация нового пользователя"""
    users = DB.load_users()

    if any(u["username"] == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    user_id = max([u["user_id"] for u in users], default=0) + 1
    salt = User.generate_salt()
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()

    new_user = {
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed,
        "salt": salt,
        "registration_date": datetime.utcnow().isoformat(),
    }

    users.append(new_user)
    DB.save_users(users)

    portfolios = DB.load_portfolios()
    portfolios.append({"user_id": user_id, "wallets": {}})
    DB.save_portfolios(portfolios)

    print(f"Пользователь '{username}' зарегистрирован (id={user_id}).")


def login(args):
    """Авторизация пользователя"""
    parts = parse_args(args, ["--username", "--password"])
    username = parts.get("--username")
    password = parts.get("--password")

    if not username or not password:
        print("Укажите --username и --password")
        return

    users = DB.load_users()
    user_data = next((u for u in users if u["username"] == username), None)
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

    portfolios = DB.load_portfolios()
    portfolio_data = next((p for p in portfolios if p["user_id"] == user.user_id), None)
    if portfolio_data:
        wallets = {
            code: Wallet(code, w["balance"])
            for code, w in portfolio_data.get("wallets", {}).items()
        }
    else:
        wallets = {}

    user.portfolio = Portfolio(user_id=user.user_id, wallets=wallets)
    SESSION["current_user"] = user
    print(f"Вы вошли как '{username}'")


def show_portfolio(args):
    """Показывает портфель пользователя"""
    user = SESSION.get("current_user")
    if not user:
        raise ValueError("Сначала выполните login")

    parts = parse_args(args, ["--base"])
    base = parts.get("--base", DB.settings.get("default_base_currency")).upper()
    get_currency(base)

    portfolio = user.portfolio
    if not portfolio.wallets:
        print("У вас пока нет кошельков")
        return

    print(f"Портфель пользователя '{user.username}' (база: {base}):")
    total = 0.0
    for code, wallet in portfolio.wallets.items():
        bal = wallet.balance
        if code == base:
            conv = bal
        else:
            rate = DB.get_rate_rates(code, base)
            if rate is None:
                raise ApiRequestError(f"Нет курса {code}→{base}")
            conv = bal * rate
        total += conv
        print(f"- {code}: {bal:.4f} → {conv:.2f} {base}")

    print("---------------------------------")
    print(f"ИТОГО: {total:,.2f} {base}")

@log_action("BUY", verbose=True)
def buy(args):
    user = SESSION.get("current_user")
    if not user:
        raise ValueError("Сначала выполните login")

    params = parse_args(args, {"--currency", "--amount"})
    currency = params.get("--currency")
    amount_str = params.get("--amount")

    if currency is None or amount_str is None:
        raise ValueError("Укажите --currency и --amount")

    try:
        amount = float(amount_str)
    except Exception:
        raise ValueError("'amount' должен быть числом")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    currency = currency.upper()
    get_currency(currency)  
    
    portfolios = DB.load_portfolios()
    portfolio_data = next((p for p in portfolios if p["user_id"] == user.user_id), None)
    if not portfolio_data:
        raise ValueError("Портфель пользователя не найден")

    wallets = portfolio_data.get("wallets", {})
    if currency not in wallets:
        wallets[currency] = {"balance": 0.0}

    before_balance = wallets[currency]["balance"]
    wallets[currency]["balance"] += amount
    after_balance = wallets[currency]["balance"]

    portfolio_data["wallets"] = wallets
    DB.save_portfolios(portfolios)
    
    rate = DB.get_rate_rates(currency, DB.settings.get("default_base_currency"))
    if rate is None:
        raise ApiRequestError(f"Не удалось получить курс для {currency}→USD")
    cost = amount * rate
    
    print(
        f"Покупка выполнена: {amount:.4f} {currency} " 
        f"по курсу {rate:.2f} USD/{currency}"
    )
    print(f"- {currency}: было {before_balance:.4f} → стало {after_balance:.4f}")
    print(f"Оценочная стоимость покупки: {cost:,.2f} USD")

    return {
        "user": user,
        "currency": currency,
        "amount": amount,
        "rate": rate,
        "base": "USD",
        "wallet_before": {currency: before_balance},
        "wallet_after": {currency: after_balance}
    }


@log_action("SELL", verbose=True)
def sell(args):
    user = SESSION.get("current_user")
    if not user:
        raise ValueError("Сначала выполните login")

    params = parse_args(args, {"--currency", "--amount"})
    currency = params.get("--currency")
    amount_str = params.get("--amount")

    if currency is None or amount_str is None:
        raise ValueError("Укажите --currency и --amount")

    try:
        amount = float(amount_str)
    except Exception:
        raise ValueError("'amount' должен быть числом")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    currency = currency.upper()
    get_currency(currency)
    
    portfolios = DB.load_portfolios()
    portfolio_data = next((p for p in portfolios if p["user_id"] == user.user_id), None)
    if not portfolio_data:
        raise ValueError("Портфель пользователя не найден")

    wallets = portfolio_data.get("wallets", {})
    if currency not in wallets or wallets[currency]["balance"] < amount:
        available = wallets.get(currency, {"balance": 0.0})["balance"]
        raise InsufficientFundsError(
            available=available,
            required=amount,
            code=currency
        )

    before_balance = wallets[currency]["balance"]
    wallets[currency]["balance"] += amount
    after_balance = wallets[currency]["balance"]


    rate = DB.get_rate_rates(currency, DB.settings.get("default_base_currency"))
    if rate is None:
        raise ApiRequestError(f"Не удалось получить курс для {currency}→USD")

    if "USD" not in wallets:
        wallets["USD"] = 0.0
    wallets["USD"]["balance"] += amount * rate

    portfolio_data["wallets"] = wallets
    DB.save_portfolios(portfolios)
    
    revenue = amount * rate
    
    print(f"Продажа: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}")
    print(f"- {currency}: было {before_balance:.4f} → стало {after_balance:.4f}")
    print(f"Оценочная выручка: {revenue:,.2f} USD")

    return {
        "user": user,
        "currency": currency,
        "amount": amount,
        "rate": rate,
        "base": "USD",
        "wallet_before": {currency: before_balance},
        "wallet_after": {currency: after_balance}
    }

def get_rate(from_code: str, to_code: str):
    from_code = from_code.upper()
    to_code = to_code.upper()

    try:
        get_currency(from_code)
        get_currency(to_code)
    except Exception:
        raise CurrencyNotFoundError(f"Одна из валют не найдена: {from_code}, {to_code}")

    data = DB.load_rates()
    pairs = data.get("pairs", {})

    direct_key = f"{from_code}_{to_code}"
    inverse_key = f"{to_code}_{from_code}"

    if direct_key in pairs:
        pair = pairs[direct_key]
        rate_value = pair["rate"]
        updated_at_str = pair.get("updated_at")
    elif inverse_key in pairs:
        pair = pairs[inverse_key]
        rate_value = 1 / pair["rate"] if pair["rate"] != 0 else 0
        updated_at_str = pair.get("updated_at")
    else:
        raise ApiRequestError(f"Курс {from_code}→{to_code} недоступен")

    ttl_seconds = DB.settings.get("rates_ttl_seconds", 300)
    now = datetime.utcnow()
    if updated_at_str:
        try:
            updated_at_dt = datetime.fromisoformat(updated_at_str.replace("Z", ""))
        except Exception:
            updated_at_dt = datetime.min
    else:
        updated_at_dt = datetime.min

    if (now - updated_at_dt).total_seconds() > ttl_seconds:
        print("Внимание: курс устарел (TTL)")

    print(f"Курс {from_code}→{to_code}: {rate_value:.8f} (обновлено: {updated_at_str})")
    if rate_value != 0:
        print(f"Обратный курс {to_code}→{from_code}: {1 / rate_value:.5f}")

    return {"rate": rate_value, "updated_at": updated_at_str}

def update_rates(source: str = None):
    storage = RatesStorage()
    clients = []

    if source:
        src = source.lower()
        if src == "coingecko":
            clients.append(CoinGeckoClient())
        elif src == "exchangerate":
            clients.append(ExchangeRateApiClient())
        else:
            print(f"Неизвестный источник '{source}'")
            return
    else:
        clients = [CoinGeckoClient(), ExchangeRateApiClient()]

    updater = RatesUpdater(clients, storage)

    try:
        updated_rates, last_refresh = updater.run_update()
        if updated_rates:
            print(
                f"Update successful. Total rates updated: {len(updated_rates)}. "
                f"Last refresh: {last_refresh}"
            )

    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        logger.error(f"Unknown error during rates update: {e}")


def show_rates(currency: str = None, top: int = None, base: str = "USD"):
    storage = RatesStorage()
    try:
        cache = storage.load_current_rates()
    except FileNotFoundError:
        print(
            "Локальный кеш курсов пуст. Выполните 'update-rates', "
            "чтобы загрузить данные."
        )

        return

    pairs = cache.get("pairs", {})
    results = []

    base_currency = base.upper()
    for pair, data in pairs.items():
        from_curr, to_curr = pair.split("_")
        if currency and currency.upper() != from_curr:
            continue
        if base_currency != to_curr:
            continue
        results.append((from_curr, to_curr, data["rate"], data["updated_at"]))

    if top:
        results = sorted(results, key=lambda x: x[2], reverse=True)[:top]
    else:
        results = sorted(results, key=lambda x: x[0])

    if not results:
        if currency:
            print(f"Курс для '{currency}' не найден.")
        else:
            print("Нет доступных курсов.")
            
        return

    print(f"Rates from cache (updated at {cache.get('last_refresh')}):")
    for from_curr, to_curr, rate, updated_at in results:
        print(f"- {from_curr}_{to_curr}: {rate:.6f} (updated: {updated_at})")

    logger.info(f"Displayed {len(results)} rates", extra={"action": "show-rates"})

def print_help():
    """Выводит справку по доступным командам CLI"""
    print("""
    Доступные команды:
          
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
    """)   

