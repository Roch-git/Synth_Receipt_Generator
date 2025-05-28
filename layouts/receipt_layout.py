"""
Receipt Layout
=============

Specjalizowany układ dla paragonów sklepowych.

Moduł implementuje logikę tworzenia układu paragonu, określania pozycji
i wymiarów poszczególnych elementów, oraz generowania danych zawartości paragonu.
"""
import json
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional, Union

import numpy as np
from utils.exceptions import LayoutError


class ReceiptLayout:
    """
    Klasa implementująca układ paragonu sklepowego.
    
    Generuje kompletny układ paragonu wraz z nagłówkiem, listą produktów i stopką.
    Odpowiada za rozmieszczenie poszczególnych elementów na paragonie oraz generowanie
    danych zawartości zgodnie z konfiguracją.
    
    Attributes:
        text_scale (List[float]): Zakres skali tekstu.
        align (List[str]): Dostępne typy wyrównania tekstu.
        stack_spacing (List[float]): Zakres odstępów między wierszami.
        margin (float): Margines dokumentu.
        header_scale (List[float]): Zakres skali dla nagłówka PARAGON FISKALNY.
        heights (Dict[str, int]): Wysokości poszczególnych sekcji.
        spacing (Dict[str, int]): Dodatkowe odstępy między sekcjami.
        separator_config (Dict): Konfiguracja separatorów.
        date_range (Dict[str, int]): Konfiguracja zakresu dat.
        corpus (Dict): Dane korpusu tekstowego.
        products_count (List[int]): Zakres liczby produktów [min, max].
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicjalizuje układ paragonu.
        
        Args:
            config: Konfiguracja układu paragonu.
        """
        if config is None:
            config = {}
        
        # Konfiguracja układu
        self.text_scale = config.get("text_scale", [0.03, 0.06])
        self.align = config.get("align", ["left", "center"])
        self.stack_spacing = config.get("stack_spacing", [0.02, 0.03])
        self.margin = config.get("margin", 0.05)
        # Parametr dla skali nagłówka PARAGON FISKALNY
        self.header_scale = config.get("header_scale", [0.7, 0.9])

        # Wczytanie konfiguracji wysokości elementów
        self._initialize_heights(config)
        
        # Wczytanie konfiguracji separatorów
        self._initialize_separators(config)

        # Konfiguracja zakresu dat
        self.date_range = config.get("date_range", {
            "min_days_back": 0,
            "max_days_back": 730,
            "min_hour": 8,
            "max_hour": 21
        })
        
        # Korpus będzie ustawiony przez metodę load_corpus
        self.corpus = None
        
        # Zakres liczby produktów - będzie pobrany z głównej konfiguracji
        self.products_count = [3, 15]  # Domyślne wartości zmieniane później
        
        # Inicjalizacja atrybutów, które będą ustawione później
        self.current_formatting = {}
        self.chosen_separator = None
        self.separator_length_factor = 0.35
        self.document_content_width = 0
        self.max_chars_per_line = 0
        self.half_width_chars = 0
    
    def _initialize_heights(self, config: Dict[str, Any]) -> None:
        """
        Inicjalizuje wysokości sekcji paragonu.
        
        Args:
            config: Konfiguracja układu paragonu.
        """
        heights_config = config.get("heights", {})
        
        # Wysokości poszczególnych sekcji z wartościami domyślnymi
        self.heights = {
            "shop_name": heights_config.get("shop_name", 25),
            "shop_address": heights_config.get("shop_address", 20),
            "shop_tax_id": heights_config.get("shop_tax_id", 20),
            "date_number": heights_config.get("date_number", 20),
            "receipt_header": heights_config.get("receipt_header", 30),
            "separator": heights_config.get("separator", 15),
            "product": heights_config.get("product", 25),
            "vat_line": heights_config.get("vat_line", 20),
            "total_sum": heights_config.get("total_sum", 30),
            "payment_method": heights_config.get("payment_method", 20),
            "footer": heights_config.get("footer", 20)
        }
        
        # Dodatkowe odstępy między sekcjami
        spacing_config = heights_config.get("spacing", {})
        self.spacing = {
            "after_shop_name": spacing_config.get("after_shop_name", 5),
            "after_date_number": spacing_config.get("after_date_number", 5),
            "after_receipt_header": spacing_config.get("after_receipt_header", 5),
            "after_separator": spacing_config.get("after_separator", 5),
            "before_products": spacing_config.get("before_products", 10),
            "after_products": spacing_config.get("after_products", 5),
            "before_payment": spacing_config.get("before_payment", 10),
            "after_payment": spacing_config.get("after_payment", 10)
        }
    
    def _initialize_separators(self, config: Dict[str, Any]) -> None:
        """
        Inicjalizuje konfigurację separatorów.
        
        Args:
            config: Konfiguracja układu paragonu.
        """
        self.separator_config = config.get("separators", {})
        if not self.separator_config:
            self.separator_config = {
                "types": [
                    {"symbol": "-", "name": "dash", "weight": 6, "length": 0.4},
                    {"symbol": ".", "name": "dot", "weight": 2, "length": 0.5},
                    {"symbol": "*", "name": "star", "weight": 2, "length": 0.21}
                ],
                "locations": {
                    "header": 0.9,
                    "title": 0.95,
                    "products": 0.8,
                    "vat": 0.6,
                    "payment": 0.7,
                    "footer": 0.85
                },
                "length": [0.34, 0.36]  # Min i max długość
            }
    
    def load_corpus(self, corpus_path: str) -> None:
        """
        Wczytuje korpus z pliku JSON.
        
        Args:
            corpus_path: Ścieżka do pliku korpusu
            
        Raises:
            FileNotFoundError: Gdy nie znaleziono pliku korpusu
            ValueError: Gdy plik korpusu zawiera nieprawidłowy format JSON
        """
        self.corpus_path = corpus_path
        try:
            with open(corpus_path, 'r', encoding='utf-8') as f:
                self.corpus = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Nie znaleziono pliku korpusu: {corpus_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Plik korpusu {corpus_path} zawiera nieprawidłowy format JSON")
    
    def _should_display_separator(self, location: str) -> bool:
        """
        Sprawdza, czy separator ma być widoczny w danej lokalizacji.
        
        Args:
            location: Nazwa lokalizacji separatora
            
        Returns:
            True jeśli separator ma być widoczny, False w przeciwnym przypadku
        """
        location_prob = self.separator_config.get("locations", {}).get(location, 0.8)
        return random.random() <= location_prob
    
    def set_products_count(self, count_range: List[int]) -> None:
        """
        Ustawia zakres liczby produktów.
        
        Args:
            count_range: Lista [min_count, max_count]
        """
        self.products_count = count_range

    def generate(self, bbox: List[int]) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, str], float, Dict[str, Dict[str, Any]], str, str, str, str]:
        """
        Generuje układ paragonu w ramach określonego prostokąta.
        
        Args:
            bbox: Prostokąt określający położenie i rozmiar paragonu [x, y, width, height].
            
        Returns:
            Krotka zawierająca:
                - layouts (Dict): Słownik layoutów poszczególnych sekcji
                - products (List[Dict]): Lista produktów
                - payment_method (Dict): Metoda płatności
                - total_price (float): Suma paragonu
                - vat_summary (Dict): Podsumowanie VAT
                - separator (str): Separator
                - date (str): Data paragonu
                - number (str): Numer paragonu
                - header (str): Nagłówek paragonu
                
        Raises:
            LayoutError: Gdy korpus nie został wczytany
        """
        if self.corpus is None:
            raise LayoutError("Korpus nie został wczytany. Użyj metody load_corpus().")
        
        # Parametry prostokąta
        x, y, width, height = bbox
        
        # Jednolity margines dla całej kartki (5% szerokości)
        margin_x = int(width * self.margin)
        content_width = width - 2 * margin_x
        
        # Zapisujemy parametry szerokości dla późniejszego formatowania tekstu
        self._calculate_text_width_parameters(content_width)
        
        # Inicjalizacja słownika dla layoutów
        layouts = {}
        
        # Generowanie danych paragonu
        shop_data = self._generate_shop_data()
        receipt_data = self._generate_receipt_data()
        products = self._generate_products()
        separator = "-" * int(content_width)  # Separator dopasowany do szerokości
        
        # Inicjalizacja pozycji y dla kolejnych elementów
        current_y = y + 10  # Dodajemy trochę przestrzeni na górze
        
        # Generowanie layoutu paragonu używając podejścia modularnego
        current_y, header_layouts = self._generate_header_layout(current_y, x, width, margin_x, content_width)
        layouts.update(header_layouts)
        
        current_y, date_layouts = self._generate_date_number_layout(current_y, x, margin_x, content_width)
        layouts.update(date_layouts)
        
        current_y, receipt_header_layouts = self._generate_receipt_header_layout(current_y, x, margin_x, content_width)
        layouts.update(receipt_header_layouts)
        
        current_y, products_layouts = self._generate_products_layout(current_y, x, margin_x, content_width, products)
        layouts.update(products_layouts)
        
        # Obliczenie podsumowania VAT
        vat_summary = self._calculate_vat_summary(products)
        
        # Suma paragonu
        total_price = sum(product["total_price"] for product in products)
        
        # Wybór losowej metody płatności
        payment_method = random.choice(self.corpus["payment_methods"])
        
        current_y, vat_layouts = self._generate_vat_summary_layout(current_y, x, margin_x, content_width, vat_summary)
        layouts.update(vat_layouts)
        
        current_y, payment_layouts = self._generate_payment_layout(current_y, x, margin_x, content_width)
        layouts.update(payment_layouts)
        
        current_y, footer_layouts = self._generate_footer_layout(current_y, x, margin_x, content_width)
        layouts.update(footer_layouts)

        # Zapisujemy wygenerowane dane jako atrybuty klasy (dla kompatybilności wstecznej)
        self.shop_data = shop_data
        self.receipt_data = receipt_data
        self.products = products
        self.total_price = total_price
        self.payment_method = payment_method
        
        return (layouts, products, payment_method, total_price, vat_summary, 
                separator, receipt_data["date"], receipt_data["number"], receipt_data["header"])
    
    def _calculate_text_width_parameters(self, content_width: int) -> None:
        """
        Oblicza parametry szerokości tekstu na podstawie szerokości zawartości.
        
        Args:
            content_width: Szerokość zawartości
        """
        # Przybliżona liczba pikseli na znak
        chars_per_px = 8.7
        
        # Zapisujemy parametry jako atrybuty dla późniejszego wykorzystania
        self.document_content_width = content_width
        self.max_chars_per_line = int(content_width / chars_per_px)
        self.half_width_chars = self.max_chars_per_line // 2

    def _generate_shop_data(self) -> Dict[str, str]:
        """
        Generuje dane sklepu.
        
        Returns:
            Słownik z danymi sklepu
        """
        shop = random.choice(self.corpus["shop_names"])
        return {
            "name": shop["name"],
            "address": random.choice(self.corpus["company_info"]["addresses"]),
            "tax_id": random.choice(self.corpus["company_info"]["tax_ids"])
        }
        
    def _generate_receipt_data(self) -> Dict[str, str]:
        """
        Generuje dane paragonu z losową datą.
        
        Returns:
            Słownik z danymi paragonu
        """
        # Losowa data z zakresu ostatnich dwóch lat
        days_back = random.randint(
            self.date_range.get("min_days_back", 0),
            self.date_range.get("max_days_back", 730)
        )
        random_date = datetime.now() - timedelta(days=days_back)
        
        # Losowa godzina
        random_hour = random.randint(
            self.date_range.get("min_hour", 8),
            self.date_range.get("max_hour", 21)
        )
        random_minute = random.randint(0, 59)
        
        # Formatowanie daty według wybranego formatu
        date_format = self.current_formatting.get('date_format', 'dash')
        if date_format == "dash":
            formatted_date = random_date.strftime("%d-%m-%Y")
        elif date_format == "dot":
            formatted_date = random_date.strftime("%d.%m.%Y")
        elif date_format == "slash":
            formatted_date = random_date.strftime("%d/%m/%Y")
        else:
            formatted_date = random_date.strftime("%d-%m-%Y")  # Domyślny format
        
        formatted_time = f"{random_hour:02d}:{random_minute:02d}"
        
        # Generowanie numeru paragonu
        receipt_number = f"{random.randint(1000, 9999)}/{random.randint(1, 12)}/{random.randint(2022, 2025)}"
        
        # Formatowanie numeru paragonu według wybranego formatu
        number_format = self.current_formatting.get('receipt_number_format', 'Nr paragonu: {number}')
        formatted_number = number_format.format(number=receipt_number)
        
        return {
            "header": random.choice(self.corpus["receipt_headers"]),
            "date": f"Data: {formatted_date} {formatted_time}",
            "number": formatted_number
        }
    
    def _generate_products(self) -> List[Dict[str, Any]]:
        """
        Generuje listę produktów na paragonie.
        
        Returns:
            Lista produktów
        """
        num_products = random.randint(self.products_count[0], self.products_count[1])
        products = []
        
        # Generowanie losowych produktów
        for _ in range(num_products):
            product = self._generate_single_product()
            products.append(product)
        
        return products
    
    def _generate_single_product(self) -> Dict[str, Any]:
        """
        Generuje pojedynczy produkt na paragonie.
        
        Returns:
            Słownik z danymi produktu
        """
        # Wybór losowego produktu
        product = random.choice(self.corpus["products"]["grocery"])
        
        # Pobranie jednostki miary
        unit = product["unit"]
        
        # Generowanie ilości produktu
        quantity = self._generate_product_quantity(unit)
        
        # Losowa cena jednostkowa z zakresu
        unit_price = round(random.uniform(product["price_range"][0], product["price_range"][1]), 2)
        
        # Obliczenie ceny całkowitej
        total_product_price = round(quantity * unit_price, 2)
        
        # Formatowanie produktu
        product_info = {
            "name": product['name'],
            "quantity": quantity,
            "unit": unit,
            "unit_price": unit_price,
            "total_price": total_product_price,
            "vat_symbol": product["vat_symbol"],
            "vat_rate": product["vat_rate"]
        }
        
        return product_info
    
    def _generate_product_quantity(self, unit: str) -> float:
        """
        Generuje ilość produktu na podstawie jednostki miary.
        
        Args:
            unit: Jednostka miary produktu
            
        Returns:
            Ilość produktu
        """
        # Sprawdzamy, czy mamy konfigurację zakresów dla tej jednostki
        if unit in self.corpus["quantity_ranges"]:
            quantity_config = self.corpus["quantity_ranges"][unit]
            ranges = quantity_config["ranges"]
            
            # Wybór zakresu na podstawie wag
            weights = [range_config["weight"] for range_config in ranges]
            selected_range = random.choices(ranges, weights=weights, k=1)[0]
            
            # Losowanie wartości z wybranego zakresu
            min_val = selected_range["min"]
            max_val = selected_range["max"]
            
            if unit == "kg":
                quantity = round(random.uniform(min_val, max_val), 2)
            else:  # "szt." i inne jednostki całkowitoliczbowe
                quantity = random.randint(min_val, max_val)
        else:
            # Domyślne zachowanie gdy brak konfiguracji
            if unit == "kg":
                quantity = round(random.uniform(0.1, 12.0), 2)
            else:
                quantity = random.randint(1, 20)
        
        return quantity
    
    def _calculate_vat_summary(self, products: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Oblicza podsumowanie VAT dla produktów.
        
        Args:
            products: Lista produktów
            
        Returns:
            Słownik z podsumowaniem VAT według symboli
        """
        vat_summary = {}
        
        for product in products:
            symbol = product["vat_symbol"]
            vat_rate_str = product["vat_rate"]
            
            # Konwersja stawki VAT na liczbę
            vat_rate = float(re.sub(r'[^0-9.]', '', vat_rate_str)) / 100
            
            # Obliczenie wartości netto i kwoty podatku
            net_price = round(product["total_price"] / (1 + vat_rate), 2)
            tax_amount = round(product["total_price"] - net_price, 2)
            
            # Aktualizacja podsumowania VAT
            if symbol not in vat_summary:
                vat_summary[symbol] = {"rate": vat_rate_str, "net": 0.0, "tax": 0.0}
            
            vat_summary[symbol]["net"] += net_price
            vat_summary[symbol]["tax"] += tax_amount
        
        return vat_summary
    
    def _generate_header_layout(
        self, 
        current_y: int, 
        x: int, 
        width: int, 
        margin_x: int, 
        content_width: int
    ) -> Tuple[int, Dict[str, List[Tuple[List[int], str]]]]:
        """
        Generuje layout dla nagłówka paragonu.
        
        Args:
            current_y: Aktualna pozycja y
            x: Pozycja x początku paragonu
            width: Szerokość paragonu
            margin_x: Margines
            content_width: Szerokość treści
            
        Returns:
            Krotka (zaktualizowana pozycja y, słownik layoutów sekcji)
        """
        layouts = {}
        
        # NAZWA SKLEPU - wyśrodkowana
        shop_name_height = self.heights.get("shop_name", 25)
        shop_name_bbox = [x + margin_x, current_y, content_width, shop_name_height]
        layouts["shop_name"] = [(shop_name_bbox, "center")]
        current_y += shop_name_height + self.spacing.get("after_shop_name", 5)
        
        # ADRES SKLEPU - wyśrodkowany
        address_height = self.heights.get("shop_address", 20)
        address_bbox = [x + margin_x, current_y, content_width, address_height]
        layouts["shop_address"] = [(address_bbox, "center")]
        current_y += address_height
        
        # NIP - wyśrodkowany
        nip_height = self.heights.get("shop_tax_id", 20)
        nip_bbox = [x + margin_x, current_y, content_width, nip_height]
        layouts["shop_tax_id"] = [(nip_bbox, "center")]
        current_y += nip_height
        
        # Separator - dodaj tylko jeśli ma być widoczny
        if self._should_display_separator("header"):
            separator_height = self.heights.get("separator", 15)
            separator_width = content_width
            separator_bbox = [x + margin_x, current_y, separator_width, separator_height]
            layouts["header_separator"] = [(separator_bbox, "center")]
            current_y += separator_height + self.spacing.get("after_separator", 5)
        
        return current_y, layouts

    def _generate_date_number_layout(
        self, 
        current_y: int, 
        x: int, 
        margin_x: int, 
        content_width: int
    ) -> Tuple[int, Dict[str, List[Tuple[List[int], str]]]]:
        """
        Generuje layout dla daty i numeru paragonu.
        
        Args:
            current_y: Aktualna pozycja y
            x: Pozycja x początku paragonu
            margin_x: Margines
            content_width: Szerokość treści
            
        Returns:
            Krotka (zaktualizowana pozycja y, słownik layoutów sekcji)
        """
        layouts = {}
        
        # Data i nr paragonu na tej samej linii - data po lewej, nr po prawej
        date_line_height = self.heights.get("date_number", 20)
        date_width = int(content_width * 0.5)  # Lewa połowa dla daty
        number_width = int(content_width * 0.5)  # Prawa połowa dla numeru
        
        date_bbox = [x + margin_x, current_y, date_width, date_line_height]
        number_bbox = [x + margin_x + date_width, current_y, number_width, date_line_height]
        
        layouts["date_number"] = [
            (date_bbox, "left"),
            (number_bbox, "right")
        ]
        
        current_y += date_line_height + self.spacing.get("after_date_number", 5)
        
        return current_y, layouts

    def _generate_receipt_header_layout(
        self, 
        current_y: int, 
        x: int, 
        margin_x: int, 
        content_width: int
    ) -> Tuple[int, Dict[str, List[Tuple[List[int], str]]]]:
        """
        Generuje layout dla nagłówka PARAGON FISKALNY.
        
        Args:
            current_y: Aktualna pozycja y
            x: Pozycja x początku paragonu
            margin_x: Margines
            content_width: Szerokość treści
            
        Returns:
            Krotka (zaktualizowana pozycja y, słownik layoutów sekcji)
        """
        layouts = {}
        
        # PARAGON FISKALNY - wyraźnie wyśrodkowany, większy i pogrubiony
        header_height = self.heights.get("receipt_header", 30)
        receipt_header_bbox = [x + margin_x, current_y, content_width, header_height]
        layouts["receipt_header"] = [(receipt_header_bbox, "center")]
        current_y += header_height + self.spacing.get("after_receipt_header", 5)
        
        # Separator po nagłówku
        if self._should_display_separator("title"):
            separator_height = self.heights.get("separator", 15)
            separator_bbox = [x + margin_x, current_y, content_width, separator_height]
            layouts["title_separator"] = [(separator_bbox, "center")]
            current_y += separator_height + self.spacing.get("before_products", 10)
        
        return current_y, layouts
    
    def _generate_products_layout(
        self, 
        current_y: int, 
        x: int, 
        margin_x: int, 
        content_width: int, 
        products: List[Dict[str, Any]]
    ) -> Tuple[int, Dict[str, List[Tuple[List[int], str]]]]:
        """
        Generuje layout dla listy produktów z obsługą długich nazw.
        
        Args:
            current_y: Aktualna pozycja y
            x: Pozycja x początku paragonu
            margin_x: Margines
            content_width: Szerokość treści
            products: Lista produktów
            
        Returns:
            Krotka (zaktualizowana pozycja y, słownik layoutów sekcji)
        """
        layouts = {}
        product_layouts = []
        
        # Wysokość linii produktu
        product_height = self.heights.get("product", 25)
        
        # Generowanie layoutu dla każdego produktu
        for product in products:
            product_name = product["name"]
            
            # Obsługa produktu w zależności od długości nazwy
            if len(product_name) > self.max_chars_per_line:
                # Długa nazwa - wymaga podziału na wiele linii
                current_y = self._generate_long_product_layout(
                    product_name, product_height, x, margin_x, content_width, 
                    current_y, product_layouts
                )
            elif len(product_name) > self.half_width_chars:
                # Średnio długa nazwa - nazwa na pełną szerokość, cena w nowej linii
                current_y = self._generate_medium_product_layout(
                    product_height, x, margin_x, content_width, 
                    current_y, product_layouts
                )
            else:
                # Krótka nazwa - nazwa i cena w jednej linii
                current_y = self._generate_short_product_layout(
                    product_height, x, margin_x, content_width, 
                    current_y, product_layouts
                )
        
        layouts["products"] = product_layouts
        
        # Separator po produktach
        if self._should_display_separator("products"):
            separator_height = self.heights.get("separator", 15)
            separator_bbox = [x + margin_x, current_y, content_width, separator_height]
            layouts["products_separator"] = [(separator_bbox, "center")]
            current_y += separator_height + self.spacing.get("after_separator", 5)
        
        return current_y, layouts
    
    def _generate_long_product_layout(
        self, 
        product_name: str, 
        product_height: int, 
        x: int, 
        margin_x: int, 
        content_width: int, 
        current_y: int, 
        product_layouts: List[List[Tuple[List[int], str]]]
    ) -> int:
        """
        Generuje layout dla produktu z długą nazwą.
        
        Args:
            product_name: Nazwa produktu
            product_height: Wysokość linii produktu
            x: Pozycja x początku paragonu
            margin_x: Margines
            content_width: Szerokość treści
            current_y: Aktualna pozycja y
            product_layouts: Lista layoutów produktów do aktualizacji
            
        Returns:
            Zaktualizowana pozycja y
        """
        # Funkcja pomocnicza do dzielenia długiego tekstu na fragmenty
        def split_long_text(text, max_length):
            return [text[i:i+max_length] for i in range(0, len(text), max_length)]
        
        # Podział nazwy na fragmenty
        name_parts = split_long_text(product_name, self.max_chars_per_line)
        
        # Generowanie warstw dla każdej linii nazwy oprócz ostatniej
        for part in name_parts[:-1]:
            name_bbox = [x + margin_x, current_y, content_width, product_height]
            product_layouts.append([
                (name_bbox, "left")  # Pełna szerokość
            ])
            current_y += product_height
        
        # Ostatnia część nazwy
        last_part = name_parts[-1]
        
        # Decyzja o umieszczeniu ceny
        if len(last_part) > self.half_width_chars:
            # Ostatnia część nazwy na pełną szerokość
            name_bbox = [x + margin_x, current_y, content_width, product_height]
            product_layouts.append([
                (name_bbox, "left")
            ])
            current_y += product_height
            
            # Cena w nowej linii
            price_bbox = [x + margin_x, current_y, content_width, product_height]
            product_layouts.append([
                (price_bbox, "right")  # Wyrównanie do prawej
            ])
            current_y += product_height
        else:
            # Nazwa i cena w jednej linii z nakładaniem
            # NAKŁADANIE: Definiujemy procent nakładania i szerokości
            name_width = int(content_width * 0.5)        # 50% szerokości dla nazwy
            price_width = int(content_width * 0.65)      # 65% szerokości dla ceny
            overlap = int(content_width * 0.15)          # 15% nakładania
            
            name_bbox = [x + margin_x, current_y, name_width, product_height]
            price_bbox = [x + margin_x + name_width - overlap, current_y, price_width, product_height]
            
            product_layouts.append([
                (name_bbox, "left"),
                (price_bbox, "right")
            ])
            current_y += product_height
        
        return current_y
    
    def _generate_medium_product_layout(
        self, 
        product_height: int, 
        x: int, 
        margin_x: int, 
        content_width: int, 
        current_y: int, 
        product_layouts: List[List[Tuple[List[int], str]]]
    ) -> int:
        """
        Generuje layout dla produktu ze średnio długą nazwą.
        
        Args:
            product_height: Wysokość linii produktu
            x: Pozycja x początku paragonu
            margin_x: Margines
            content_width: Szerokość treści
            current_y: Aktualna pozycja y
            product_layouts: Lista layoutów produktów do aktualizacji
            
        Returns:
            Zaktualizowana pozycja y
        """
        # Nazwa produktu na pełną szerokość
        name_bbox = [x + margin_x, current_y, content_width, product_height]
        product_layouts.append([
            (name_bbox, "left")
        ])
        current_y += product_height
        
        # Cena w nowej linii
        price_bbox = [x + margin_x, current_y, content_width, product_height]
        product_layouts.append([
            (price_bbox, "right")  # Wyrównanie do prawej
        ])
        current_y += product_height
        
        return current_y
    
    def _generate_short_product_layout(
        self, 
        product_height: int, 
        x: int, 
        margin_x: int, 
        content_width: int, 
        current_y: int, 
        product_layouts: List[List[Tuple[List[int], str]]]
    ) -> int:
        """
        Generuje layout dla produktu z krótką nazwą.
        
        Args:
            product_height: Wysokość linii produktu
            x: Pozycja x początku paragonu
            margin_x: Margines
            content_width: Szerokość treści
            current_y: Aktualna pozycja y
            product_layouts: Lista layoutów produktów do aktualizacji
            
        Returns:
            Zaktualizowana pozycja y
        """
        # Standardowy layout z nakładaniem - nazwa i cena w jednej linii
        # NAKŁADANIE: Definiujemy procent nakładania i szerokości
        name_width = int(content_width * 0.6)        # 60% szerokości dla nazwy
        price_width = int(content_width * 0.65)      # 65% szerokości dla ceny  
        overlap = int(content_width * 0.25)          # 25% nakładania
        
        name_bbox = [x + margin_x, current_y, name_width, product_height]
        price_bbox = [x + margin_x + name_width - overlap, current_y, price_width, product_height]
        
        product_layouts.append([
            (name_bbox, "left"),
            (price_bbox, "right")
        ])
        current_y += product_height
        
        return current_y
    
    def _generate_vat_summary_layout(
        self, 
        current_y: int, 
        x: int, 
        margin_x: int, 
        content_width: int, 
        vat_summary: Dict[str, Dict[str, Any]]
    ) -> Tuple[int, Dict[str, List[Tuple[List[int], str]]]]:
        """
        Generuje layout dla podsumowania VAT.
        
        Args:
            current_y: Aktualna pozycja y
            x: Pozycja x początku paragonu
            margin_x: Margines
            content_width: Szerokość treści
            vat_summary: Podsumowanie VAT
            
        Returns:
            Krotka (zaktualizowana pozycja y, słownik layoutów sekcji)
        """
        layouts = {}
        vat_layouts = []
        
        # Podsumowanie VAT - informacja do lewej, kwoty do prawej
        for symbol, data in vat_summary.items():
            if data["net"] > 0:
                vat_height = self.heights.get("vat_line", 20)
                vat_label_width = int(content_width * 0.6)
                vat_amount_width = int(content_width * 0.4)
                
                # Sprzedaż opodatkowana
                vat_label_bbox = [x + margin_x, current_y, vat_label_width, vat_height]
                vat_amount_bbox = [x + margin_x + vat_label_width, current_y, vat_amount_width, vat_height]
                
                vat_layouts.append([
                    (vat_label_bbox, "left"),
                    (vat_amount_bbox, "right")
                ])
                
                current_y += vat_height
                
                # Kwota VAT
                vat_tax_label_bbox = [x + margin_x, current_y, vat_label_width, vat_height]
                vat_tax_amount_bbox = [x + margin_x + vat_label_width, current_y, vat_amount_width, vat_height]
                
                vat_layouts.append([
                    (vat_tax_label_bbox, "left"),
                    (vat_tax_amount_bbox, "right")
                ])
                
                current_y += vat_height
        
        layouts["vat_summary"] = vat_layouts
        
        # Separator po VAT
        if self._should_display_separator("vat"):
            separator_height = self.heights.get("separator", 15)
            separator_bbox = [x + margin_x, current_y, content_width, separator_height]
            layouts["vat_separator"] = [(separator_bbox, "center")]
            current_y += separator_height + self.spacing.get("after_separator", 5)
        
        return current_y, layouts

    def _generate_payment_layout(
        self, 
        current_y: int, 
        x: int, 
        margin_x: int, 
        content_width: int
    ) -> Tuple[int, Dict[str, List[Tuple[List[int], str]]]]:
        """
        Generuje layout dla podsumowania płatności.
        
        Args:
            current_y: Aktualna pozycja y
            x: Pozycja x początku paragonu
            margin_x: Margines
            content_width: Szerokość treści
            
        Returns:
            Krotka (zaktualizowana pozycja y, słownik layoutów sekcji)
        """
        layouts = {}
        
        # Podsumowanie płatności - tekst do lewej, kwota do prawej
        current_y += self.spacing.get("before_payment", 10)
        payment_label_width = int(content_width * 0.6)
        payment_amount_width = int(content_width * 0.4)
        
        # Suma - wyraźnie większa i pogrubiona
        sum_height = self.heights.get("total_sum", 30)
        sum_label_bbox = [x + margin_x, current_y, payment_label_width, sum_height]
        sum_amount_bbox = [x + margin_x + payment_label_width, current_y, payment_amount_width, sum_height]
        
        layouts["total_sum"] = [
            (sum_label_bbox, "left"),
            (sum_amount_bbox, "right")
        ]
        
        current_y += sum_height
        
        # Sposób płatności
        payment_height = self.heights.get("payment_method", 20)
        payment_method_bbox = [x + margin_x, current_y, payment_label_width, payment_height]
        payment_amount_bbox = [x + margin_x + payment_label_width, current_y, payment_amount_width, payment_height]
        
        layouts["payment_method"] = [
            (payment_method_bbox, "left"),
            (payment_amount_bbox, "right")
        ]
        
        current_y += payment_height + self.spacing.get("after_payment", 10)
        
        # Separator przed stopką
        if self._should_display_separator("payment"):
            separator_height = self.heights.get("separator", 15)
            separator_bbox = [x + margin_x, current_y, content_width, separator_height]
            layouts["payment_separator"] = [(separator_bbox, "center")]
            current_y += separator_height + self.spacing.get("after_separator", 5)
        
        return current_y, layouts

    def _generate_footer_layout(
        self, 
        current_y: int, 
        x: int, 
        margin_x: int, 
        content_width: int
    ) -> Tuple[int, Dict[str, List[Tuple[List[int], str]]]]:
        """
        Generuje layout dla stopki paragonu.
        
        Args:
            current_y: Aktualna pozycja y
            x: Pozycja x początku paragonu
            margin_x: Margines
            content_width: Szerokość treści
            
        Returns:
            Krotka (zaktualizowana pozycja y, słownik layoutów sekcji)
        """
        layouts = {}
        
        # Stopka - wyrównana do środka
        footer_height = self.heights.get("footer", 20)
        footer_bbox = [x + margin_x, current_y, content_width, footer_height]
        layouts["footer"] = [(footer_bbox, "center")]
        
        current_y += footer_height
        
        return current_y, layouts