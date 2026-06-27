"""Rdzen konwersji danych miedzy formatami JSON / YAML / XML.

Dane sa trzymane jako zwykly obiekt Pythona (dict / list / wartosci proste).
Kazdy format ma:
  - funkcje wczytujaca (tekst -> obiekt) z WALIDACJA skladni  (Task2/4/6),
  - funkcje zapisujaca (obiekt -> tekst w danym formacie)      (Task3/5/7).

Na tym etapie (Task1) gotowy jest szkielet i wspolne API; konkretne formaty
sa zaslepkami i zostana wypelnione w kolejnych taskach.
"""

from __future__ import annotations

import json
import os
from typing import Any

import yaml
import xmltodict

# Obslugiwane formaty (yaml = alias yml).
SUPPORTED = ("json", "yml", "yaml", "xml")


class ConversionError(Exception):
    """Blad konwersji w postaci czytelnej dla uzytkownika."""


# --------------------------------------------------------------------------- #
#  Rozpoznawanie formatu po rozszerzeniu pliku                                 #
# --------------------------------------------------------------------------- #
def detect_format(path: str) -> str:
    """Zwraca kanoniczny format ('json' | 'yml' | 'xml') na podstawie sciezki."""
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext == "yaml":
        ext = "yml"
    if ext not in ("json", "yml", "xml"):
        raise ConversionError(
            f"Nieobslugiwane rozszerzenie '.{ext or '?'}' w pliku: {path}\n"
            f"Dozwolone formaty: .json  .yml/.yaml  .xml"
        )
    return ext


# --------------------------------------------------------------------------- #
#  Implementacje per format — zaslepki (wypelniane w Task2-7)                  #
# --------------------------------------------------------------------------- #
def _load_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ConversionError(f"Niepoprawny JSON (linia {e.lineno}, kol. {e.colno}): {e.msg}") from e


def _dump_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def _load_yaml(text: str) -> Any:
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ConversionError(f"Niepoprawny YAML: {e}") from e


def _dump_yaml(obj: Any) -> str:
    return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, default_flow_style=False)


def _load_xml(text: str) -> Any:
    try:
        return xmltodict.parse(text)
    except Exception as e:  # xmltodict opakowuje rozne bledy parsera SAX
        raise ConversionError(f"Niepoprawny XML: {e}") from e


def _dump_xml(obj: Any) -> str:
    # xmltodict.unparse wymaga slownika z DOKLADNIE jednym korzeniem.
    # Dane z JSON/YAML czesto go nie maja (lista lub kilka kluczy) -> owijamy.
    if not (isinstance(obj, dict) and len(obj) == 1):
        obj = {"root": obj}
    try:
        return xmltodict.unparse(obj, pretty=True, full_document=True)
    except Exception as e:
        raise ConversionError(
            f"Nie mozna zapisac danych jako XML: {e}\n"
            f"(np. wartosci None/puste klucze nie mapuja sie na XML)"
        ) from e


# --------------------------------------------------------------------------- #
#  Wspolne API: rejestr formatow + funkcje tekst/plik                          #
# --------------------------------------------------------------------------- #
_LOADERS = {"json": _load_json, "yml": _load_yaml, "xml": _load_xml}
_DUMPERS = {"json": _dump_json, "yml": _dump_yaml, "xml": _dump_xml}


def _canon_fmt(fmt: str) -> str:
    """Sprowadza nazwe formatu do 'json' | 'yml' | 'xml' (yaml -> yml)."""
    f = (fmt or "").lower().lstrip(".")
    if f == "yaml":
        f = "yml"
    if f not in _LOADERS:
        raise ConversionError(f"Nieobslugiwany format: '{fmt}'. Dozwolone: json, yml/yaml, xml")
    return f


def loads(text: str, fmt: str) -> Any:
    """Tekst -> obiekt wg formatu, z walidacja skladni."""
    return _LOADERS[_canon_fmt(fmt)](text)


def dumps(obj: Any, fmt: str) -> str:
    """Obiekt -> tekst w podanym formacie."""
    return _DUMPERS[_canon_fmt(fmt)](obj)


def load_file(path: str) -> Any:
    """Wczytuje plik do obiektu Pythona, walidujac skladnie wg formatu."""
    fmt = detect_format(path)
    if not os.path.isfile(path):
        raise ConversionError(f"Plik wejsciowy nie istnieje: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        raise ConversionError(f"Nie mozna odczytac pliku '{path}': {e}") from e
    return _LOADERS[fmt](text)


def dump_to_file(obj: Any, path: str) -> None:
    """Zapisuje obiekt do pliku w formacie wynikajacym z rozszerzenia."""
    fmt = detect_format(path)
    text = _DUMPERS[fmt](obj)
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(parent):
        raise ConversionError(f"Katalog docelowy nie istnieje: {parent}")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    except OSError as e:
        raise ConversionError(f"Nie mozna zapisac pliku '{path}': {e}") from e


def convert(src: str, dst: str) -> Any:
    """Pelna konwersja: wczytuje src, zapisuje dst w nowym formacie."""
    obj = load_file(src)
    dump_to_file(obj, dst)
    return obj
