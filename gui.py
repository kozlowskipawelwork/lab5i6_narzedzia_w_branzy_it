#!/usr/bin/env python3
"""Konwerter danych — GUI w PySide6 (Qt). Task8 / Task9.

Dlaczego PySide6, a nie pywebview: pywebview na Windows wymaga Edge WebView2,
przez co zbudowany `.exe` GUI nie uruchamia sie pod wine. Qt pakuje sie w pelni
do samodzielnego `.exe` / ELF-a i dziala pod wine oraz na Linuksie, bez WebView2.

Cala konwersja i zapis pliku po stronie rdzenia (converter/core.py). Konwersja
biegnie w osobnym watku (QThread) — Task9 (async, nie blokuje UI).
Styl interfejsu: QSS (arkusz stylow Qt, skladnia zblizona do CSS) — motyw "Nocturne".

Budowanie .exe (bez okna konsoli):
    pyinstaller --onefile --noconsole --name konwerter-gui gui.py
"""

from __future__ import annotations

import datetime
import os
import sys

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QComboBox, QLineEdit,
    QPlainTextEdit, QFileDialog, QVBoxLayout, QHBoxLayout, QButtonGroup,
)

from converter.core import loads, dumps, detect_format, ConversionError


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


QSS = """
QWidget { background: #08080a; color: #e9e5db; font-family: 'JetBrains Mono','Cascadia Code',Consolas,monospace; font-size: 13px; }
QLabel#title { font-family: Georgia,'Times New Roman',serif; font-size: 30px; font-weight: 700; letter-spacing: 2px; }
QLabel#kicker { color: #b6403d; font-size: 11px; letter-spacing: 4px; }
QLabel#section { font-family: Georgia,serif; font-size: 13px; letter-spacing: 3px; color: #e9e5db; }
QLabel#hint { color: #8b887f; font-size: 11px; letter-spacing: 2px; }
QLabel#ok { color: #a6e3a1; }
QLabel#bad { color: #f38ba8; }
QPlainTextEdit, QLineEdit, QComboBox {
    background: #0c0c0e; border: 1px solid #24242a; border-radius: 6px;
    padding: 6px; color: #e9e5db; selection-background-color: #7a2424;
}
QPlainTextEdit:focus, QLineEdit:focus { border-color: #b6403d; }
QPushButton {
    background: #101013; border: 1px solid #3a3a42; border-radius: 6px;
    padding: 7px 14px; color: #cdd6f4;
}
QPushButton:hover { border-color: #b6403d; color: #f3efe6; }
QPushButton#fmt:checked { background: #b6403d; color: #08080a; border: none; font-weight: 700; }
QPushButton#convert {
    background: #b6403d; color: #08080a; border: none; border-radius: 8px;
    padding: 13px; font-family: Georgia,serif; font-size: 15px; font-weight: 700; letter-spacing: 2px;
}
QPushButton#convert:hover { background: #d65450; }
QPushButton#convert:disabled { background: #3a3a42; color: #8b887f; }
QPlainTextEdit#console { color: #9399b2; }
"""


