"""
Background
==========

Moduł odpowiedzialny za generowanie tła dla paragonu.

Zapewnia jednolite tło dla całego dokumentu, na którym będzie
umieszczana warstwa paragonu.
"""
from typing import Tuple, Dict, Any, Optional

from synthtiger import components, layers


class Background:
    """
    Klasa generująca tło dla paragonu.
    
    Generuje jednolite tło, które może być opcjonalnie zmodyfikowane
    przez różne efekty wizualne, takie jak rozmycie gaussowskie.
    
    Attributes:
        image (components.BaseTexture): Komponent tekstury tła.
        effect (components.Iterator): Komponent efektów wizualnych.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Inicjalizuje generator tła.
        
        Args:
            config: Konfiguracja generatora tła.
        """
        self.image = components.BaseTexture(**config.get("image", {}))
        self.effect = components.Iterator(
            [
                components.Switch(components.GaussianBlur()),
            ],
            **config.get("effect", {})
        )

    def generate(self, size: Tuple[int, int]) -> layers.Layer:
        """
        Generuje warstwę tła o podanym rozmiarze.
        
        Args:
            size: Rozmiar tła (szerokość, wysokość).
            
        Returns:
            Warstwa tła.
        """
        bg_layer = layers.RectLayer(size, (255, 255, 255, 255))
        self.image.apply([bg_layer])
        self.effect.apply([bg_layer])

        return bg_layer