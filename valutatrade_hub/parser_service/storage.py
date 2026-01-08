import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from ..core.exceptions import StorageError
from .config import config


class FileLock:
    """Простой файловый lock для атомарных операций"""
    def __init__(self, path: Path):
        self.lockfile = path.with_suffix(path.suffix + ".lock")
        self.acquired = False

    def acquire(self, timeout: float = 5.0) -> None:
        import time
        start = time.time()
        while True:
            try:
                fd = os.open(str(self.lockfile), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w") as f:
                    f.write(f"{os.getpid()}\n")
                self.acquired = True
                return
            except FileExistsError:
                if (time.time() - start) >= timeout:
                    raise StorageError(f"Timeout acquiring lock {self.lockfile}")
                time.sleep(0.1)

    def release(self) -> None:
        if self.acquired and self.lockfile.exists():
            try:
                self.lockfile.unlink()
            finally:
                self.acquired = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class RatesStorage:
    """Хранение курсов: rates.json и exchange_rates.json"""

    def __init__(self,
                 rates_path: Optional[str] = None,
                 history_path: Optional[str] = None):
        self.rates_path = Path(rates_path or config.RATES_FILE_PATH)
        self.history_path = Path(history_path or config.HISTORY_FILE_PATH)
        
        self.rates_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        self._rates_lock = FileLock(self.rates_path)
        self._history_lock = FileLock(self.history_path)

    @staticmethod
    def _atomic_write(path: Path, data: str) -> None:
        with tempfile.NamedTemporaryFile(
            "w", dir=path.parent, delete=False,
            encoding="utf-8"
        ) as tmp:
            tmp.write(data)
            tempname = Path(tmp.name)
        os.replace(str(tempname), str(path))

    @staticmethod
    def _to_iso_z(dt: Optional[datetime] = None) -> str:
        d = dt or datetime.now(timezone.utc)
        return (
            d.astimezone(timezone.utc).replace(microsecond=0)
            .isoformat().replace("+00:00", "Z")
        )    
    
    def save_current_rates(self, combined_rates: Dict[str, Dict]) -> None:
        now = self._to_iso_z()
        pairs = {}
        for pair_key, payload in combined_rates.items():
            rate = payload.get("rate")
            source = payload.get("source", "unknown")
            updated_at = payload.get("meta", {}).get("timestamp") or now
            pairs[pair_key] = {
                "rate": rate,
                "updated_at": updated_at,
                "source": source
            }

        out_obj = {"pairs": pairs, "last_refresh": now}
        text = json.dumps(out_obj, ensure_ascii=False, indent=4)

        with self._rates_lock:
            self._atomic_write(self.rates_path, text)

    def load_current_rates(self) -> Dict:
        if not self.rates_path.exists():
            return {}
        try:
            with self.rates_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
   
    def append_history_records(self, records: List[Dict]) -> None:
        history = []
        if self.history_path.exists():
            try:
                with self.history_path.open("r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        
        existing_ids = {r["id"] for r in history if "id" in r}
        
        new_records = [r for r in records if r.get("id") not in existing_ids]

        if not new_records:
            return

        history.extend(new_records)
        text = json.dumps(history, ensure_ascii=False, indent=4)

        with self._history_lock:
            self._atomic_write(self.history_path, text)
