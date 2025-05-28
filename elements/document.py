"""
Document
========

Moduł odpowiedzialny za generowanie warstwy dokumentu paragonu.

Klasa Document zarządza tworzeniem tła dokumentu, nakładaniem tekstu
oraz aplikowaniem efektów wizualnych, które tworzą realistyczny wygląd paragonu.
"""
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union

from synthtiger import components, layers

from elements.receipt_content import ReceiptContent
from elements.paper import Paper


class Document:
    """
    Klasa odpowiedzialna za generowanie warstwy dokumentu paragonu.
    
    Zarządza tworzeniem tła dokumentu, nakładaniem tekstu oraz aplikowaniem
    efektów wizualnych, które tworzą realistyczny wygląd paragonu.
    
    Attributes:
        fullscreen (float): Prawdopodobieństwo, że dokument zajmie cały obszar.
        landscape (float): Prawdopodobieństwo orientacji poziomej.
        short_size (List[int]): Zakres rozmiaru krótszego boku [min, max].
        aspect_ratio (List[float]): Zakres współczynnika proporcji [min, max].
        paper (Paper): Komponent generujący tło dokumentu.
        content (ReceiptContent): Komponent generujący zawartość paragonu.
        effect (components.Iterator): Komponent aplikujący efekty wizualne.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Inicjalizacja generatora dokumentu.
        
        Args:
            config: Konfiguracja dokumentu
        """
        # Pobieranie podstawowych parametrów z konfiguracji
        self.fullscreen = config.get("fullscreen", 1.0)
        self.landscape = config.get("landscape", 0.0)
        self.short_size = config.get("short_size", [250, 480])
        self.aspect_ratio = config.get("aspect_ratio", [3, 5])
        
        # Inicjalizacja obiektu do generowania tła dokumentu
        self.paper = Paper(config.get("paper", {}))
        
        # Inicjalizacja generatora zawartości paragonu
        self.content = ReceiptContent(config.get("content", {}))
        
        # Inicjalizacja efektów na podstawie konfiguracji
        self._initialize_effects(config)
    
    def _initialize_effects(self, config: Dict[str, Any]) -> None:
        """
        Inicjalizuje listę efektów na podstawie konfiguracji.
        
        Args:
            config: Konfiguracja z możliwymi ustawieniami efektów
        """
        # Pobieranie konfiguracji efektów
        effects_config = config.get("effects", {})
        effect_list = []
        
        # Dodawanie efektu zniekształcenia elastycznego
        if effects_config.get("elastic_distortion", True):
            effect_list.append(components.Switch(components.ElasticDistortion()))
        
        # Dodawanie efektu szumu gaussowskiego
        if effects_config.get("gaussian_noise", True):
            effect_list.append(components.Switch(components.AdditiveGaussianNoise()))
        
        # Dodawanie efektu perspektywy
        if effects_config.get("perspective", True):
            # Tworzenie listy wariantów perspektywy
            perspective_variants = []
            variant_count = effects_config.get("perspective_variants", 8)
            
            for _ in range(variant_count):
                perspective_variants.append(components.Perspective())
            
            effect_list.append(components.Switch(components.Selector(perspective_variants)))
        
        # Inicjalizacja iteratora efektów z kompletną listą
        self.effect = components.Iterator(
            effect_list,
            **config.get("effect", {})
        )
    
    def generate(
        self, 
        size: Tuple[int, int]
    ) -> Tuple[layers.Layer, List[layers.Layer], List[str], Dict[str, Any]]:
        """
        Generuje dokument paragonu o podanym rozmiarze.
        
        Args:
            size: Docelowy rozmiar dokumentu (szerokość, wysokość)
            
        Returns:
            Krotka (warstwa papieru, warstwy tekstowe, teksty, dane strukturalne)
        """
        # Określenie rozmiaru dokumentu
        document_size = self._calculate_document_size(size)
        
        # Generowanie warstw tekstowych i treści
        text_layers, texts, structured_data = self.content.generate(document_size)
        
        # Generowanie warstwy papieru (tła dokumentu)
        paper_layer = self.paper.generate(document_size)
        
        # Zastosowanie efektów do wszystkich warstw
        self._apply_effects(text_layers, paper_layer)
        
        return paper_layer, text_layers, texts, structured_data
    
    def _calculate_document_size(self, size: Tuple[int, int]) -> Tuple[int, int]:
        """
        Oblicza rozmiar dokumentu na podstawie parametrów konfiguracji.
        
        Args:
            size: Docelowy rozmiar dokumentu (szerokość, wysokość)
            
        Returns:
            Obliczony rozmiar dokumentu (szerokość, wysokość)
        """
        width, height = size
        
        # Jeśli dokument ma zajmować cały obszar, zwracamy oryginalny rozmiar
        if np.random.rand() < self.fullscreen:
            return size
        
        # Losowe określenie orientacji (dla paragonów zwykle pionowa)
        landscape = np.random.rand() < self.landscape
        
        # Maksymalny wymiar krótszego boku
        max_size = width if landscape else height
        
        # Losowanie wartości krótszego boku
        short_size = np.random.randint(
            min(width, height, self.short_size[0]),
            min(width, height, self.short_size[1]) + 1
        )
        
        # Losowanie współczynnika proporcji
        aspect_ratio = np.random.uniform(
            min(max_size / short_size, self.aspect_ratio[0]),
            min(max_size / short_size, self.aspect_ratio[1])
        )
        
        # Obliczenie dłuższego boku
        long_size = int(short_size * aspect_ratio)
        
        # Ustalenie finalnych wymiarów w zależności od orientacji
        return (long_size, short_size) if landscape else (short_size, long_size)
    
    def _apply_effects(self, text_layers: List[layers.Layer], paper_layer: layers.Layer) -> None:
        """
        Stosuje efekty wizualne do wszystkich warstw dokumentu.
        
        Args:
            text_layers: Lista warstw tekstowych
            paper_layer: Warstwa tła dokumentu
        """
        self.effect.apply([*text_layers, paper_layer])