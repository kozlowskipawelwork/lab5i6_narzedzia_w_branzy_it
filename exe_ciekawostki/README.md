# Ciekawostki — zbudowane pliki .exe (wersja pywebview)

Artefakty zbudowane przez GitHub Actions (runner Windows) we wczesniejszej iteracji
projektu, w ktorej GUI bylo oparte na **pywebview**:

- `konwerter.exe`     — wersja konsolowa (CLI). Dziala na Windows oraz pod wine.
- `konwerter-gui.exe` — wersja z GUI (pywebview). Dziala na Windows; pod wine NIE,
                        bo pywebview wymaga Edge WebView2 (w wine go brak).

Zostawione jako ciekawostka / pamiatka iteracji. Finalne GUI projektu jest oparte na
PySide6 (patrz README w glownym katalogu, sekcja "Historia / decyzje projektowe").
