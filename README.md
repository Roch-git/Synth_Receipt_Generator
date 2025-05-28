# Generator Syntetycznych Paragonów

Generator syntetycznych paragonów to narzędzie do tworzenia realistycznie wyglądających obrazów paragonów sklepowych wraz z odpowiadającymi im metadanymi strukturalnymi. Jest to przydatne do generowania danych treningowych dla systemów OCR (Optical Character Recognition) oraz modeli AI specjalizujących się w przetwarzaniu dokumentów.

## Przykłady wygenerowanych paragonów

<p align="center">
  <img src="images/screenshot_1.png" alt="Screenshot 1" width="250"/>
  <img src="images/screenshot_2.png" alt="Screenshot 2" width="250"/>
  <img src="images/screenshot_3.png" alt="Screenshot 3" width="250"/>
</p>


## Instalacja

### Wymagania

- Python 3.8 lub nowszy
- Biblioteki Python:
  - numpy
  - Pillow
  - synthtiger
  - pyyaml

### Kroki instalacji

1. **Klonowanie repozytorium**
   ```bash
   git clone https://github.com/[Twój-Username]/generator-paragonow.git
   cd generator-paragonow

2. **Utworzenie wirtualnego środowiska (opcjonalne)**

# Utworzenie środowiska
python -m venv venv

# Aktywacja środowiska
# Na Windows:
venv\Scripts\activate

# Na macOS/Linux:
source venv/bin/activate

3. **Instalacja zależności**

pip install -r requirements.txt

### Sposób uruchomienia

Aby wygenerować paragony, użyj poniższej komendy:

```bash
python main.py --config config_receipt.yaml --output wygenerowane_paragony --count 50 --seed 123 --verbose
 ```


| Opcja       | Opis                                         | Wartość domyślna      |
| ----------- | -------------------------------------------- | --------------------- |
| `--config`  | Ścieżka do pliku konfiguracyjnego            | `config_receipt.yaml` |
| `--output`  | Katalog wyjściowy                            | `output`              |
| `--count`   | Liczba paragonów do wygenerowania            | `100`                 |
| `--seed`    | Ziarno losowości (dla powtarzalnych wyników) | `42`                  |
| `--verbose` | Włącza szczegółowe logowanie                 | `False`               |
