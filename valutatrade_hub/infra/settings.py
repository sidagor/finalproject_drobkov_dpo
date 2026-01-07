# valutatrade_hub/infra/settings.py
import json
from pathlib import Path
from typing import Any


class SingletonMeta(type):
    """
    Метакласс для Singleton.
    Гарантирует, что создается только один экземпляр класса,
    независимо от количества импортов или вызовов конструктора.
    Выбран метакласс вместо __new__ для более явного контроля и читаемости.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class SettingsLoader(metaclass=SingletonMeta):
    """
    Singleton для конфигурации проекта.
    Загружает и кеширует данные из config.json.
    """

    DEFAULT_CONFIG = {
        "data_path": "data",
        "users_file": "users.json",
        "portfolios_file": "portfolios.json",
        "rates_file": "rates.json",
        "rates_ttl_seconds": 300,
        "default_base_currency": "USD",
        "log_path": "logs/valutatrade.log",
        "log_level": "INFO",
        "log_format": "[%(asctime)s] %(levelname)s - %(message)s"
    }

    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path("config.json")
        self._config = {}
        self.reload()

    def get(self, key: str, default: Any = None) -> Any:
        """Возвращает значение по ключу, если не найдено — default"""
        return self._config.get(key, default)

    def reload(self):
        """Перезагрузка конфигурации"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self._config = {**self.DEFAULT_CONFIG, **cfg}
            except Exception:
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()
