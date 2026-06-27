# Task0 — installResources.ps1
# ----------------------------------------------------------------------------
# Skrypt instalujacy WSZYSTKIE komponenty Pythona potrzebne do zbudowania
# projektu. Zasada: KAZDA instalacja przez pip uzyta w projekcie ma tu swoja
# linijke. Ten sam skrypt uruchamia GitHub Actions przed zbudowaniem .exe
# (Task: automatyczne budowanie).
#
# Uruchomienie (PowerShell, domyslny shell runnera windows):
#     ./installResources.ps1
# ----------------------------------------------------------------------------

Write-Host ">> Aktualizacja pip..."
python -m pip install --upgrade pip

Write-Host ">> Instalacja zaleznosci projektu..."
python -m pip install pyyaml        # YAML  (Task4/5)
python -m pip install xmltodict     # XML   (Task6/7)
python -m pip install pywebview     # GUI HTML/CSS (Task8/9)
python -m pip install pyinstaller   # budowanie .exe

Write-Host ">> Gotowe. Zainstalowane pakiety:"
python -m pip list
