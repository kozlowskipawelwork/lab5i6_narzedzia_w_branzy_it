"""Pakiet konwertera danych JSON / YAML / XML."""

from .core import (
    convert,
    load_file,
    dump_to_file,
    loads,
    dumps,
    detect_format,
    ConversionError,
    SUPPORTED,
)

__all__ = [
    "convert",
    "load_file",
    "dump_to_file",
    "loads",
    "dumps",
    "detect_format",
    "ConversionError",
    "SUPPORTED",
]
