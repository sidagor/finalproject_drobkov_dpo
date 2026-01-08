import logging
import time
from threading import Event

from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .config import config
from .storage import RatesStorage
from .updater import RatesUpdater

logger = logging.getLogger(__name__)


class Scheduler:
    """
    Периодический планировщик, который запускает обновление курсов
    каждые N секунд. Работает до тех пор, пока не получит сигнал stop().
    """

    def __init__(self, interval: int = None):
        self.interval = interval or config.UPDATE_INTERVAL_SECONDS
        self.stop_event = Event()
        
        self.storage = RatesStorage(config.RATES_FILE_PATH)
        self.clients = [
            CoinGeckoClient(),
            ExchangeRateApiClient()
        ]
        self.updater = RatesUpdater(self.clients, self.storage)

    def start(self):
        logger.info(f"Scheduler started. Update interval = {self.interval} seconds.")

        try:
            while not self.stop_event.is_set():
                start_time = time.time()

                logger.info("Running scheduled update...")
                try:
                    self.updater.run_update()
                except Exception as e:
                    logger.exception(f"Unexpected error during update: {e}")

                elapsed = time.time() - start_time
                sleep_time = max(0, self.interval - elapsed)

                logger.debug(f"Sleeping {sleep_time:.2f} seconds until next update...")
                self.stop_event.wait(timeout=sleep_time)

        except KeyboardInterrupt:
            logger.warning("Scheduler interrupted by user (Ctrl+C).")

        finally:
            logger.info("Scheduler stopped.")

    def stop(self):
        """Останавливает планировщик извне."""
        logger.info("Stop signal received. Stopping scheduler...")
        self.stop_event.set()


def run_scheduler():
    """Точка входа для CLI."""
    scheduler = Scheduler()
    scheduler.start()


if __name__ == "__main__":    
    logging.basicConfig(level=logging.INFO)
    run_scheduler()