class ConvertWorker(QThread):
    """Task9 — konwersja + zapis pliku w osobnym watku, zeby nie blokowac UI."""

    done = Signal(dict)

    def __init__(self, text: str, src_fmt: str, dst_fmt: str, out_dir: str, out_name: str):
        super().__init__()
        self._a = (text, src_fmt, dst_fmt, out_dir, out_name)

    def run(self) -> None:
        text, src_fmt, dst_fmt, out_dir, out_name = self._a
        log: list[str] = []

        def add(m: str) -> None:
            log.append(f"{_ts()}  {m}")

        try:
            if not text.strip():
                raise ConversionError("Brak danych zrodlowych.")
            add(f"read · bufor [{src_fmt}]")
            obj = loads(text, src_fmt)                 # parse + walidacja (Task2/4/6)
            add(f"validate · skladnia {src_fmt} OK")
            add(f"serialize · obiekt -> {dst_fmt}")
            output = dumps(obj, dst_fmt)               # zapis z obiektu (Task3/5/7)

            target_dir = out_dir if out_dir and os.path.isdir(out_dir) else os.getcwd()
            ext = "yml" if dst_fmt in ("yaml", "yml") else dst_fmt
            name = (out_name or f"output.{ext}").strip()
            out_path = os.path.join(target_dir, name)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(output)
            add(f"write · {out_path}")
            add(f"COMPLETE · {src_fmt} -> {dst_fmt}")
            self.done.emit({"ok": True, "output": output, "out_path": out_path, "log": log})
        except ConversionError as e:
            add("error · " + str(e))
            self.done.emit({"ok": False, "error": str(e), "log": log})
        except Exception as e:  # zabezpieczenie przed nieprzewidzianym bledem
            add("error · " + str(e))
            self.done.emit({"ok": False, "error": f"Nieoczekiwany blad: {e}", "log": log})


