
class InsufficientFundsError(Exception):
    """Недостаточно средств на кошельке"""
    def __init__(self, code: str, available: float, required: float):
        self.code = code
        self.available = available
        self.required = required
        super().__init__(
            f"Недостаточно средств: доступно {available:.4f} {code},"
            f"требуется {required:.4f} {code}"
        )    


class CurrencyNotFoundError(Exception):
    """Неизвестная валюта"""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(Exception):
    """Ошибка при обращении к внешнему API"""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")

class StorageError(Exception):
    """Ошибка работы с файловым хранилищем"""
    pass