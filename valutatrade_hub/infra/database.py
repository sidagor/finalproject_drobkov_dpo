# valutatrade_hub/infra/database.py
import json
from pathlib import Path
from threading import Lock

from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """
    Singleton для управления JSON-файлами (Users, Portfolios, Rates).
    Выполняет ВСЕ операции чтения/записи — utils.py не должен ничего знать о файлах.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.settings = SettingsLoader()

        base = Path(self.settings.get("data_path"))
        self.users_file = base / self.settings.get("users_file")
        self.portfolios_file = base / self.settings.get("portfolios_file")
        self.rates_file = base / self.settings.get("rates_file")

        base.mkdir(parents=True, exist_ok=True)


    def load_users(self):
        return self._load_json(self.users_file, default=[])

    def save_users(self, users):
        self._save_json(self.users_file, users)


    def load_portfolios(self):
        return self._load_json(self.portfolios_file, default=[])

    def save_portfolios(self, portfolios):
        self._save_json(self.portfolios_file, portfolios)


    def load_rates(self):
        return self._load_json(self.rates_file, default={})

    def save_rates(self, rates):
        self._save_json(self.rates_file, rates)

    def get_rate_rates(self, a: str, b: str):
        """
        Возвращает курс валюты a→b для формата:
        """
        a = a.upper()
        b = b.upper()
        rates = self.load_rates()

        pairs = rates.get("pairs", {})
        key = f"{a}_{b}"

        entry = pairs.get(key)
        if not entry:
            return None

        return entry.get("rate")

    def _load_json(self, path: Path, default):
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def _save_json(self, path: Path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

