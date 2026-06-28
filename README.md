# Konwerter danych JSON / YAML / XML

Projekt koncowy z przedmiotu Narzedzia w branzy IT (Lab5 i 6).
Program konwertuje dane miedzy formatami .json, .yml/.yaml i .xml.

## Uzycie (CLI)

```
program.exe pathFile1.x pathFile2.y
```

gdzie x i y to jeden z formatow .json, .yml lub .xml. Program rozpoznaje format po
rozszerzeniu, wczytuje dane z pliku wejsciowego i zapisuje je do pliku wyjsciowego w
nowym formacie.

Przyklad:

```
program.exe dane.json dane.yml
```

## Struktura

```
project.py             CLI, parsowanie argumentow (Task1)
gui.py                 GUI w PySide6 (Task8, Task9)
converter/core.py      wczytywanie/zapis JSON, YAML, XML + walidacja (Task2-7)
web/index.html         interfejs z wczesniejszej iteracji na pywebview (juz nieuzywany)
installResources.ps1   instalacja zaleznosci pip (Task0, uzywany tez w CI)
requirements.txt       lista zaleznosci
.github/workflows/     GitHub Actions, automatyczny build
```

## Uruchomienie lokalne

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# GUI na Linux wymaga jeszcze: sudo apt install libxcb-cursor0

python project.py dane.json dane.yml    # CLI
python gui.py                           # GUI
```

## Budowanie (PyInstaller)

```bash
pyinstaller --onefile --name konwerter project.py     # CLI
pyinstaller --onefile --name konwerter-gui gui.py     # GUI
```

To samo robi GitHub Actions i wystawia dwa artefakty:

* konwerter-windows: pliki .exe (CLI dziala tez pod wine, GUI .exe tylko na Windowsie)
* konwerter-linux: natywne pliki ELF, GUI uruchamia sie wprost na Linuksie (bez wine,
  wymaga tylko systemowego libxcb-cursor0)

Uwaga: przy zapisie do XML wszystkie wartosci staja sie tekstem (np. liczba 1 wroci
jako "1"). To ograniczenie samego formatu XML, nie blad programu.

## Mapowanie taskow

```
Task0   installResources.ps1
Task1   parsowanie argumentow (project.py)
Task2   wczytanie JSON + walidacja (converter/core.py)
Task3   zapis JSON
Task4   wczytanie YAML + walidacja
Task5   zapis YAML
Task6   wczytanie XML + walidacja
Task7   zapis XML
Task8   wersja z GUI (gui.py)
Task9   odczyt i zapis w osobnym watku (gui.py)
```

## Historia GUI

GUI przeszlo kilka iteracji, zanim wyladowalo na PySide6.

1. Najpierw wybralem pywebview (HTML/CSS). To byl blad. Zbudowany .exe GUI nie odpala
   sie pod wine, bo pywebview na Windowsie korzysta z Edge WebView2, ktorego w wine nie
   ma. Przez to nie moglem przetestowac GUI .exe lokalnie na Linuksie.

2. Probowalem zbudowac w CI natywny linuksowy plik ELF z pywebview, zeby dalo sie go
   odpalic bez wine. Wyszlo okolo 435 MB i potrafilo cicho wisiec (webkit odpala
   podprocesy, ktore w rozpakowanym onefile nie zawsze startuja), wiec odpuscilem.

3. Przepisalem GUI na PySide6 (Qt). Pakuje sie w calosci do .exe i do ELF-a, nie
   potrzebuje WebView2 ani webkita, build jest duzo lzejszy. Zakladalem, ze dzieki temu
   .exe ruszy tez pod wine.

4. Pod wine i tak nie ruszylo. Najpierw blad init_sys_streams, a po zmianie na build z
   konsola i doinstalowaniu runtime VC++ pojawilo sie DLL load failed importing QtCore.
   Wine 9.0 jest po prostu za stary na Qt 6.11. Dlatego dla Linuksa buduje natywny ELF
   (PySide6, okolo 65 MB, bez wine), ktory odpala GUI wprost. Build ELF-a jest podpiety
   do pipeline (job build-linux, artefakt konwerter-linux).

Stare pliki .exe z wersji pywebview zostawilem w katalogu exe_ciekawostki jako pamiatke.

Obie wersje GUI (pywebview i PySide6) sprawdzilem na Windowsie kolegi ze studiow.
Uruchamiaja sie poprawnie. Problemy dotyczyly tylko uruchamiania pod wine na Linuksie,
nie samego Windowsa.

## Branche

Kazdy task jest na osobnej galezi (Task0, Task1, ... Task9) scalanej do master.
