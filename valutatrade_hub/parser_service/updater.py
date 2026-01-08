# parser_service/updater.py
import datetime
import logging

from ..core.exceptions import ApiRequestError
from .storage import RatesStorage

logger = logging.getLogger("parser_service")


class RatesUpdater:
    """
    Главный координатор обновления курсов.
    """

    def __init__(self, api_clients: list, storage: RatesStorage):
        self.api_clients = api_clients
        self.storage = storage

    def run_update(self) -> tuple[dict, str]:
        """
        Возвращает:
            combined_rates: словарь всех курсов
            last_refresh: время последнего обновления в формате YYYY-MM-DDTHH:MM:SS
        """
        logger.info("Starting rates update...")
        combined_rates = {}
        history_records = []

        for client in self.api_clients:
            client_name = client.__class__.__name__
            client_short = (
                "CoinGecko" 
                if "CoinGecko" in client_name 
                else "ExchangeRate-API"
            )    

            try:
                data = client.fetch_rates()
                logger.info(f"Fetching from {client_short}... OK ({len(data)} rates)")
                
                for pair_key, payload in data.items():
                    combined_rates[pair_key] = payload
                    from_cur, to_cur = pair_key.split("_")
                    record_id = f"{pair_key}_{datetime.datetime.utcnow().isoformat()}Z"
                    history_records.append({
                        "id": record_id,
                        "from_currency": from_cur,
                        "to_currency": to_cur,
                        "rate": payload["rate"],
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                        "source": payload["source"],
                        "meta": payload["meta"],
                    })

            except ApiRequestError as e:
                logger.error(f"{client_short} failed: {e}")
                continue

        if not combined_rates:
            logger.error("No rates fetched. Update aborted.")
            return {}, ""
        
        logger.info(f"Writing {len(combined_rates)} rates to {self.storage.rates_path}")
        self.storage.save_current_rates(combined_rates)
        self.storage.append_history_records(history_records)

        last_refresh = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        
        return combined_rates, last_refresh
