"""
Narzędzia do przetwarzania tekstu
=================================

Funkcje pomocnicze związane z przetwarzaniem i formatowaniem
tekstu na paragonie.
"""
import random
from typing import List, Dict, Any, Tuple, Optional, Union


def format_number(number: float, decimal_separator: str = ".", decimal_places: int = 2) -> str:
    """Formatuje liczbę używając podanego separatora dziesiętnego.
    
    Args:
        number: Liczba do sformatowania
        decimal_separator: Separator dziesiętny (domyślnie ".")
        decimal_places: Liczba miejsc po przecinku
        
    Returns:
        Sformatowana liczba jako tekst
    """
    format_str = f"{{:.{decimal_places}f}}"
    return format_str.format(number).replace('.', decimal_separator)


def split_long_text(text: str, max_length: int) -> List[str]:
    """Dzieli długi tekst na fragmenty o określonej maksymalnej długości.
    
    Args:
        text: Tekst do podzielenia
        max_length: Maksymalna długość fragmentu
        
    Returns:
        Lista fragmentów tekstu
    """
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]


def weighted_choice(options: List[Dict[str, Any]], key_name: str, weight_key: str = "weight") -> Any:
    """Wybiera element z listy opcji na podstawie wag.
    
    Args:
        options: Lista opcji (słowników)
        key_name: Nazwa klucza z wartością do zwrócenia
        weight_key: Nazwa klucza zawierającego wagę
        
    Returns:
        Wybrana wartość
        
    Examples:
        >>> options = [{"format": "standard", "weight": 5}, {"format": "compact", "weight": 2}]
        >>> weighted_choice(options, "format")
        'standard'  # z prawdopodobieństwem 5/7
    """
    if not options:
        return None
        
    total_weight = sum(item.get(weight_key, 1) for item in options)
    r = random.uniform(0, total_weight)
    current_weight = 0
    
    for item in options:
        current_weight += item.get(weight_key, 1)
        if r <= current_weight:
            return item[key_name]
    
    # Domyślnie zwraca pierwszy element
    return options[0][key_name]


def format_price(
    quantity: float, 
    unit_price: float, 
    total_price: float,
    vat_symbol: str,
    unit: str = "", 
    multiply_sign: str = "x",
    decimal_separator: str = ".",
    price_format: str = "standard"
) -> str:
    """Formatuje cenę produktu zgodnie z podanym formatem.
    
    Args:
        quantity: Ilość produktu
        unit_price: Cena jednostkowa
        total_price: Cena całkowita
        vat_symbol: Symbol stawki VAT
        unit: Jednostka miary (opcjonalnie)
        multiply_sign: Znak mnożenia
        decimal_separator: Separator dziesiętny
        price_format: Format ceny ("standard", "no_spaces" lub "hybrid")
        
    Returns:
        Sformatowana cena jako tekst
    """
    # Formatowanie liczb z odpowiednim separatorem dziesiętnym
    quantity_str = format_number(
        quantity, 
        decimal_separator, 
        3 if unit in ["kg", "l"] else 0
    )
    unit_price_str = format_number(unit_price, decimal_separator)
    total_price_str = format_number(total_price, decimal_separator)
    
    # Wybór formatu ceny
    if price_format == "standard":
        if unit:  # Jeśli jednostka nie jest pusta
            return f"{quantity_str} {unit} {multiply_sign} {unit_price_str} = {total_price_str} {vat_symbol}"
        else:
            return f"{quantity_str} {multiply_sign} {unit_price_str} = {total_price_str} {vat_symbol}"
    
    elif price_format == "no_spaces":
        if unit:  # Jeśli jednostka nie jest pusta
            return f"{quantity_str}{unit}{multiply_sign}{unit_price_str}={total_price_str}{vat_symbol}"
        else:
            return f"{quantity_str}{multiply_sign}{unit_price_str}={total_price_str}{vat_symbol}"
    
    elif price_format == "hybrid":
        if unit:  # Jeśli jednostka nie jest pusta
            return f"{quantity_str} {unit} {multiply_sign} {unit_price_str} = {total_price_str}{vat_symbol}"
        else:
            return f"{quantity_str} {multiply_sign} {unit_price_str} = {total_price_str}{vat_symbol}"
    
    # Domyślny przypadek
    return f"{quantity_str} {multiply_sign} {unit_price_str} = {total_price_str} {vat_symbol}"