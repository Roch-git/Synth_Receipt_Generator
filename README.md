# Generator Syntetycznych Paragonów

Generator syntetycznych paragonów to narzędzie do tworzenia **realistycznych obrazów paragonów sklepowych** wraz z odpowiadającymi im metadanymi strukturalnymi. Świetnie nadaje się do generowania danych treningowych dla systemów OCR oraz modeli AI przetwarzających dokumenty.

---

## Przykłady wygenerowanych paragonów

<p align="center">
  <img src="images/screenshot_1.jpg" alt="Screenshot 1" width="250"/>
  <img src="images/screenshot_2.jpg" alt="Screenshot 2" width="250"/>
  <img src="images/screenshot_3.jpg" alt="Screenshot 3" width="250"/>
</p>

---

## Instalacja

### Wymagania

- Python **3.8** lub nowszy
- Pakiety Python:
  - `numpy`
  - `Pillow`
  - `synthtiger`
  - `pyyaml`

### Szybki start

1. **Klonowanie repozytorium**
    ```bash
    git clone https://github.com/Roch-git/Synth_Receipt_Generator.git
    cd Synth_Receipt_Generator
    ```

2. **(Opcjonalnie) Utwórz i aktywuj środowisko wirtualne**

    <details>
    <summary>Instrukcje (kliknij, by rozwinąć)</summary>

    **Tworzenie środowiska**
    ```bash
    python -m venv venv
    ```

    **Aktywacja środowiska**

    - **Windows:**
      ```bash
      venv\Scripts\activate
      ```
    - **macOS/Linux:**
      ```bash
      source venv/bin/activate
      ```
    </details>

3. **Instalacja zależności**
    ```bash
    pip install -r requirements.txt
    ```

---

## Sposób uruchomienia

Aby wygenerować paragony, użyj poniższej komendy (dostosuj argumenty według potrzeb):

```bash
python main.py --config config_receipt.yaml --output wygenerowane_paragony --count 50 --seed 123 --verbose
```
### Opis opcji uruchomienia

| Opcja       | Opis                                         | Wartość domyślna      |
| ----------- | -------------------------------------------- | --------------------- |
| `--config`  | Ścieżka do pliku konfiguracyjnego            | `config_receipt.yaml` |
| `--output`  | Katalog wyjściowy                            | `output`              |
| `--count`   | Liczba paragonów do wygenerowania            | `100`                 |
| `--seed`    | Ziarno losowości (dla powtarzalnych wyników) | `42`                  |
| `--verbose` | Włącza szczegółowe logowanie                 | `False`               |
