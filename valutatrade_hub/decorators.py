import functools

from valutatrade_hub.logging_config import actions_logger as logger


def log_action(action_type, verbose=False):
    """
    Декоратор для логирования операций.
    action_type: 'BUY', 'SELL', 'REGISTER', 'LOGIN'
    verbose: добавляет изменения кошелька в лог (в одну запись)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            default_extra = {
                "action": action_type,
                "username": "unknown",
                "currency": None,
                "amount": None,
                "rate": None,
                "base": "USD",
                "result": None
            }

            try:
                result = func(*args, **kwargs)
                
                user = result.get("user")
                username = getattr(user, "username", "unknown") if user else "unknown"
                currency = result.get("currency")
                amount = result.get("amount")
                rate = result.get("rate")
                base = result.get("base", "USD")
                
                verbose_msg = ""
                if verbose:
                    wallet_before = result.get("wallet_before")
                    wallet_after = result.get("wallet_after")
                    if wallet_before and wallet_after:
                        verbose_msg = " | Wallet: %s -> %s" % (
                            wallet_before,
                            wallet_after
                        )
                
                log_extra = {
                    **default_extra,
                    "username": username,
                    "currency": currency,
                    "amount": f"{amount:.4f}" if amount is not None else None,
                    "rate": f"{rate:.2f}" if rate is not None else None,
                    "base": base,
                    "result": "OK"
                }
                
                logger.info(verbose_msg, extra=log_extra)

                return result

            except Exception as e:
                error_extra = {
                    **default_extra,
                    "username": getattr(kwargs.get("user"), "username", "unknown"),
                    "result": "ERROR",
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
                logger.error("", extra=error_extra)
                raise

        return wrapper
    return decorator




