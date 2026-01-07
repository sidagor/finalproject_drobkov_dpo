import logging
from logging.handlers import RotatingFileHandler


def setup_parsing_logger():
    """Логгер для parser_service: простые информационные логи в консоль"""
    logger = logging.getLogger("parser_service")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
        ))
        logger.addHandler(console_handler)
    return logger

def setup_actions_logger():
    """Структурированный логгер для действий пользователя"""
    logger = logging.getLogger("actions")
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        "logs/actions.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )

    formatter = logging.Formatter(
        "%(levelname)s %(asctime)s %(action)s user='%(username)s' "
        "currency='%(currency)s' amount=%(amount)s rate=%(rate)s "
        "base='%(base)s' result=%(result)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

parser_logger = setup_parsing_logger()
actions_logger = setup_actions_logger()


