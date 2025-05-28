"""
SynthReceipt
============

Generator syntetycznych paragonów sklepowych, który tworzy realistyczne obrazy paragonów
wraz z odpowiadającymi im metadanymi strukturalnymi.

Moduł zawiera główną klasę SynthReceipt odpowiedzialną za generowanie, zapisywanie
i zarządzanie wygenerowanymi danymi paragonów.
"""
import json
import os
import re
from typing import Any, Dict, List, Tuple, Union

import numpy as np
from elements.background import Background
from elements.document import Document
from elements.receipt_content import ReceiptContent
from PIL import Image
from synthtiger import components, layers, templates


class SynthReceipt(templates.Template):
    """Generator syntetycznych paragonów sklepowych.
    
    Klasa generuje realistyczne paragony sklepowe jako obrazy wraz z odpowiadającymi
    im danymi strukturalnymi. Wykorzystuje komponenty tła, dokumentu i efektów
    wizualnych do stworzenia różnorodnych, realistycznie wyglądających paragonów.
    
    Attributes:
        quality (List[int]): Zakres jakości kompresji JPEG [min, max].
        landscape (float): Prawdopodobieństwo orientacji poziomej (dla paragonów zwykle 0).
        short_size (List[int]): Zakres rozmiaru krótszego boku paragonu [min, max].
        aspect_ratio (List[float]): Zakres współczynnika proporcji [min, max].
        background (Background): Komponent generujący tło paragonu.
        document (Document): Komponent generujący warstwę dokumentu.
        effect (components.Iterator): Komponent aplikujący efekty wizualne.
        splits (List[str]): Nazwy podziałów danych (train/validation/test).
        split_ratio (List[float]): Proporcje podziału danych.
        split_indexes (np.ndarray): Przypisanie indeksów do podziałów.
    """

    def __init__(self, config=None, split_ratio: List[float] = [0.7, 0.15, 0.15]):
        """Inicjalizuje generator paragonów.
        
        Args:
            config (Dict, optional): Konfiguracja generatora. Defaults to None.
            split_ratio (List[float]): Proporcje podziału danych na zbiory 
                train/validation/test. Defaults to [0.7, 0.15, 0.15].
        """
        super().__init__(config)
        if config is None:
            config = {}

        # Konfiguracja ogólnych parametrów generatora
        self.quality = config.get("quality", [70, 95])
        self.landscape = config.get("landscape", 0.0)  # Paragony zawsze pionowe
        self.short_size = config.get("short_size", [480, 720])
        self.aspect_ratio = config.get("aspect_ratio", [2, 4])
        
        # Inicjalizacja komponentów generujących poszczególne elementy paragonu
        self.background = Background(config.get("background", {}))
        self.document = Document(config.get("document", {}))
        
        # Inicjalizacja komponentów efektów wizualnych
        self.effect = components.Iterator(
            [
                components.Switch(components.RGB()),
                components.Switch(components.Shadow()),
                components.Switch(components.Contrast()),
                components.Switch(components.Brightness()),
                components.Switch(components.MotionBlur()),
                components.Switch(components.GaussianBlur()),
            ],
            **config.get("effect", {})
        )

        # Konfiguracja podziału danych na zbiory treningowe/walidacyjne/testowe
        self.splits = ["train", "validation", "test"]
        self.split_ratio = split_ratio
        self.split_indexes = np.random.choice(3, size=10000, p=split_ratio)

    def generate(self):
        """Generuje syntetyczny paragon wraz z metadanymi.
        
        Proces generacji obejmuje:
        1. Ustalenie rozmiaru paragonu
        2. Generowanie tła
        3. Generowanie warstwy dokumentu i tekstu
        4. Łączenie wszystkich warstw
        5. Aplikowanie efektów wizualnych
        
        Returns:
            Dict[str, Any]: Słownik zawierający wygenerowane dane:
                - image (np.ndarray): Obraz paragonu w formacie RGB
                - label (str): Pełny tekst paragonu
                - quality (int): Jakość obrazu (w skali JPEG)
                - roi (np.ndarray): Region zainteresowania (koordynaty)
                - structured_data (Dict): Strukturalne dane paragonu
        """
        # Ustalenie rozmiaru paragonu (zawsze pionowy, wąski)
        landscape = np.random.rand() < self.landscape  # Prawie zawsze False dla paragonów
        short_size = np.random.randint(self.short_size[0], self.short_size[1] + 1)
        aspect_ratio = np.random.uniform(self.aspect_ratio[0], self.aspect_ratio[1])
        long_size = int(short_size * aspect_ratio)
        size = (long_size, short_size) if landscape else (short_size, long_size)

        # Generowanie tła
        bg_layer = self.background.generate(size)
        
        # Generowanie warstwy dokumentu i tekstu
        paper_layer, text_layers, texts, structured_data = self.document.generate(size)

        # Łączenie wszystkich warstw
        document_group = layers.Group([*text_layers, paper_layer])
        document_space = np.clip(size - document_group.size, 0, None)
        
        # Wymuszenie pozycjonowania na środku lub po lewej stronie
        document_group.left = 0  # Wyrównaj do lewej krawędzi
        document_group.top = 0   # Wyrównaj do górnej krawędzi
        roi = np.array(paper_layer.quad, dtype=int)

        # Łączenie i aplikowanie efektów
        layer = layers.Group([*document_group.layers, bg_layer]).merge()
        self.effect.apply([layer])

        # Przygotowanie wyniku
        image = layer.output(bbox=[0, 0, *size])
        label = " ".join(texts)
        label = label.strip()
        label = re.sub(r"\s+", " ", label)
        quality = np.random.randint(self.quality[0], self.quality[1] + 1)

        # Zwrócenie wynikowych danych
        data = {
            "image": image,
            "label": label,
            "quality": quality,
            "roi": roi,
            "structured_data": structured_data
        }

        return data

    def init_save(self, root):
        """Inicjalizuje katalogi zapisu wygenerowanych danych.
        
        Args:
            root (str): Ścieżka głównego katalogu zapisu.
        """
        if not os.path.exists(root):
            os.makedirs(root, exist_ok=True)

    def save(self, root, data, idx):
        """Zapisuje wygenerowany paragon i jego metadane.
        
        Zapisuje obraz paragonu w formacie JPEG oraz odpowiadające mu
        metadane w formacie JSONL. Pliki są organizowane w podkatalogach
        odpowiadających podziałowi na zbiory (train/validation/test).
        
        Args:
            root (str): Katalog główny do zapisu danych.
            data (Dict[str, Any]): Dane wygenerowanego paragonu.
            idx (int): Indeks wygenerowanego paragonu.
        """
        image = data["image"]
        label = data["label"]
        quality = data["quality"]
        roi = data["roi"]
        structured_data = data.get("structured_data", {})  # Bezpieczne pobieranie

        # Określenie podziału danych (train/validation/test)
        split_idx = self.split_indexes[idx % len(self.split_indexes)]
        output_dirpath = os.path.join(root, self.splits[split_idx])

        # Zapis obrazu w formacie JPEG
        image_filename = f"receipt_{idx}.jpg"
        image_filepath = os.path.join(output_dirpath, image_filename)
        os.makedirs(os.path.dirname(image_filepath), exist_ok=True)
        
        # Konwersja z RGBA na RGB przed zapisem
        image = Image.fromarray(image[..., :3].astype(np.uint8))  # Użyj tylko pierwszych 3 kanałów (RGB)
        image.save(image_filepath, quality=quality)

        # Przygotowanie uproszczonych metadanych z zaokrąglonymi cenami
        donut_metadata = {
            "shop": {
                "name": structured_data.get("shop", {}).get("name", "")
            },
            "products": [
                {
                    "name": p.get("name", ""),
                    "quantity": p.get("quantity", 0),
                    "unit": p.get("unit", ""),
                    "unit_price": round(float(p.get("unit_price", 0)), 2),
                    "total_price": round(float(p.get("total_price", 0)), 2)
                } for p in structured_data.get("products", [])
            ],
            "total": round(float(structured_data.get("total", 0.0)), 2)
        }

        # Zapisz metadane w formacie JSONL
        metadata_filename = f"metadata_{self.splits[split_idx]}.jsonl"
        metadata_filepath = os.path.join(root, metadata_filename)
        os.makedirs(os.path.dirname(metadata_filepath), exist_ok=True)

        metadata = {
            "file_name": os.path.join(self.splits[split_idx], image_filename),
            "ground_truth": json.dumps(donut_metadata, ensure_ascii=False)
        }
        
        with open(metadata_filepath, "a", encoding="utf-8") as fp:
            json.dump(metadata, fp, ensure_ascii=False)
            fp.write("\n")
            
    def end_save(self, root):
        """Finalizuje proces zapisywania danych.
        
        Ta metoda może być rozszerzona w przyszłości, np. do generowania
        podsumowań lub statystyk na temat wygenerowanych danych.
        
        Args:
            root (str): Katalog główny zapisu danych.
        """
        pass

    def format_metadata(self, image_filename: str, keys: List[str], values: List[Any]):
        """Formatuje metadane do zapisu w formacie JSONL.
        
        Args:
            image_filename (str): Nazwa pliku obrazu.
            keys (List[str]): Klucze metadanych.
            values (List[Any]): Wartości metadanych.
            
        Returns:
            Dict[str, Any]: Sformatowane metadane.
            
        Raises:
            AssertionError: Gdy liczba kluczy i wartości jest różna.
        """
        assert len(keys) == len(values), "Length does not match: keys({}), values({})".format(len(keys), len(values))

        _gt_parse_v = dict()
        for k, v in zip(keys, values):
            _gt_parse_v[k] = v
        gt_parse = {"gt_parse": _gt_parse_v}
        gt_parse_str = json.dumps(gt_parse, ensure_ascii=False)
        metadata = {"file_name": image_filename, "ground_truth": gt_parse_str}
        return metadata