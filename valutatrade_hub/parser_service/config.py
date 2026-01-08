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
    
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY")


    
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"
    
    BASE_CURRENCY: str = "USD"
    
    FIAT_CURRENCIES: Tuple[str, ...] = ("EUR", "GBP", "RUB")
    
    CRYPTO_CURRENCIES: Tuple[str, ...] = ("BTC", "ETH", "SOL")
    
    CRYPTO_ID_MAP: dict = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana"
    })
    
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"
    
    REQUEST_TIMEOUT: int = 10

    UPDATE_INTERVAL_SECONDS: int = 300
    
    USER_AGENT: str = "ValutaTradeHub/ParserService"


config = ParserConfig()
