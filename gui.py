#!/usr/bin/env python3
"""Konwerter danych — wersja z GUI (Task8/9), oparta na pywebview.

UI to samodzielny HTML/CSS w  web/index.html  (motyw "Nocturne").
WAZNE: cala konwersja i zapis na dysk dzieja sie po stronie PYTHONA
(converter/core.py) — JavaScript tylko rysuje interfejs i wola mostek:

    window.pywebview.api.pick_open()                         -> sciezka pliku
    window.pywebview.api.read_source(path)                   -> {name,dir,format,text,valid,...}
    window.pywebview.api.validate(text, fmt)                 -> {ok, error?}
    window.pywebview.api.convert(text, srcFmt, dstFmt, dir, name) -> {ok, output, out_path, log[]}

Task9 (async/wielowatkowo): wlasciwa konwersja + zapis pliku leca w osobnym
watku roboczym (threading.Thread), a wywolania API i tak sa dispatchowane przez
pywebview poza watkiem renderujacym UI, wiec okno sie nie zacina.

Budowanie .exe (bez okna konsoli):
    pyinstaller --onefile --noconsole --add-data "web;web" gui.py
(na Linux/macOS separator w --add-data to ":", czyli  "web:web")
"""

from __future__ import annotations

import datetime
import os
import sys
import threading

import webview  # pywebview

from converter.core import loads, dumps, detect_format, ConversionError


def _resource_dir() -> str:
    """Katalog z plikami UI — dziala tak samo w trybie pyinstaller --onefile."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "web")


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def _blen(text: str) -> int:
    return len((text or "").encode("utf-8"))


class Api:
    """Metody wolane z JavaScriptu jako window.pywebview.api.<nazwa>()."""

    def __init__(self) -> None:
        self._window: "webview.Window | None" = None

    def bind(self, window: "webview.Window") -> None:
        self._window = window

    # --- natywne okno wyboru pliku --------------------------------------- #
    def pick_open(self) -> str:
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Dane (*.json;*.yml;*.yaml;*.xml)", "Wszystkie pliki (*.*)"),
        )
        return result[0] if result else ""

    # --- wczytanie pliku zrodlowego (czytanie po stronie Pythona) -------- #
    def read_source(self, path: str) -> dict:
        path = (path or "").strip()
        if not path:
            return {"ok": False, "error": "Nie podano sciezki pliku."}
        try:
            fmt = detect_format(path)
        except ConversionError as e:
            return {"ok": False, "error": str(e)}
        if not os.path.isfile(path):
            return {"ok": False, "error": f"Plik nie istnieje: {path}"}
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            return {"ok": False, "error": f"Nie mozna odczytac pliku: {e}"}

        valid, err = True, ""
        try:
            loads(text, fmt)  # walidacja skladni (Task2/4/6)
        except ConversionError as e:
            valid, err = False, str(e)

        return {
            "ok": True,
            "name": os.path.basename(path),
            "dir": os.path.dirname(os.path.abspath(path)),
            "format": fmt,
            "text": text,
            "size": _blen(text),
            "valid": valid,
            "error": err,
        }

    # --- szybka walidacja edytowanego tekstu ----------------------------- #
    def validate(self, text: str, fmt: str) -> dict:
        try:
            loads(text or "", fmt)
            return {"ok": True}
        except ConversionError as e:
            return {"ok": False, "error": str(e)}
        except Exception as e:  # zabezpieczenie
            return {"ok": False, "error": str(e)}

    # --- wlasciwa konwersja (Task2-7) w osobnym watku (Task9) ------------ #
    def convert(self, text: str, src_fmt: str, dst_fmt: str, out_dir: str, out_name: str) -> dict:
        result: dict = {}

        def worker() -> None:
            log: list[dict] = []

            def add(msg: str) -> None:
                log.append({"time": _ts(), "text": msg})

            try:
                if not (text or "").strip():
                    raise ConversionError("Brak danych zrodlowych.")
                add(f"read · bufor [{src_fmt}] ({_blen(text)} B)")
                obj = loads(text, src_fmt)            # parse + walidacja (Task2/4/6)
                add(f"validate · skladnia {src_fmt} OK")
                add(f"serialize · obiekt → {dst_fmt}")
                output = dumps(obj, dst_fmt)          # zapis z obiektu (Task3/5/7)

                target_dir = out_dir if out_dir and os.path.isdir(out_dir) else os.getcwd()
                ext = "yml" if dst_fmt in ("yaml", "yml") else dst_fmt
                name = (out_name or f"output.{ext}").strip()
                out_path = os.path.join(target_dir, name)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(output)
                add(f"write · {out_path} ({_blen(output)} B)")
                add(f"COMPLETE · {src_fmt} → {dst_fmt}")
                result.update(ok=True, output=output, out_path=out_path, log=log)
            except ConversionError as e:
                add("error · " + str(e))
                result.update(ok=False, error=str(e), log=log)
            except Exception as e:  # zabezpieczenie przed nieprzewidzianym
                add("error · " + str(e))
                result.update(ok=False, error=f"Nieoczekiwany blad: {e}", log=log)

        worker_thread = threading.Thread(target=worker, name="convert-worker", daemon=True)
        worker_thread.start()
        worker_thread.join()
        return result


def main() -> None:
    api = Api()
    index_html = os.path.join(_resource_dir(), "index.html")
    window = webview.create_window(
        "Konwerter danych — JSON / YAML / XML",
        url=index_html,
        js_api=api,
        width=1180,
        height=900,
        min_size=(900, 720),
        background_color="#08080a",
    )
    api.bind(window)
    webview.start()


if __name__ == "__main__":
    main()
