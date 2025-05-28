"""
Logger
======

Moduł do logowania komunikatów w generatorze paragonów.

Zapewnia spójne i konfigurowalne logowanie w całym projekcie.
"""
import logging
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Tworzy i konfiguruje logger.
    
    Args:
        name: Nazwa loggera, zwykle nazwa modułu.
        level: Poziom logowania (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Jeśli nie podano, używany jest domyślny poziom INFO.
            
    Returns:
        Skonfigurowany logger.
    """
    if level is None:
        level = logging.INFO
        
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Jeśli logger nie ma jeszcze handlerów, dodaj handler do konsoli
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# Globalny logger dla modułu utils
logger = get_logger(__name__)