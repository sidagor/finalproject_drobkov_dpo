import time
from abc import ABC, abstractmethod

import requests

from ..core.exceptions import ApiRequestError
from .config import config


class BaseApiClient(ABC):
    """Абстрактный клиент для всех внешних API"""

    @abstractmethod
    def fetch_rates(self) -> dict:
        """
        Должен возвращать словарь формата:
        {"BTC_USD": 59337.21, "ETH_USD": 3700.1}
        """
        pass


class CoinGeckoClient(BaseApiClient):
    """
    Клиент CoinGecko.
    Работает без ключа, использует ids и vs_currencies.
    """

    def fetch_rates(self) -> dict:
        start = time.time()

        ids = ",".join(config.CRYPTO_ID_MAP.values())
        url = (
            f"{config.COINGECKO_URL}?ids={ids}"
            f"&vs_currencies={config.BASE_CURRENCY.lower()}"
        )    

        try:
            response = requests.get(
                url, timeout=config.REQUEST_TIMEOUT,
                headers={"User-Agent": config.USER_AGENT}
            )

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko request failed: {e}")

        if response.status_code != 200:
            raise ApiRequestError(f"CoinGecko returned status {response.status_code}")

        data = response.json()
        fetch_ms = int((time.time() - start) * 1000)

        result = {}

        for symbol, coin_id in config.CRYPTO_ID_MAP.items():
            if coin_id in data:
                rate = data[coin_id].get(config.BASE_CURRENCY.lower())
                if rate is not None:
                    key = f"{symbol}_{config.BASE_CURRENCY}"
                    result[key] = {
                        "rate": rate,
                        "source": "CoinGecko",
                        "meta": {
                            "raw_id": coin_id,
                            "request_ms": fetch_ms,
                            "status_code": response.status_code,
                            "etag": response.headers.get("ETag"),
                        }
                    }

        return result


class ExchangeRateApiClient(BaseApiClient):
    """
    Клиент ExchangeRate-API.
    Использует API-ключ + базовую валюту.
    """

    def fetch_rates(self) -> dict:
        if not config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("Missing EXCHANGERATE_API_KEY environment variable.")

        start = time.time()
        url = (
            f"{config.EXCHANGERATE_API_URL}/{config.EXCHANGERATE_API_KEY}/"
            f"latest/{config.BASE_CURRENCY}"
        )    

        try:
            response = requests.get(
                url,
                timeout=config.REQUEST_TIMEOUT,
                headers={"User-Agent": config.USER_AGENT}
            )
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API request failed: {e}")

        if response.status_code != 200:
            raise ApiRequestError(
                f"ExchangeRate-API returned status {response.status_code}"
            )

        data = response.json()
        fetch_ms = int((time.time() - start) * 1000)

        if data.get("result") != "success":
            raise ApiRequestError(f"ExchangeRate-API returned error: {data}")

        conversion_rates = data.get("conversion_rates")
        if not conversion_rates:
            raise ApiRequestError(
                f"ExchangeRate-API returned no conversion_rates: {data}"
            )

        result = {}

        for fiat in config.FIAT_CURRENCIES:
            if fiat in conversion_rates:
                rate = conversion_rates[fiat]
                key = f"{fiat}_{config.BASE_CURRENCY}"
                result[key] = {
                    "rate": rate,
                    "source": "ExchangeRate-API",
                    "meta": {
                        "request_ms": fetch_ms,
                        "status_code": response.status_code,
                        "raw_id": fiat,
                        "etag": response.headers.get("ETag"),
                    }
                }

        return result
