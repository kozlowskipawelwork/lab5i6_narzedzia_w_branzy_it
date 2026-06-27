#!/usr/bin/env python3
"""Konwerter danych JSON / YAML / XML — wersja konsolowa (CLI).

Sposob uzycia (zgodnie z PDF):
    program.exe pathFile1.x pathFile2.y
gdzie x, y to jeden z formatow: .json .yml/.yaml .xml

Plik .exe budowany jest komenda:
    pyinstaller --onefile project.py

Task1 = parsowanie argumentow uruchomienia (ponizej, argparse).
"""

from __future__ import annotations

import argparse
import sys

from converter.core import convert, ConversionError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="program",
        description="Konwerter danych miedzy formatami JSON / YAML / XML.",
        epilog="Przyklad:  program.exe dane.json dane.yml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="plik wejsciowy  (.json | .yml/.yaml | .xml)")
    parser.add_argument("output", help="plik wyjsciowy (.json | .yml/.yaml | .xml)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        convert(args.input, args.output)
    except ConversionError as e:
        print(f"BLAD: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Przerwano.", file=sys.stderr)
        return 130
    print(f"OK: {args.input} -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
