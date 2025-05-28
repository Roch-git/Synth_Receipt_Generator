"""
Receipt Content
==============

Specjalizowana klasa do generowania zawartości paragonu sklepowego.
Odpowiada za tworzenie tekstu paragonu, formatowanie produktów, cen,
oraz zarządzanie layoutem tekstu.
"""
import json
import random
from typing import Dict, List, Tuple, Any, Optional, Union

from synthtiger import components, layers

from layouts.receipt_layout import ReceiptLayout
from utils.text_processing import format_number, split_long_text, weighted_choice, format_price


class ReceiptContent:
    """
    Klasa odpowiedzialna za generowanie zawartości paragonu.
    
    Implementuje logikę tworzenia elementów tekstowych paragonu, formatowania cen,
    dat, oraz innych elementów tekstowych zgodnie z konfiguracją.
    
    Attributes:
        margin (float): Margines dokumentu.
        font (components.BaseFont): Komponent czcionki.
        layout (ReceiptLayout): Układ paragonu.
        chosen_separator (Dict[str, str]): Wybrany separator sekcji.
        separator_length_factor (float): Współczynnik długości separatora.
        separator_config (Dict): Konfiguracja separatorów.
        products_count (List[int]): Zakres liczby produktów [min, max].
        formatting_config (Dict): Konfiguracja formatowania tekstu.
        corpus_path (str): Ścieżka do pliku korpusu.
        corpus (Dict): Dane korpusu tekstowego.
        textbox_config (Dict): Konfiguracja pola tekstowego.
        content_color (components.Switch): Komponent koloru treści.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Inicjalizacja generatora zawartości paragonu.
        
        Args:
            config: Konfiguracja generatora zawartości.
        """
        self.margin = config.get("margin", 0.05)
        self.font = components.BaseFont(**config.get("font", {}))

        # Inicjalizacja układu paragonu i przekazanie marginesy
        layout_config = config.get("layout", {})
        layout_config["margin"] = self.margin  # Przekazujemy margin do layoutu
        self.layout = ReceiptLayout(layout_config)

        # Inicjalizacja domyślnych wartości dla separatorów
        self.chosen_separator = {"symbol": "-", "name": "dash"}
        self.separator_length_factor = 0.35

        # Inicjalizacja układu paragonu
        layout_config = config.get("layout", {})
        self.separator_config = self.layout.separator_config
        
        # Inicjalizacja układu paragonu
        self.layout = ReceiptLayout(config.get("layout", {}))
        
        # Pobieranie zakresu liczby produktów
        self.products_count = config.get("products_count", [3, 15])
        
        # Przekazanie zakresu liczby produktów do układu
        self.layout.set_products_count(self.products_count)

        # Wczytanie konfiguracji formatowania
        self.formatting_config = config.get("formatting", {})
        
        # Zapewnienie domyślnych wartości jeśli brak konfiguracji
        if not self.formatting_config:
            self.formatting_config = self._get_default_formatting()
        
        # Wczytanie korpusu - tylko raz
        corpus_config = config.get("text", {})
        self.corpus_path = corpus_config.get("path", "receipt_corpus.json")
        
        self._load_corpus()
        
        # Konfiguracja tekstboxu i koloru
        self.textbox_config = config.get("textbox", {})
        self.content_color = components.Switch(components.RGB(), **config.get("content_color", {}))
        
        # Atrybuty inicjalizowane podczas generowania
        self.current_formatting = {}

    def _get_default_formatting(self) -> Dict[str, List[Dict[str, Any]]]:
        """Zwraca domyślną konfigurację formatowania paragonu.
        
        Returns:
            Domyślna konfiguracja formatowania
        """
        return {
            "multiply_signs": [{"symbol": "x", "weight": 5}, {"symbol": "*", "weight": 1}, {"symbol": "X", "weight": 1}],
            "unit_formats": [{"format": "szt.", "weight": 1}, {"format": "szt", "weight": 4}, {"format": "", "weight": 2}],
            "decimal_separators": [{"symbol": ".", "weight": 1}, {"symbol": ",", "weight": 9}],
            "price_formats": [{"format": "standard", "weight": 5}, {"format": "no_spaces", "weight": 2}, {"format": "hybrid", "weight": 5}],
            "date_formats": [{"format": "dash", "weight": 4}, {"format": "dot", "weight": 3}, {"format": "slash", "weight": 2}],
            "sum_formats": [{"format": "SUMA PLN:", "weight": 8}, {"format": "SUMA:", "weight": 1}, {"format": "RAZEM:", "weight": 1}],
            "receipt_number_formats": [{"format": "Nr paragonu: {number}", "weight": 5}, {"format": "Paragon nr {number}", "weight": 3}, {"format": "#{number}", "weight": 2}, {"format": "FV {number}", "weight": 1}]
        }

    def _load_corpus(self) -> None:
        """Wczytuje korpus z pliku JSON.
        
        Raises:
            FileNotFoundError: Gdy nie znaleziono pliku korpusu
            ValueError: Gdy plik korpusu zawiera nieprawidłowy format JSON
        """
        try:
            with open(self.corpus_path, 'r', encoding='utf-8') as f:
                self.corpus = json.load(f)
                self.layout.corpus = self.corpus  # Przekazanie korpusu do layoutu
        except FileNotFoundError:
            raise FileNotFoundError(f"Nie znaleziono pliku korpusu: {self.corpus_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Plik korpusu {self.corpus_path} zawiera nieprawidłowy format JSON")
    
    def generate(self, size: Tuple[int, int]) -> Tuple[List[layers.Layer], List[str], Dict[str, Any]]:
        """
        Generuje zawartość paragonu o podanym rozmiarze.
        
        Args:
            size: Rozmiar paragonu (szerokość, wysokość)
            
        Returns:
            Krotka (warstwy tekstowe, teksty, dane strukturalne)
        """
        width, height = size
        
        # Określenie marginesów
        margin_x = int(width * self.margin)
        margin_y = int(height * self.margin)
        layout_bbox = [margin_x, margin_y, width - 2*margin_x, height - 2*margin_y]

        # Na początku generacji losujemy formatowanie dla tego paragonu
        self.current_formatting = self._select_formatting()
        
        # Przekazujemy wybrany format do obiektu layout, jeśli potrzebny
        if hasattr(self, 'layout'):
            self.layout.current_formatting = self.current_formatting
        
        # Generowanie układu paragonu
        layout_data = self.layout.generate(layout_bbox)
        layouts = layout_data[0]  # Słownik layoutów
        receipt_data = {
            'products': layout_data[1],
            'payment_method': layout_data[2],
            'total_price': layout_data[3],
            'vat_summary': layout_data[4],
            'separator': layout_data[5],
            'receipt_date': layout_data[6],
            'receipt_number': layout_data[7],
            'receipt_header': layout_data[8]
        }
        
        # Wybieramy jedną wspólną czcionkę dla całego paragonu
        base_font = self.font.sample()
        
        # Losowanie jednego separatora dla całego paragonu
        self._select_receipt_separator()
        self.layout.chosen_separator = self.chosen_separator
        self.layout.separator_length_factor = self.separator_length_factor
        
        # Inicjalizacja słowników dla warstw i tekstów
        text_layers_dict = {}
        texts_dict = {}
        
        # Generowanie poszczególnych sekcji paragonu
        self._generate_header(text_layers_dict, texts_dict, base_font, layouts, receipt_data)
        self._generate_products(text_layers_dict, texts_dict, base_font, layouts, receipt_data)
        self._generate_vat_summary(text_layers_dict, texts_dict, base_font, layouts, receipt_data)
        self._generate_payment_summary(text_layers_dict, texts_dict, base_font, layouts, receipt_data)
        self._generate_footer(text_layers_dict, texts_dict, base_font, layouts, receipt_data)
                
        # Konwersja słowników na listy w określonej kolejności
        text_layers, texts = self._convert_dicts_to_lists(text_layers_dict, texts_dict)
        
        # Aplikowanie koloru treści
        self.content_color.apply([layer for layer in text_layers if layer is not None])
        
        # Filtrowanie pustych warstw (None)
        filtered_layers, filtered_texts = self._filter_empty_layers(text_layers, texts)
        
        # Przygotowanie strukturalnych danych dla DONUT
        structured_data = self._prepare_structured_data(texts_dict, receipt_data)

        return filtered_layers, filtered_texts, structured_data
    
    def _select_formatting(self) -> Dict[str, str]:
        """Losuje formatowanie dla bieżącego paragonu.
        
        Returns:
            Słownik z wybranymi opcjami formatowania
        """
        formatting = {}
        
        # Wykorzystanie funkcji pomocniczej weighted_choice z utils
        formatting['multiply_sign'] = weighted_choice(
            self.formatting_config.get("multiply_signs", [{"symbol": "x", "weight": 1}]), 
            'symbol'
        )
        
        formatting['unit_format'] = weighted_choice(
            self.formatting_config.get("unit_formats", [{"format": "szt.", "weight": 1}]), 
            'format'
        )
        
        formatting['decimal_separator'] = weighted_choice(
            self.formatting_config.get("decimal_separators", [{"symbol": ".", "weight": 1}]), 
            'symbol'
        )
        
        formatting['price_format'] = weighted_choice(
            self.formatting_config.get("price_formats", [{"format": "standard", "weight": 1}]), 
            'format'
        )
        
        formatting['date_format'] = weighted_choice(
            self.formatting_config.get("date_formats", [{"format": "dash", "weight": 1}]), 
            'format'
        )
        
        formatting['sum_format'] = weighted_choice(
            self.formatting_config.get("sum_formats", [{"format": "SUMA PLN:", "weight": 1}]), 
            'format'
        )
        
        formatting['receipt_number_format'] = weighted_choice(
            self.formatting_config.get("receipt_number_formats", [{"format": "Nr paragonu: {number}", "weight": 1}]), 
            'format'
        )
        
        return formatting
    
    def _format_number(self, number: float, decimal_places: int = 2) -> str:
        """
        Formatuje liczbę używając wybranego separatora dziesiętnego.
        
        Args:
            number: Liczba do sformatowania
            decimal_places: Liczba miejsc po przecinku
            
        Returns:
            Sformatowana liczba jako tekst
        """
        return format_number(number, self.current_formatting['decimal_separator'], decimal_places)
    
    def _format_price(self, product: Dict[str, Any]) -> str:
        """Formatuje cenę produktu zgodnie z wybranym formatem.
        
        Args:
            product: Słownik z danymi produktu
            
        Returns:
            Sformatowana cena jako tekst
        """
        quantity = product['quantity']
        unit = product['unit']
        unit_price = product['unit_price']
        total_price = product['total_price']
        vat_symbol = product['vat_symbol']
        
        # Przygotowanie elementów
        multiply_sign = self.current_formatting['multiply_sign']
        
        # Tylko kg i l zachowują swoją oryginalną nazwę jednostki
        if unit in ["kg", "l"]:
            unit_display = unit
        else:
            # Dla wszystkich innych jednostek używamy wylosowanego formatu
            unit_display = self.current_formatting['unit_format']
        
        return format_price(
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            vat_symbol=vat_symbol,
            unit=unit_display,
            multiply_sign=multiply_sign,
            decimal_separator=self.current_formatting['decimal_separator'],
            price_format=self.current_formatting['price_format']
        )
    
    def _select_receipt_separator(self) -> None:
        """
        Wybiera jeden typ separatora i jego długość dla całego paragonu.
        Ustawia wartości w atrybutach klasy do wykorzystania we wszystkich separatorach.
        """
        # Wybieramy typ separatora na podstawie wag (tylko raz dla całego paragonu)
        separator_types = self.separator_config["types"]
        weights = [sep["weight"] for sep in separator_types]
        self.chosen_separator = random.choices(separator_types, weights=weights, k=1)[0]
        
        # Generujemy współczynnik długości (tylko raz dla całego paragonu)
        length_range = self.separator_config["length"]
        self.separator_length_factor = random.uniform(length_range[0], length_range[1])

    def _convert_dicts_to_lists(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any]
    ) -> Tuple[List[Any], List[str]]:
        """Konwertuje słowniki warstw i tekstów na listy w określonej kolejności.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych
            texts_dict: Słownik tekstów
            
        Returns:
            Krotka (lista warstw, lista tekstów)
        """
        text_layers = []
        texts = []
        
        # Definicja kolejności renderowania sekcji
        sections_order = [
            "shop_name", "shop_address", "shop_tax_id", "header_separator",
            "date_number", "receipt_header", "title_separator",
            "products", "products_separator",
            "vat_summary", "vat_separator",
            "total_sum", "payment_method", "payment_separator",
            "footer"
        ]
        
        # Konwersja słowników na listy z zachowaniem kolejności
        for section in sections_order:
            if section in text_layers_dict:
                if isinstance(text_layers_dict[section], list):
                    text_layers.extend(text_layers_dict[section])
                    texts.extend(texts_dict[section])
                else:
                    text_layers.append(text_layers_dict[section])
                    texts.append(texts_dict[section])
        
        return text_layers, texts
    
    def _filter_empty_layers(
        self, 
        text_layers: List[Any], 
        texts: List[str]
    ) -> Tuple[List[Any], List[str]]:
        """Filtruje puste warstwy (None) z list.
        
        Args:
            text_layers: Lista warstw tekstowych
            texts: Lista tekstów
            
        Returns:
            Krotka (filtrowana lista warstw, filtrowana lista tekstów)
        """
        filtered_layers = []
        filtered_texts = []
        
        for layer, text in zip(text_layers, texts):
            if layer is not None:
                filtered_layers.append(layer)
                filtered_texts.append(text)
        
        return filtered_layers, filtered_texts
    
    def _prepare_structured_data(
        self, 
        texts_dict: Dict[str, Any], 
        receipt_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Przygotowuje strukturalne dane dla DONUT.
        
        Args:
            texts_dict: Słownik tekstów
            receipt_data: Dane paragonu
            
        Returns:
            Słownik z danymi strukturalnymi
        """
        # Pobieramy dane o sklepie
        shop_data = {
            "name": texts_dict.get("shop_name", ""),
            "address": texts_dict.get("shop_address", ""),
        }
        
        # Stworzone od nowa produkty z zaokrąglonymi cenami
        cleaned_products = []
        for product in receipt_data['products']:
            cleaned_product = {
                "name": product["name"],
                "quantity": product["quantity"],
                "unit": product["unit"],
                "unit_price": round(product["unit_price"], 2),  # Zaokrąglenie
                "total_price": round(product["total_price"], 2)  # Zaokrąglenie
            }
            cleaned_products.append(cleaned_product)

        structured_data = {
            "shop": shop_data,
            "date": receipt_data['receipt_date'],
            "number": receipt_data['receipt_number'],
            "products": cleaned_products,
            "total": round(receipt_data['total_price'], 2)  # Zaokrąglenie sumy
        }
        
        return structured_data
    
    def _convert_dicts_to_lists(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any]
    ) -> Tuple[List[Any], List[str]]:
        """Konwertuje słowniki warstw i tekstów na listy w określonej kolejności.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych
            texts_dict: Słownik tekstów
            
        Returns:
            Krotka (lista warstw, lista tekstów)
        """
        text_layers = []
        texts = []
        
        # Definicja kolejności renderowania sekcji
        sections_order = [
            "shop_name", "shop_address", "shop_tax_id", "header_separator",
            "date_number", "receipt_header", "title_separator",
            "products", "products_separator",
            "vat_summary", "vat_separator",
            "total_sum", "payment_method", "payment_separator",
            "footer"
        ]
        
        # Konwersja słowników na listy z zachowaniem kolejności
        for section in sections_order:
            if section in text_layers_dict:
                if isinstance(text_layers_dict[section], list):
                    text_layers.extend(text_layers_dict[section])
                    texts.extend(texts_dict[section])
                else:
                    text_layers.append(text_layers_dict[section])
                    texts.append(texts_dict[section])
        
        return text_layers, texts
    
    def _filter_empty_layers(
        self, 
        text_layers: List[Any], 
        texts: List[str]
    ) -> Tuple[List[Any], List[str]]:
        """Filtruje puste warstwy (None) z list.
        
        Args:
            text_layers: Lista warstw tekstowych
            texts: Lista tekstów
            
        Returns:
            Krotka (filtrowana lista warstw, filtrowana lista tekstów)
        """
        filtered_layers = []
        filtered_texts = []
        
        for layer, text in zip(text_layers, texts):
            if layer is not None:
                filtered_layers.append(layer)
                filtered_texts.append(text)
        
        return filtered_layers, filtered_texts
    
    def _prepare_structured_data(
        self, 
        texts_dict: Dict[str, Any], 
        receipt_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Przygotowuje strukturalne dane dla DONUT.
        
        Args:
            texts_dict: Słownik tekstów
            receipt_data: Dane paragonu
            
        Returns:
            Słownik z danymi strukturalnymi
        """
        # Pobieramy dane o sklepie
        shop_data = {
            "name": texts_dict.get("shop_name", ""),
            "address": texts_dict.get("shop_address", ""),
        }
        
        # Stworzone od nowa produkty z zaokrąglonymi cenami
        cleaned_products = []
        for product in receipt_data['products']:
            cleaned_product = {
                "name": product["name"],
                "quantity": product["quantity"],
                "unit": product["unit"],
                "unit_price": round(product["unit_price"], 2),  # Zaokrąglenie
                "total_price": round(product["total_price"], 2)  # Zaokrąglenie
            }
            cleaned_products.append(cleaned_product)

        structured_data = {
            "shop": shop_data,
            "date": receipt_data['receipt_date'],
            "number": receipt_data['receipt_number'],
            "products": cleaned_products,
            "total": round(receipt_data['total_price'], 2)  # Zaokrąglenie sumy
        }
        
        return structured_data
    
    def _create_text_layer(
        self, 
        text: str, 
        bbox: List[int], 
        base_font: Dict[str, Any], 
        align: str = "left", 
        size_factor: float = 0.7, 
        bold: bool = False, 
        min_size: int = 8
    ) -> Optional[layers.TextLayer]:
        """
        Tworzy warstwę tekstową z odpowiednim skalowaniem i wyrównaniem.
        
        Args:
            text: Tekst do umieszczenia na warstwie
            bbox: Prostokąt określający położenie i rozmiar warstwy [x, y, width, height]
            base_font: Bazowa czcionka
            align: Wyrównanie tekstu ('left', 'right', 'center')
            size_factor: Współczynnik rozmiaru czcionki względem wysokości boksu
            bold: Czy tekst ma być pogrubiony
            min_size: Minimalny rozmiar czcionki
            
        Returns:
            Warstwa tekstowa lub None w przypadku błędu
        """
        if not text or not bbox:
            return None
            
        x, y, w, h = bbox
        font = base_font.copy()
        font["size"] = max(min_size, int(h * size_factor))
        font["bold"] = bold
        
        try:
            text_layer = layers.TextLayer(text, **font)
            
            # Ustawienie koloru tekstu
            brightness = random.randint(150, 200)
            text_layer.color = (brightness, brightness, brightness, 255)
            
            # Skalowanie jeśli tekst jest zbyt szeroki
            if text_layer.width > w:
                scale_factor = w / text_layer.width
                font["size"] = max(min_size, int(font["size"] * scale_factor))
                text_layer = layers.TextLayer(text, **font)
            
            # Pozycjonowanie
            text_layer.top = y
            if align == "left":
                text_layer.left = x
            elif align == "right":
                text_layer.right = x + w
            elif align == "center":
                text_layer.centerx = x + w/2
            
            return text_layer
        except Exception as e:
            print(f"Błąd podczas tworzenia warstwy tekstowej: {e}")
            return None
        
    def _generate_separator(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any], 
        location: str, 
        bbox: Optional[List[int]], 
        base_font: Dict[str, Any]
    ) -> bool:
        """Generuje separator w określonej lokalizacji.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych do aktualizacji
            texts_dict: Słownik tekstów do aktualizacji
            location: Nazwa lokalizacji separatora
            bbox: Prostokąt określający położenie i rozmiar warstwy
            base_font: Bazowa czcionka
            
        Returns:
            True jeśli separator został wygenerowany, False w przeciwnym przypadku
        """
        # Jeśli nie ma bbox (bo ReceiptLayout zdecydował, że nie ma separatora)
        if bbox is None:
            return False
        
        # Sprawdzamy, czy typ separatora ma określoną własną długość
        separator_length = self.separator_length_factor
        if "length" in self.chosen_separator:
            # Używamy długości z wybranego typu
            separator_length = self.chosen_separator["length"]
            
        # Generowanie warstwy separatora
        symbol = self.chosen_separator["symbol"]
        count = int(bbox[2] * separator_length)
        actual_separator = symbol * count
        
        separator_layer = self._create_text_layer(
            text=actual_separator,
            bbox=bbox,
            base_font=base_font,
            align="center",
            size_factor=0.7
        )
        
        if separator_layer:
            text_layers_dict[f"{location}_separator"] = separator_layer
            texts_dict[f"{location}_separator"] = actual_separator
            return True
            
        return False
    
    def _generate_header(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any], 
        base_font: Dict[str, Any], 
        layouts: Dict[str, Any], 
        receipt_data: Dict[str, Any]
    ) -> None:
        """
        Generuje sekcję nagłówkową paragonu.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych do aktualizacji
            texts_dict: Słownik tekstów do aktualizacji
            base_font: Bazowa czcionka
            layouts: Słownik layoutów dla paragonu
            receipt_data: Dane paragonu
        """
        # Generowanie danych sklepu (nazwa, adres, NIP)
        shop_data = self._generate_shop_header(text_layers_dict, texts_dict, base_font, layouts)
        
        # Separator po danych sklepu
        header_separator_bbox = self._get_layout_bbox(layouts, "header_separator")
        self._generate_separator(text_layers_dict, texts_dict, "header", header_separator_bbox, base_font)
        
        # Data i numer paragonu
        self._generate_date_number(text_layers_dict, texts_dict, base_font, layouts, receipt_data)
        
        # Nagłówek PARAGON FISKALNY
        self._generate_receipt_title(text_layers_dict, texts_dict, base_font, layouts, receipt_data)
        
        # Separator po nagłówku
        title_separator_bbox = self._get_layout_bbox(layouts, "title_separator")
        self._generate_separator(text_layers_dict, texts_dict, "title", title_separator_bbox, base_font)
    
    def _get_layout_bbox(self, layouts: Dict[str, Any], section_name: str) -> Optional[List[int]]:
        """Pobiera bbox dla sekcji z layoutu.
        
        Args:
            layouts: Słownik layoutów
            section_name: Nazwa sekcji
            
        Returns:
            Bbox sekcji lub None jeśli sekcja nie istnieje
        """
        if section_name in layouts and layouts[section_name]:
            return layouts[section_name][0][0]
        return None
    
    def _generate_shop_header(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any], 
        base_font: Dict[str, Any], 
        layouts: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generuje nagłówek sklepu (nazwa, adres, NIP).
        
        Args:
            text_layers_dict: Słownik warstw tekstowych do aktualizacji
            texts_dict: Słownik tekstów do aktualizacji
            base_font: Bazowa czcionka
            layouts: Słownik layoutów dla paragonu
            
        Returns:
            Słownik z danymi sklepu
        """
        # Wybór losowego sklepu
        shop = random.choice(self.corpus["shop_names"])
        shop_name = shop["name"]
        
        # Wybór losowego adresu i NIP
        company_address = random.choice(self.corpus["company_info"]["addresses"])
        company_tax_id = random.choice(self.corpus["company_info"]["tax_ids"])
        
        # 1. Nazwa sklepu (pogrubiona i większa)
        shop_layer = self._create_text_layer(
            text=shop_name,
            bbox=layouts["shop_name"][0][0],  # bbox pierwszego elementu
            base_font=base_font,
            align="center",
            size_factor=0.9,
            bold=True
        )
        text_layers_dict["shop_name"] = shop_layer
        texts_dict["shop_name"] = shop_name
        
        # 2. Adres sklepu
        address_layer = self._create_text_layer(
            text=company_address,
            bbox=layouts["shop_address"][0][0],
            base_font=base_font,
            align="center",
            size_factor=0.7
        )
        text_layers_dict["shop_address"] = address_layer
        texts_dict["shop_address"] = company_address
        
        # 3. NIP
        nip_layer = self._create_text_layer(
            text=company_tax_id,
            bbox=layouts["shop_tax_id"][0][0],
            base_font=base_font,
            align="center",
            size_factor=0.7
        )
        text_layers_dict["shop_tax_id"] = nip_layer
        texts_dict["shop_tax_id"] = company_tax_id
        
        return {
            "name": shop_name,
            "address": company_address,
            "tax_id": company_tax_id
        }
    
    def _generate_date_number(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any], 
        base_font: Dict[str, Any], 
        layouts: Dict[str, Any], 
        receipt_data: Dict[str, Any]
    ) -> None:
        """
        Generuje sekcję daty i numeru paragonu.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych do aktualizacji
            texts_dict: Słownik tekstów do aktualizacji
            base_font: Bazowa czcionka
            layouts: Słownik layoutów dla paragonu
            receipt_data: Dane paragonu
        """
        # Generowanie warstwy daty
        date_layer = self._create_text_layer(
            text=receipt_data['receipt_date'],
            bbox=layouts["date_number"][0][0],
            base_font=base_font,
            align="left",
            size_factor=0.7
        )
        
        # Generowanie warstwy numeru paragonu
        number_layer = self._create_text_layer(
            text=receipt_data['receipt_number'],
            bbox=layouts["date_number"][1][0],
            base_font=base_font,
            align="right",
            size_factor=0.7
        )
        
        text_layers_dict["date_number"] = [date_layer, number_layer]
        texts_dict["date_number"] = [receipt_data['receipt_date'], receipt_data['receipt_number']]
    
    def _generate_receipt_title(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any], 
        base_font: Dict[str, Any], 
        layouts: Dict[str, Any], 
        receipt_data: Dict[str, Any]
    ) -> None:
        """
        Generuje nagłówek PARAGON FISKALNY.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych do aktualizacji
            texts_dict: Słownik tekstów do aktualizacji
            base_font: Bazowa czcionka
            layouts: Słownik layoutów dla paragonu
            receipt_data: Dane paragonu
        """
        # Używamy losowej skali dla nagłówka
        header_scale = random.uniform(
            self.layout.header_scale[0], 
            self.layout.header_scale[1]
        )
        
        header_layer = self._create_text_layer(
            text=receipt_data['receipt_header'],
            bbox=layouts["receipt_header"][0][0],
            base_font=base_font,
            align="center",
            size_factor=header_scale,  # Używamy wylosowanej skali
            bold=True
        )
        text_layers_dict["receipt_header"] = header_layer
        texts_dict["receipt_header"] = receipt_data['receipt_header']

    def _generate_products(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any], 
        base_font: Dict[str, Any], 
        layouts: Dict[str, Any], 
        receipt_data: Dict[str, Any]
    ) -> None:
        """
        Generuje listę produktów na paragonie.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych do aktualizacji
            texts_dict: Słownik tekstów do aktualizacji
            base_font: Bazowa czcionka
            layouts: Słownik layoutów dla paragonu
            receipt_data: Dane paragonu
        """
        products = receipt_data['products']
        product_layers = []
        product_texts = []
        
        # Pobieranie parametrów z layoutu
        layout_params = self._get_layout_text_parameters()
        
        # Generowanie layoutu dla każdego produktu
        layout_index = 0
        skipped_products = 0
        
        # Przetwarzanie produktów zgodnie z dostępnymi layoutami
        for product_idx, product in enumerate(products):
            # Sprawdzenie czy mamy jeszcze dostępne layouty
            if layout_index >= len(layouts["products"]):
                skipped_products += 1
                continue
                
            product_name = product["name"]
            name_length = len(product_name)
            
            # Obsługa produktów w zależności od długości nazwy
            if name_length > layout_params["max_chars_per_line"]:
                # Bardzo długa nazwa - podział na fragmenty
                layout_index = self._process_very_long_name_product(
                    product, layouts, layout_index, base_font, 
                    product_layers, product_texts, layout_params
                )
            elif name_length > layout_params["half_width_chars"]:
                # Średnio długa nazwa
                layout_index = self._process_medium_name_product(
                    product, layouts, layout_index, base_font, 
                    product_layers, product_texts
                )
            else:
                # Krótka nazwa
                layout_index = self._process_short_name_product(
                    product, layouts, layout_index, base_font, 
                    product_layers, product_texts
                )
        
        # Informacja o pominiętych produktach
        if skipped_products > 0:
            print(f"Uwaga: Pominięto {skipped_products} produktów z powodu braku layoutów")
        
        # Zapisanie rezultatów
        text_layers_dict["products"] = product_layers
        texts_dict["products"] = product_texts
        
        # Separator po produktach
        products_separator_bbox = self._get_layout_bbox(layouts, "products_separator")
        self._generate_separator(
            text_layers_dict, texts_dict, "products", 
            products_separator_bbox, base_font
        )
    
    def _get_layout_text_parameters(self) -> Dict[str, int]:
        """Pobiera parametry layoutu dotyczące tekstu.
        
        Returns:
            Słownik z parametrami tekstowymi layoutu
        """
        # Domyślne wartości
        params = {
            "max_chars_per_line": 50,
            "half_width_chars": 25
        }
        
        # Jeśli layout ma zdefiniowane własne parametry, użyj ich
        if hasattr(self.layout, 'max_chars_per_line'):
            params["max_chars_per_line"] = self.layout.max_chars_per_line
        
        if hasattr(self.layout, 'half_width_chars'):
            params["half_width_chars"] = self.layout.half_width_chars
            
        return params
    
    def _process_very_long_name_product(
        self, 
        product: Dict[str, Any], 
        layouts: Dict[str, Any], 
        layout_index: int, 
        base_font: Dict[str, Any], 
        product_layers: List[Any], 
        product_texts: List[str],
        layout_params: Dict[str, int]
    ) -> int:
        """
        Przetwarza produkt z bardzo długą nazwą.
        
        Args:
            product: Dane produktu
            layouts: Słownik layoutów
            layout_index: Aktualny indeks layoutu
            base_font: Bazowa czcionka
            product_layers: Lista warstw produktów do aktualizacji
            product_texts: Lista tekstów produktów do aktualizacji
            layout_params: Parametry layoutu
            
        Returns:
            Zaktualizowany indeks layoutu
        """
        product_name = product["name"]
        max_chars = layout_params["max_chars_per_line"]
        half_width_chars = layout_params["half_width_chars"]
        
        # Podział nazwy na fragmenty
        name_parts = split_long_text(product_name, max_chars)
        
        # Generowanie warstw dla każdej linii nazwy oprócz ostatniej
        for part in name_parts[:-1]:
            if layout_index >= len(layouts["products"]):
                break
                
            current_layout = layouts["products"][layout_index]
            
            # Zakładamy, że layout dla części nazwy zawiera tylko jeden element
            if len(current_layout) >= 1:
                part_bbox = current_layout[0][0]
                part_layer = self._create_text_layer(
                    text=part,
                    bbox=part_bbox,
                    base_font=base_font,
                    align="left",
                    size_factor=0.7
                )
                
                product_layers.append(part_layer)
                product_texts.append(part)
                
            layout_index += 1
        
        # Obsługa ostatniej części nazwy
        if layout_index < len(layouts["products"]):
            last_part = name_parts[-1]
            current_layout = layouts["products"][layout_index]
            
            # Decyzja o umieszczeniu ceny w zależności od długości ostatniej części
            if len(last_part) > half_width_chars:
                # Ostatnia część nazwy na pełną szerokość
                layout_index = self._process_last_part_full_width(
                    product, last_part, layouts, layout_index, base_font,
                    product_layers, product_texts
                )
            else:
                # Nazwa i cena w jednej linii
                layout_index = self._process_last_part_with_price(
                    product, last_part, layouts, layout_index, base_font,
                    product_layers, product_texts
                )
        
        return layout_index
    
    def _process_last_part_full_width(
        self, 
        product: Dict[str, Any], 
        last_part: str, 
        layouts: Dict[str, Any], 
        layout_index: int, 
        base_font: Dict[str, Any], 
        product_layers: List[Any], 
        product_texts: List[str]
    ) -> int:
        """
        Przetwarza ostatnią część bardzo długiej nazwy na pełną szerokość.
        
        Args:
            product: Dane produktu
            last_part: Ostatnia część nazwy
            layouts: Słownik layoutów
            layout_index: Aktualny indeks layoutu
            base_font: Bazowa czcionka
            product_layers: Lista warstw produktów do aktualizacji
            product_texts: Lista tekstów produktów do aktualizacji
            
        Returns:
            Zaktualizowany indeks layoutu
        """
        current_layout = layouts["products"][layout_index]
        name_bbox = current_layout[0][0]
        
        name_layer = self._create_text_layer(
            text=last_part,
            bbox=name_bbox,
            base_font=base_font,
            align="left",
            size_factor=0.7
        )
        
        product_layers.append(name_layer)
        product_texts.append(last_part)
        layout_index += 1
        
        # Cena w nowej linii
        if layout_index < len(layouts["products"]):
            price_layout = layouts["products"][layout_index]
            price_bbox = price_layout[0][0]
            
            price_text = self._format_price(product)
            price_layer = self._create_text_layer(
                text=price_text,
                bbox=price_bbox,
                base_font=base_font,
                align="right",
                size_factor=0.7
            )
            
            product_layers.append(price_layer)
            product_texts.append(price_text)
            layout_index += 1
            
        return layout_index
    
    def _process_last_part_with_price(
        self, 
        product: Dict[str, Any], 
        last_part: str, 
        layouts: Dict[str, Any], 
        layout_index: int, 
        base_font: Dict[str, Any], 
        product_layers: List[Any], 
        product_texts: List[str]
    ) -> int:
        """
        Przetwarza ostatnią część nazwy wraz z ceną w jednej linii.
        
        Args:
            product: Dane produktu
            last_part: Ostatnia część nazwy
            layouts: Słownik layoutów
            layout_index: Aktualny indeks layoutu
            base_font: Bazowa czcionka
            product_layers: Lista warstw produktów do aktualizacji
            product_texts: Lista tekstów produktów do aktualizacji
            
        Returns:
            Zaktualizowany indeks layoutu
        """
        current_layout = layouts["products"][layout_index]
        
        # Sprawdzamy, czy ostatnia część nazwy i cena są w jednej linii
        if len(current_layout) == 2:
            # Nazwa i cena w jednej linii
            name_bbox = current_layout[0][0]
            price_bbox = current_layout[1][0]
            
            name_layer = self._create_text_layer(
                text=last_part,
                bbox=name_bbox,
                base_font=base_font,
                align="left",
                size_factor=0.7
            )
            
            price_text = self._format_price(product)
            price_layer = self._create_text_layer(
                text=price_text,
                bbox=price_bbox,
                base_font=base_font,
                align="right",
                size_factor=0.7
            )
            
            product_layers.extend([name_layer, price_layer])
            product_texts.extend([last_part, price_text])
            
        layout_index += 1
        return layout_index
    
    def _process_medium_name_product(
        self, 
        product: Dict[str, Any], 
        layouts: Dict[str, Any], 
        layout_index: int, 
        base_font: Dict[str, Any], 
        product_layers: List[Any], 
        product_texts: List[str]
    ) -> int:
        """
        Przetwarza produkt ze średnio długą nazwą.
        
        Args:
            product: Dane produktu
            layouts: Słownik layoutów
            layout_index: Aktualny indeks layoutu
            base_font: Bazowa czcionka
            product_layers: Lista warstw produktów do aktualizacji
            product_texts: Lista tekstów produktów do aktualizacji
            
        Returns:
            Zaktualizowany indeks layoutu
        """
        product_name = product["name"]
        
        # Sprawdzamy czy mamy co najmniej dwa layouty (dla nazwy i ceny)
        if layout_index + 1 >= len(layouts["products"]):
            return layout_index  # Niewystarczająca liczba layoutów
            
        # Layout dla nazwy
        name_layout = layouts["products"][layout_index]
        name_bbox = name_layout[0][0]
        
        name_layer = self._create_text_layer(
            text=product_name,
            bbox=name_bbox,
            base_font=base_font,
            align="left",
            size_factor=0.7
        )
        
        product_layers.append(name_layer)
        product_texts.append(product_name)
        
        layout_index += 1
        
        # Layout dla ceny
        price_layout = layouts["products"][layout_index]
        price_bbox = price_layout[0][0]
        
        price_text = self._format_price(product)
        price_layer = self._create_text_layer(
            text=price_text,
            bbox=price_bbox,
            base_font=base_font,
            align="right",
            size_factor=0.7
        )
        
        product_layers.append(price_layer)
        product_texts.append(price_text)
        
        layout_index += 1
        return layout_index
    
    def _process_short_name_product(
        self, 
        product: Dict[str, Any], 
        layouts: Dict[str, Any], 
        layout_index: int, 
        base_font: Dict[str, Any], 
        product_layers: List[Any], 
        product_texts: List[str]
    ) -> int:
        """
        Przetwarza produkt z krótką nazwą.
        
        Args:
            product: Dane produktu
            layouts: Słownik layoutów
            layout_index: Aktualny indeks layoutu
            base_font: Bazowa czcionka
            product_layers: Lista warstw produktów do aktualizacji
            product_texts: Lista tekstów produktów do aktualizacji
            
        Returns:
            Zaktualizowany indeks layoutu
        """
        product_name = product["name"]
        
        # Sprawdzamy czy mamy dostępny layout
        if layout_index >= len(layouts["products"]):
            return layout_index
            
        current_layout = layouts["products"][layout_index]
        
        # Layout powinien mieć dwa elementy (nazwę i cenę)
        if len(current_layout) >= 2:
            name_bbox = current_layout[0][0]
            price_bbox = current_layout[1][0]
            
            name_layer = self._create_text_layer(
                text=product_name,
                bbox=name_bbox,
                base_font=base_font,
                align="left",
                size_factor=0.7
            )
            
            price_text = self._format_price(product)
            price_layer = self._create_text_layer(
                text=price_text,
                bbox=price_bbox,
                base_font=base_font,
                align="right",
                size_factor=0.7
            )
            
            product_layers.extend([name_layer, price_layer])
            product_texts.extend([product_name, price_text])
            
        layout_index += 1
        return layout_index
    
    def _generate_vat_summary(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any], 
        base_font: Dict[str, Any], 
        layouts: Dict[str, Any], 
        receipt_data: Dict[str, Any]
    ) -> None:
        """
        Generuje podsumowanie VAT na paragonie.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych do aktualizacji
            texts_dict: Słownik tekstów do aktualizacji
            base_font: Bazowa czcionka
            layouts: Słownik layoutów dla paragonu
            receipt_data: Dane paragonu
        """
        vat_summary = receipt_data['vat_summary']
        vat_layers = []
        vat_texts = []
        
        vat_section_idx = 0
        for symbol, data in vat_summary.items():
            if data["net"] > 0 and vat_section_idx < len(layouts["vat_summary"]):
                # Formatowanie liczb z wybranym separatorem
                net_amount = self._format_number(data['net'])
                tax_amount = self._format_number(data['tax'])
                
                # Dodanie linii sprzedaży opodatkowanej
                vat_section_idx = self._add_vat_net_line(
                    symbol, net_amount, layouts["vat_summary"], vat_section_idx,
                    base_font, vat_layers, vat_texts
                )
                
                # Dodanie linii kwoty VAT
                if vat_section_idx < len(layouts["vat_summary"]):
                    vat_section_idx = self._add_vat_tax_line(
                        symbol, data['rate'], tax_amount, layouts["vat_summary"], 
                        vat_section_idx, base_font, vat_layers, vat_texts
                    )
        
        text_layers_dict["vat_summary"] = vat_layers
        texts_dict["vat_summary"] = vat_texts
        
        # Separator po VAT
        vat_separator_bbox = self._get_layout_bbox(layouts, "vat_separator")
        self._generate_separator(
            text_layers_dict, texts_dict, "vat", 
            vat_separator_bbox, base_font
        )
    
    def _add_vat_net_line(
        self, 
        symbol: str, 
        net_amount: str, 
        vat_layouts: List[Any], 
        section_idx: int, 
        base_font: Dict[str, Any], 
        vat_layers: List[Any], 
        vat_texts: List[str]
    ) -> int:
        """
        Dodaje linię sprzedaży opodatkowanej VAT.
        
        Args:
            symbol: Symbol stawki VAT
            net_amount: Kwota netto
            vat_layouts: Layouty sekcji VAT
            section_idx: Indeks sekcji VAT
            base_font: Bazowa czcionka
            vat_layers: Lista warstw VAT do aktualizacji
            vat_texts: Lista tekstów VAT do aktualizacji
            
        Returns:
            Zaktualizowany indeks sekcji VAT
        """
        vat_layout = vat_layouts[section_idx]
        
        vat_label = f"Sprzedaż opod. {symbol}"
        label_layer = self._create_text_layer(
            text=vat_label,
            bbox=vat_layout[0][0],
            base_font=base_font,
            align="left",
            size_factor=0.7
        )
        vat_layers.append(label_layer)
        vat_texts.append(vat_label)
        
        # Kwota netto (prawa strona)
        amount_layer = self._create_text_layer(
            text=net_amount,
            bbox=vat_layout[1][0],
            base_font=base_font,
            align="right",
            size_factor=0.7
        )
        vat_layers.append(amount_layer)
        vat_texts.append(net_amount)
        
        return section_idx + 1
    
    def _add_vat_tax_line(
        self, 
        symbol: str, 
        rate: str, 
        tax_amount: str, 
        vat_layouts: List[Any], 
        section_idx: int, 
        base_font: Dict[str, Any], 
        vat_layers: List[Any], 
        vat_texts: List[str]
    ) -> int:
        """
        Dodaje linię kwoty podatku VAT.
        
        Args:
            symbol: Symbol stawki VAT
            rate: Stawka VAT
            tax_amount: Kwota podatku
            vat_layouts: Layouty sekcji VAT
            section_idx: Indeks sekcji VAT
            base_font: Bazowa czcionka
            vat_layers: Lista warstw VAT do aktualizacji
            vat_texts: Lista tekstów VAT do aktualizacji
            
        Returns:
            Zaktualizowany indeks sekcji VAT
        """
        vat_tax_layout = vat_layouts[section_idx]
        
        vat_tax_label = f"Kwota {symbol} {rate}"
        tax_label_layer = self._create_text_layer(
            text=vat_tax_label,
            bbox=vat_tax_layout[0][0],
            base_font=base_font,
            align="left",
            size_factor=0.7
        )
        vat_layers.append(tax_label_layer)
        vat_texts.append(vat_tax_label)
        
        # Kwota podatku (prawa strona)
        tax_amount_layer = self._create_text_layer(
            text=tax_amount,
            bbox=vat_tax_layout[1][0],
            base_font=base_font,
            align="right",
            size_factor=0.7
        )
        vat_layers.append(tax_amount_layer)
        vat_texts.append(tax_amount)
        
        return section_idx + 1
    
    def _generate_payment_summary(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any], 
        base_font: Dict[str, Any], 
        layouts: Dict[str, Any], 
        receipt_data: Dict[str, Any]
    ) -> None:
        """
        Generuje podsumowanie płatności na paragonie.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych do aktualizacji
            texts_dict: Słownik tekstów do aktualizacji
            base_font: Bazowa czcionka
            layouts: Słownik layoutów dla paragonu
            receipt_data: Dane paragonu
        """
        # Formatowanie kwoty z odpowiednim separatorem dziesiętnym
        total_price = receipt_data['total_price']
        total_amount = self._format_number(total_price)
        
        # Generowanie sumy
        self._generate_total_sum(
            text_layers_dict, texts_dict, base_font, layouts, 
            total_amount, self.current_formatting['sum_format']
        )
        
        # Generowanie metody płatności
        self._generate_payment_method(
            text_layers_dict, texts_dict, base_font, layouts, 
            receipt_data['payment_method'], total_amount
        )

        # Separator przed stopką
        payment_separator_bbox = self._get_layout_bbox(layouts, "payment_separator")
        self._generate_separator(
            text_layers_dict, texts_dict, "payment", 
            payment_separator_bbox, base_font
        )
    
    def _generate_total_sum(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any], 
        base_font: Dict[str, Any], 
        layouts: Dict[str, Any], 
        total_amount: str, 
        sum_format: str
    ) -> None:
        """
        Generuje linię sumy paragonu.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych do aktualizacji
            texts_dict: Słownik tekstów do aktualizacji
            base_font: Bazowa czcionka
            layouts: Słownik layoutów dla paragonu
            total_amount: Kwota sumy
            sum_format: Format etykiety sumy
        """
        # Zastosowanie wybranego formatu etykiety sumy (bez kwoty)
        sum_label_text = sum_format
        
        # Dodanie "PLN" po kwocie, jeśli nie ma go w etykiecie
        if "PLN" in sum_label_text:
            sum_amount_text = f"{total_amount}"
        else:
            sum_amount_text = f"{total_amount} PLN"
        
        # Tworzymy warstwy dla etykiety i kwoty
        sum_label_layer = self._create_text_layer(
            text=sum_label_text,
            bbox=layouts["total_sum"][0][0],
            base_font=base_font,
            align="left",
            size_factor=0.9,
            bold=True
        )
        
        sum_amount_layer = self._create_text_layer(
            text=sum_amount_text,
            bbox=layouts["total_sum"][1][0],
            base_font=base_font,
            align="right",
            size_factor=0.9,
            bold=True
        )
        
        text_layers_dict["total_sum"] = [sum_label_layer, sum_amount_layer]
        texts_dict["total_sum"] = [sum_label_text, sum_amount_text]
    
    def _generate_payment_method(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any], 
        base_font: Dict[str, Any], 
        layouts: Dict[str, Any], 
        payment_method: Dict[str, str], 
        total_amount: str
    ) -> None:
        """
        Generuje linię metody płatności.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych do aktualizacji
            texts_dict: Słownik tekstów do aktualizacji
            base_font: Bazowa czcionka
            layouts: Słownik layoutów dla paragonu
            payment_method: Metoda płatności
            total_amount: Kwota sumy
        """
        # Label sposobu płatności (lewa strona)
        pm_label_text = f"{payment_method['method']}:"
        pm_label_layer = self._create_text_layer(
            text=pm_label_text,
            bbox=layouts["payment_method"][0][0],
            base_font=base_font,
            align="left",
            size_factor=0.7
        )
        
        # Kwota płatności (prawa strona) - z odpowiednim separatorem
        pm_amount_text = f"{total_amount} PLN"
        pm_amount_layer = self._create_text_layer(
            text=pm_amount_text,
            bbox=layouts["payment_method"][1][0],
            base_font=base_font,
            align="right",
            size_factor=0.7
        )
        
        text_layers_dict["payment_method"] = [pm_label_layer, pm_amount_layer]
        texts_dict["payment_method"] = [pm_label_text, pm_amount_text]
    
    def _generate_footer(
        self, 
        text_layers_dict: Dict[str, Any], 
        texts_dict: Dict[str, Any], 
        base_font: Dict[str, Any], 
        layouts: Dict[str, Any], 
        receipt_data: Dict[str, Any]
    ) -> None:
        """
        Generuje stopkę paragonu.
        
        Args:
            text_layers_dict: Słownik warstw tekstowych do aktualizacji
            texts_dict: Słownik tekstów do aktualizacji
            base_font: Bazowa czcionka
            layouts: Słownik layoutów dla paragonu
            receipt_data: Dane paragonu
        """
        # Wybór losowej stopki
        receipt_footer = random.choice(self.corpus["receipt_footers"])
        
        # Generowanie warstwy tekstowej stopki
        footer_layer = self._create_text_layer(
            text=receipt_footer,
            bbox=layouts["footer"][0][0],
            base_font=base_font,
            align="center",
            size_factor=0.7
        )
        
        text_layers_dict["footer"] = footer_layer
        texts_dict["footer"] = receipt_footer