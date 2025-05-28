"""
Generator syntetycznych paragonów - moduł główny
================================================

Skrypt uruchamiający proces generowania syntetycznych paragonów sklepowych.
Pozwala na konfigurację procesu generowania poprzez argumenty wiersza poleceń.

Przykłady użycia:
    # Wygenerowanie 100 paragonów z domyślnymi ustawieniami
    python main.py

    # Wygenerowanie 500 paragonów z własną konfiguracją 
    python main.py --config my_config.yaml --output my_receipts --count 500
    
    # Użycie określonego ziarna losowości dla powtarzalnych wyników
    python main.py --seed 123
"""
import argparse
import os
import sys
import time
import numpy as np

from template_receipt import SynthReceipt
from utils.config import load_config, get_default_config, merge_configs
from utils.exceptions import ConfigError
from utils.logger import get_logger, logging


# Utworzenie loggera dla głównego modułu
logger = get_logger(__name__)


def parse_arguments():
    """Parsuje argumenty wiersza poleceń.
    
    Returns:
        argparse.Namespace: Sparsowane argumenty wiersza poleceń.
    """
    parser = argparse.ArgumentParser(
        description="Generator syntetycznych paragonów",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default="config_receipt.yaml", 
        help="Ścieżka do pliku konfiguracyjnego"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="output", 
        help="Katalog wyjściowy"
    )
    parser.add_argument(
        "--count", 
        type=int, 
        default=100, 
        help="Liczba paragonów do wygenerowania"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42, 
        help="Ziarno losowości"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Włącza szczegółowe logowanie"
    )
    
    return parser.parse_args()


def setup_logging(verbose):
    """Konfiguruje poziom logowania.
    
    Args:
        verbose: Czy włączyć szczegółowe logowanie.
    """
    root_logger = logging.getLogger()
    if verbose:
        root_logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Włączono szczegółowe logowanie")
    else:
        root_logger.setLevel(logging.INFO)


def main():
    """Główna funkcja generująca syntetyczne paragony."""
    # Parsowanie argumentów
    args = parse_arguments()
    
    # Konfiguracja logowania
    setup_logging(args.verbose)
    
    # Ustawienie ziarna losowości dla powtarzalnych wyników
    np.random.seed(args.seed)
    logger.info(f"Ustawiono ziarno losowości: {args.seed}")
    
    try:
        # Wczytanie konfiguracji
        logger.info(f"Wczytywanie konfiguracji z pliku {args.config}...")
        user_config = load_config(args.config)
        default_config = get_default_config()
        config = merge_configs(default_config, user_config)
        
        # Tworzenie katalogu wyjściowego
        os.makedirs(args.output, exist_ok=True)
        logger.info(f"Katalog wyjściowy: {args.output}")

        # Inicjalizacja generatora
        generator = SynthReceipt(config)
        generator.init_save(args.output)

        # Generowanie paragonów
        logger.info(f"Generowanie {args.count} paragonów...")
        start_time = time.time()
        
        for i in range(args.count):
            logger.debug(f"Generowanie paragonu {i+1}/{args.count}...")
            data = generator.generate()
            generator.save(args.output, data, i)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / args.count
        
        # Podsumowanie procesu generowania
        logger.info(f"Wygenerowano {args.count} paragonów w katalogu {args.output}")
        logger.info(f"Całkowity czas: {total_time:.2f} sekund")
        logger.info(f"Średni czas na paragon: {avg_time:.2f} sekund")
        
    except ConfigError as e:
        logger.error(f"Błąd konfiguracji: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Wystąpił nieoczekiwany błąd: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()