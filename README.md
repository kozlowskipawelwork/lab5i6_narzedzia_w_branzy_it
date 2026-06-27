# Konwerter danych — JSON / YAML / XML

Projekt koncowy z przedmiotu **Narzedzia w branzy IT** (Lab5 i 6).
Program konwertuje dane miedzy formatami `.json`, `.yml/.yaml` i `.xml`.

## Uzycie (CLI)

```
program.exe pathFile1.x pathFile2.y
```

gdzie `x` i `y` to jeden z formatow `.json` / `.yml` / `.xml`. Program rozpoznaje
format po rozszerzeniu, wczytuje dane z pliku wejsciowego i zapisuje je do pliku
wyjsciowego w nowym formacie.

Przyklad:

```
program.exe dane.json dane.yml
```

## Struktura

```
project.py              # CLI – wejscie programu + parsowanie argumentow (Task1)
gui.py                  # GUI (pywebview) – Task8/9
converter/
  core.py               # rdzen: load/dump dla JSON/YAML/XML + walidacja (Task2-7)
web/
  index.html            # interfejs HTML/CSS (motyw "Nocturne")
installResources.ps1    # Task0 – instalacja komponentow pip (uzywany w CI)
requirements.txt        # zaleznosci (pip install -r)
.github/workflows/      # GitHub Actions – auto-build .exe
```

## Uruchomienie lokalne

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # GUI na Linux: pip install "pywebview[qt]"

python project.py dane.json dane.yml     # CLI
python gui.py                            # GUI
```

## Budowanie .exe (PyInstaller)

```bash
pyinstaller --onefile project.py                              # CLI
pyinstaller --onefile --noconsole --add-data "web;web" gui.py # GUI (Windows)
```

Na Linux/macOS separator w `--add-data` to `:` (czyli `"web:web"`).
Gotowy `.exe` powstaje automatycznie w GitHub Actions (artefakt builda).

> Uwaga: przy zapisie do XML wszystkie wartosci staja sie tekstem (np. liczba
> `1` wroci jako `"1"`) — to wbudowane ograniczenie formatu XML, nie blad.

## Mapowanie taskow

| Task | Zakres | Gdzie |
|------|--------|-------|
| Task0 | skrypt instalacyjny pip | `installResources.ps1` |
| Task1 | parsowanie argumentow | `project.py` |
| Task2/3 | wczytanie/zapis JSON + walidacja | `converter/core.py` |
| Task4/5 | wczytanie/zapis YAML + walidacja | `converter/core.py` |
| Task6/7 | wczytanie/zapis XML + walidacja | `converter/core.py` |
| Task8 | wersja z UI | `gui.py`, `web/index.html` |
| Task9 | async odczyt/zapis w UI | `gui.py` (watek roboczy) |

## Konwencja branchy

Kazdy task na osobnej galezi: `Task0`, `Task1`, ... `Task9` — scalane do `master`.
