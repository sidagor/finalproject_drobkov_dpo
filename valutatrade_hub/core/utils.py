import json
from .models import Wallet

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

def get_rate_rates(a, b):
    """Получает обменный курс"""
    rates = load_rates()
    if a in rates and b in rates[a]:
        return rates[a][b]
    return None

