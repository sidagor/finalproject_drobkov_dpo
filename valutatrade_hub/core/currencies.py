# valutatrade_hub/core/currencies.py
from abc import ABC, abstractmethod

from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс для представления валюты."""

    def __init__(self, name: str, code: str):
        code = code.upper()
        if not code.isalpha() or not (2 <= len(code) <= 5):
            raise ValueError(f"Неверный код валюты: {code}")
        if not name.strip():
            raise ValueError("Название валюты не может быть пустым")
        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает строковое представление валюты для отображения."""
        pass

class FiatCurrency(Currency):
    """Класс для представления фиатной валюты."""    
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        """Возвращает строковое представление валюты для отображения."""
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"

class CryptoCurrency(Currency):
    """Класс для представления криптовалюты."""
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        """Возвращает строковое представление валюты для отображения."""
        return (
            f"[CRYPTO] {self.code} — {self.name}" 
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )    

_currency_registry = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
}

def get_currency(code: str) -> Currency:
    """функция для получения экземпляра валюты."""
    code = code.upper()
    if code not in _currency_registry:
        raise CurrencyNotFoundError(f"Валюта с кодом '{code}' не найдена")
    return _currency_registry[code]
