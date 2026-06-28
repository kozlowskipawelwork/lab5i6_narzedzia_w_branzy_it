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
gui.py                  # GUI (PySide6 / Qt) – Task8/9
converter/
  core.py               # rdzen: load/dump dla JSON/YAML/XML + walidacja (Task2-7)
web/
  index.html            # UI z iteracji pywebview (nieuzywane przez finalne GUI w PySide6)
installResources.ps1    # Task0 – instalacja komponentow pip (uzywany w CI)
requirements.txt        # zaleznosci (pip install -r)
.github/workflows/      # GitHub Actions – auto-build .exe
```

## Uruchomienie lokalne

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # GUI na Linux wymaga: sudo apt install libxcb-cursor0

python project.py dane.json dane.yml     # CLI
python gui.py                            # GUI
```

## Budowanie binarek (PyInstaller)

```bash
# Windows .exe (CI: runner windows):
pyinstaller --onefile --name konwerter project.py   # CLI -> konwerter.exe
pyinstaller --onefile --name konwerter-gui gui.py   # GUI -> konwerter-gui.exe

# Linux ELF (natywny, bez wine; CI: runner ubuntu):
pyinstaller --onefile --name konwerter project.py
pyinstaller --onefile --name konwerter-gui gui.py
```

GitHub Actions buduje automatycznie **dwa artefakty**:
- `konwerter-windows` — pliki `.exe` (CLI dziala tez pod wine; GUI `.exe` tylko na Windowsie —
  pod wine 9.0 nie startuje, patrz sekcja *Historia*),
- `konwerter-linux` — natywne ELF-y; GUI `konwerter-gui` uruchamia sie wprost na Linuksie
  (`./konwerter-gui`), **bez wine** (wymaga tylko systemowego `libxcb-cursor0`).

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
| Task8 | wersja z UI | `gui.py` |
| Task9 | async odczyt/zapis w UI | `gui.py` (watek roboczy) |

## Historia / decyzje projektowe (iteracje)

Sekcja szczera, opisujaca droge do finalnego rozwiazania GUI:

1. **Pierwszy wybor: pywebview (HTML/CSS).** Popelnilem blad wybierajac pywebview do
   GUI — wynikowy plik `.exe` GUI **nie uruchamia sie pod wine**, poniewaz pywebview
   na Windows wymaga silnika **Edge WebView2**, ktorego w wine nie ma. Przez to nie
   bylem w stanie przetestowac GUI `.exe` lokalnie na Linuksie.

2. **Iteracja z natywnym ELF-em w pipeline.** Rozwazalem zbudowanie w CI natywnego
   linuksowego pliku wykonywalnego (ELF) GUI przez PyInstaller, zeby dalo sie go
   odpalic na Linuksie bez wine. Problem: bundle pywebview + WebKitGTK w trybie
   `--onefile` wyszedl **~435 MB** i potrafil cicho wisiec (webkit odpala podprocesy,
   ktore w rozpakowanym onefile nie zawsze startuja). To nie byla droga do utrzymania
   w pipeline.

3. **Finalna decyzja: przepisanie GUI na PySide6 (Qt).** PySide6 pakuje sie w pelni do
   samodzielnego `.exe` (Windows) oraz natywnego ELF-a (Linux), nie potrzebuje WebView2
   ani WebKita, a build jest znacznie lzejszy. Styl interfejsu (ciemny motyw) realizowany
   przez QSS — arkusz stylow Qt o skladni zblizonej do CSS. (Zakladalem, ze `.exe` ruszy
   tez pod wine — patrz pkt 4, gdzie sie to nie potwierdzilo.)

4. **Testowanie pod wine sie nie powiodlo -> natywny ELF w pipeline.** Lokalnie (Linux)
   `.exe` GUI nie chcial ruszyc pod wine (kolejno: `init_sys_streams`, a po przejsciu na
   build z konsola i doinstalowaniu runtime VC++ — `DLL load failed importing QtCore`;
   wine 9.0 okazal sie za stary na Qt 6.11). Dlatego zbudowalem **natywna binarke Linux
   (ELF, PySide6, ~65 MB, bez wine)**, ktora uruchamia GUI wprost na Linuksie, i dolaczylem
   jej build do pipeline (job `build-linux`, artefakt `konwerter-linux`).

Zbudowane wczesniej pliki `.exe` (wersja pywebview) zostaly zachowane w katalogu
[`exe_ciekawostki/`](exe_ciekawostki/) jako pamiatka tej iteracji.

**Test na Windowsie:** obie wersje GUI — `.exe` z pywebview oraz `.exe` z PySide6 —
zostaly przetestowane na komputerze z Windowsem kolegi ze studiow i uruchamiaja sie
poprawnie. Opisane wyzej problemy dotyczyly **wylacznie uruchamiania pod wine na
Linuksie**, a nie samego Windowsa (gdzie obie wersje dzialaja).

## Konwencja branchy

Kazdy task na osobnej galezi: `Task0`, `Task1`, ... `Task9` — scalane do `master`.
