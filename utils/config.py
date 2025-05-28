"""
Config
======

Moduł do zarządzania konfiguracją generatora paragonów.

Zapewnia funkcje do wczytywania, walidacji i przetwarzania plików konfiguracyjnych.
"""
import os
import yaml
from typing import Dict, Any, Optional

from utils.exceptions import ConfigError
from utils.logger import get_logger


logger = get_logger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Wczytuje plik konfiguracyjny YAML.
    
    Args:
        config_path: Ścieżka do pliku konfiguracyjnego.
        
    Returns:
        Konfiguracja wczytana z pliku YAML.
        
    Raises:
        ConfigError: Gdy wystąpi problem z wczytaniem konfiguracji.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info(f"Wczytano konfigurację z pliku {config_path}")
            return config
    except FileNotFoundError:
        raise ConfigError(f"Nie znaleziono pliku konfiguracyjnego: {config_path}")
    except yaml.YAMLError as e:
        raise ConfigError(f"Nieprawidłowy format pliku YAML: {e}")
    except Exception as e:
        raise ConfigError(f"Błąd podczas wczytywania konfiguracji: {e}")


def get_default_config() -> Dict[str, Any]:
    """
    Zwraca domyślną konfigurację.
    
    Returns:
        Domyślna konfiguracja.
    """
    return {
        "quality": [70, 95],
        "landscape": 0.0,
        "short_size": [480, 720],
        "aspect_ratio": [2, 4],
        "background": {},
        "document": {
            "fullscreen": 1.0,
            "landscape": 0.0,
            "short_size": [250, 480],
            "aspect_ratio": [2, 3],
            "paper": {},
            "content": {
                "margin": 0.05,
                "products_count": [3, 15]
            },
            "effects": {
                "elastic_distortion": True,
                "gaussian_noise": True,
                "perspective": True,
                "perspective_variants": 8
            }
        },
        "effect": {}
    }


def merge_configs(default_config: Dict[str, Any], user_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Łączy domyślną konfigurację z konfiguracją użytkownika.
    
    Args:
        default_config: Domyślna konfiguracja.
        user_config: Konfiguracja użytkownika (opcjonalna).
        
    Returns:
        Połączona konfiguracja.
    """
    if user_config is None:
        return default_config
        
    merged_config = default_config.copy()
    
    for key, value in user_config.items():
        if key in merged_config and isinstance(merged_config[key], dict) and isinstance(value, dict):
            merged_config[key] = merge_configs(merged_config[key], value)
        else:
            merged_config[key] = value
    
    return merged_config