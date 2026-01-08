# valutatrade_hub/core/utils.py
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader

from .models import Wallet

SETTINGS = SettingsLoader()

DB = DatabaseManager()

SESSION = {"current_user": None}


def parse_args(arg_list, allowed):
    """
    Разбирает список аргументов командной строки 
    """
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
    """
    Получает словарь данных пользователя по username через DatabaseManager.
    Возвращает None, если пользователь не найден.
    """
    users = DB.load_users()
    for u in users:
        if u["username"] == username:
            return u
    return None


def get_portfolio_by_user_id(user_id):
    """
    Получает портфель пользователя по user_id через DatabaseManager.
    Возвращает словарь {user_id, wallets}, где wallets: {код: Wallet}.
    """
    portfolios = DB.load_portfolios()
    for p in portfolios:
        if p["user_id"] == user_id:
            wallets = {
                code: Wallet(code, w["balance"])
                for code, w in p.get("wallets", {}).items()
            }
            return {"user_id": user_id, "wallets": wallets}
    return None


def get_rate_rates(a: str, b: str):
    """
    Получает курс валют через DatabaseManager.
    """
    return DB.get_rate_rates(a, b)