class MainWindow(QWidget):
    FORMATS = ["json", "yaml", "xml"]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Konwerter danych — JSON / YAML / XML")
        self.resize(1000, 780)
        self.src_dir = ""
        self.src_name = ""
        self._worker: ConvertWorker | None = None
        self._build_ui()
        self._val_timer = QTimer(self)
        self._val_timer.setSingleShot(True)
        self._val_timer.timeout.connect(self._validate_now)

    # ----- budowa interfejsu ----- #
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(12)

        kicker = QLabel("† NOCTURNE // STRUCTURED DATA")
        kicker.setObjectName("kicker")
        title = QLabel("DATA CONVERTER")
        title.setObjectName("title")
        root.addWidget(kicker)
        root.addWidget(title)

        # --- SOURCE ---
        srow = QHBoxLayout()
        s_lbl = QLabel("01 — SOURCE"); s_lbl.setObjectName("section")
        self.src_fmt = QComboBox(); self.src_fmt.addItems([f.upper() for f in self.FORMATS])
        self.src_fmt.currentIndexChanged.connect(lambda *_: self._schedule_validate())
        btn_browse = QPushButton("Wczytaj…"); btn_browse.clicked.connect(self.browse)
        btn_clear = QPushButton("Wyczyść"); btn_clear.clicked.connect(self.clear_source)
        srow.addWidget(s_lbl); srow.addStretch(1)
        srow.addWidget(QLabel("format:")); srow.addWidget(self.src_fmt)
        srow.addWidget(btn_browse); srow.addWidget(btn_clear)
        root.addLayout(srow)

        self.source = QPlainTextEdit()
        self.source.setPlaceholderText("// wczytaj plik (Wczytaj…) albo wklej surowe dane")
        self.source.textChanged.connect(self._schedule_validate)
        root.addWidget(self.source, 3)

        self.valid_lbl = QLabel("EMPTY BUFFER"); self.valid_lbl.setObjectName("hint")
        root.addWidget(self.valid_lbl)

        # --- TARGET ---
        trow = QHBoxLayout()
        t_lbl = QLabel("02 — TARGET"); t_lbl.setObjectName("section")
        trow.addWidget(t_lbl); trow.addStretch(1)
        trow.addWidget(QLabel("→ format:"))
        self.fmt_group = QButtonGroup(self)
        for f in self.FORMATS:
            b = QPushButton(f.upper()); b.setObjectName("fmt"); b.setCheckable(True)
            b.clicked.connect(lambda _=False, fmt=f: self.set_target(fmt))
            self.fmt_group.addButton(b)
            trow.addWidget(b)
            if f == "yaml":
                b.setChecked(True)
        self.target_fmt = "yaml"
        root.addLayout(trow)

        frow = QHBoxLayout()
        frow.addWidget(QLabel("plik wyj.:"))
        self.target_name = QLineEdit("output.yaml")
        frow.addWidget(self.target_name)
        root.addLayout(frow)

        self.output = QPlainTextEdit(); self.output.setReadOnly(True)
        self.output.setPlaceholderText("AWAITING CONVERSION")
        root.addWidget(self.output, 3)

        # --- CONVERT ---
        self.btn_convert = QPushButton("CONVERT †"); self.btn_convert.setObjectName("convert")
        self.btn_convert.clicked.connect(self.convert)
        root.addWidget(self.btn_convert)

        # --- CONSOLE ---
        clbl = QLabel("▸ CONSOLE"); clbl.setObjectName("hint")
        root.addWidget(clbl)
        self.console = QPlainTextEdit(); self.console.setObjectName("console")
        self.console.setReadOnly(True); self.console.setFixedHeight(130)
        self.console.setPlaceholderText("$ idle — awaiting instruction…")
        root.addWidget(self.console)

    # ----- pomocnicze ----- #
    def _src_fmt(self) -> str:
        return self.FORMATS[self.src_fmt.currentIndex()]

    def _base(self, name: str) -> str:
        i = name.rfind(".")
        return name[:i] if i > 0 else (name or "output")

    def _ext(self, fmt: str) -> str:
        return "yaml" if fmt == "yaml" else fmt

    def log(self, line: str) -> None:
        self.console.appendPlainText(line)

    # ----- akcje ----- #
    def browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik", "", "Dane (*.json *.yml *.yaml *.xml);;Wszystkie pliki (*)"
        )
        if not path:
            return
        try:
            fmt = detect_format(path)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except (ConversionError, OSError) as e:
            self.log(f"{_ts()}  error · {e}")
            return
        self.src_dir = os.path.dirname(os.path.abspath(path))
        self.src_name = os.path.basename(path)
        self.src_fmt.setCurrentIndex(self.FORMATS.index("yaml" if fmt == "yml" else fmt))
        self.source.setPlainText(text)
        self.target_name.setText(self._base(self.src_name) + "." + self._ext(self.target_fmt))
        self.log(f"{_ts()}  load · {self.src_name} ({len(text.encode('utf-8'))} B)")

    def set_target(self, fmt: str) -> None:
        self.target_fmt = fmt
        self.target_name.setText(self._base(self.src_name or "output") + "." + self._ext(fmt))

    def clear_source(self) -> None:
        self.src_dir = ""; self.src_name = ""
        self.source.clear(); self.output.clear()
        self.valid_lbl.setObjectName("hint"); self.valid_lbl.setText("EMPTY BUFFER")
        self._restyle(self.valid_lbl)

    def _schedule_validate(self) -> None:
        self._val_timer.start(350)

    def _validate_now(self) -> None:
        text = self.source.toPlainText()
        if not text.strip():
            self.valid_lbl.setObjectName("hint"); self.valid_lbl.setText("EMPTY BUFFER")
            self._restyle(self.valid_lbl); return
        try:
            loads(text, self._src_fmt())
            self.valid_lbl.setObjectName("ok")
            self.valid_lbl.setText(f"SYNTAX VALID · {self._src_fmt().upper()}")
        except ConversionError as e:
            self.valid_lbl.setObjectName("bad")
            msg = str(e).splitlines()[0]
            self.valid_lbl.setText("INVALID · " + (msg[:60] + "…" if len(msg) > 60 else msg))
        self._restyle(self.valid_lbl)

    def _restyle(self, w) -> None:
        w.style().unpolish(w); w.style().polish(w)

    def convert(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        text = self.source.toPlainText()
        if not text.strip():
            self.log(f"{_ts()}  error · brak danych zrodlowych")
            return
        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("CONVERTING…")
        self.console.clear()
        self._worker = ConvertWorker(
            text, self._src_fmt(), self.target_fmt, self.src_dir, self.target_name.text()
        )
        self._worker.done.connect(self._on_done)
        self._worker.start()

    def _on_done(self, res: dict) -> None:
        for line in res.get("log", []):
            self.log(line)
        if res.get("ok"):
            self.output.setPlainText(res.get("output", ""))
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("CONVERT †")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
