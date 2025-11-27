import hashlib
from datetime import datetime


class User:
    def __init__(self, user_id: int, username: str, hashed_password: str, salt: str, registration_date: datetime):
        self._user_id = user_id
        self.username = username           
        self._hashed_password = hashed_password
        self.salt = salt                   
        self.registration_date = registration_date   

    @property
    def user_id(self):
        return self._user_id

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    @property
    def hashed_password(self):
        return self._hashed_password

    @property
    def salt(self):
        return self._salt

    @salt.setter
    def salt(self, value: str):
        if not value:
            raise ValueError("Соль не должна быть пустой")
        self._salt = value

    @property
    def registration_date(self):
        return self._registration_date

    @registration_date.setter
    def registration_date(self, value: datetime):
        if not isinstance(value, datetime):
            raise TypeError("registration_date должен быть datetime")
        self._registration_date = value
     
    def get_user_info(self) -> dict:
        """Возвращает информацию о пользователе без пароля."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str):
        """Меняет пароль, хешируя new_password + salt."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        combined = (new_password + self._salt).encode()
        hashed = hashlib.sha256(combined).hexdigest()
        self._hashed_password = hashed

    def verify_password(self, password: str) -> bool:
        """Проверяет правильность введённого пароля."""
        combined = (password + self._salt).encode()
        hashed = hashlib.sha256(combined).hexdigest()
        return hashed == self._hashed_password

class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code
        self.balance = balance


    @property
    def balance(self):
        return self._balance


    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)


    def deposit(self, amount: float):
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self._balance += float(amount)


    def withdraw(self, amount: float):
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self._balance:
            raise ValueError("Недостаточно средств на балансе")
        self._balance -= float(amount)


    def get_balance_info(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }


class Portfolio:
    def __init__(self, user_id: int, wallets: dict[str, Wallet] | None = None):
        self._user_id = user_id
        self._wallets = wallets or {}


    @property
    def user_id(self):
        return self._user_id


    @property
    def wallets(self):
        return dict(self._wallets)


    def get_wallet(self, currency_code: str) -> Wallet | None:
        return self._wallets.get(currency_code)


    def add_currency(self, currency_code: str):
        if currency_code in self._wallets:
            raise ValueError("Кошелёк для этой валюты уже существует")
        self._wallets[currency_code] = Wallet(currency_code)


    def get_total_value(self, base_currency: str = "USD") -> float:
        exchange_rates = {
            "USD": 1.0,
            "EUR": 1.1,
            "BTC": 50000.0,
        }
        if base_currency not in exchange_rates:
            raise ValueError("Нет курса для базовой валюты")
        total = 0.0
        for code, wallet in self._wallets.items():
            if code not in exchange_rates:
                continue
            total += wallet.balance * exchange_rates[code]
        return total / exchange_rates[base_currency]