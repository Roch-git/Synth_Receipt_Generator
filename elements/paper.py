"""
Paper
=====

Moduł odpowiedzialny za generowanie warstwy papieru dla paragonu.

Tworzy realistycznie wyglądającą teksturę papieru, która stanowi
tło dla tekstu paragonu.
"""
import random
from typing import Tuple, Dict, Any

from synthtiger import components, layers


class Paper:
    """
    Klasa generująca warstwę papieru dla paragonu.
    
    Tworzy realistycznie wyglądającą teksturę papieru, na której
    będzie umieszczany tekst paragonu.
    
    Attributes:
        image (components.BaseTexture): Komponent tekstury papieru.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Inicjalizuje generator warstwy papieru.
        
        Args:
            config: Konfiguracja generatora papieru.
        """
        self.image = components.BaseTexture(**config.get("image", {}))

    def generate(self, size: Tuple[int, int]) -> layers.Layer:
        """
        Generuje warstwę papieru o podanym rozmiarze.
        
        Args:
            size: Rozmiar papieru (szerokość, wysokość).
            
        Returns:
            Warstwa papieru.
        """
        # Tworzenie jasnego tła dla papieru
        paper_layer = layers.RectLayer(size, (
            random.randint(230, 255),  # R - jasne tło
            random.randint(230, 255),  # G - jasne tło
            random.randint(230, 255),  # B - jasne tło
            255))  # Alpha - pełna nieprzezroczystość
            
        # Aplikowanie tekstury papieru
        self.image.apply([paper_layer])

        return paper_layer