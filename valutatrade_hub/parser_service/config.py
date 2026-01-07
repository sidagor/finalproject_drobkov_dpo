import os
from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class ParserConfig:
    """
    Конфигурация Parser Service:
    - API ключи (из env)
    - URL внешних сервисов
    - списки валют
    - пути к файлам
    - сетевые параметры
    """

    # Ключ загружается из переменной окружения
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY")



    # URL-ы для запросов
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Базовая валюта
    BASE_CURRENCY: str = "USD"

    # Фиатные валюты
    FIAT_CURRENCIES: Tuple[str, ...] = ("EUR", "GBP", "RUB")

    # Криптовалюты
    CRYPTO_CURRENCIES: Tuple[str, ...] = ("BTC", "ETH", "SOL")

    # Словарь соответствий: тикер → id CoinGecko
    CRYPTO_ID_MAP: dict = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana"
    })

    # Пути к файлам
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    # Таймауты
    REQUEST_TIMEOUT: int = 10

    UPDATE_INTERVAL_SECONDS: int = 300

    # Ограничения
    USER_AGENT: str = "ValutaTradeHub/ParserService"


config = ParserConfig()
