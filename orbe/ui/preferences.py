"""Preferences screen, separate from persistence and operating-system integration."""
import sys
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QLabel, QPushButton, QSlider
from ..preferences import TRIGGERS, autostart_enabled, set_autostart
from .shell import StudioWindow


class SettingsWindow(StudioWindow):
    changed = Signal()

    def __init__(self, settings):
        super().__init__("Preferências", size=(560, 450))
        self.s = settings
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        choices = (
            ("Tecla do menu", "trigger", TRIGGERS),
            ("Salvar resultados", "output", [("next", "Ao lado do original"), ("folder", "Subpasta Orbe")]),
            ("PDF → imagem", "pdf_dpi", [(150, "150 dpi · compacto"), (200, "200 dpi · equilibrado"), (300, "300 dpi · impressão")]),
        )
        for row, (text, key, options) in enumerate(choices):
            grid.addWidget(QLabel(text), row, 0)
            combo = QComboBox()
            for value, caption in options:
                combo.addItem(caption, value)
            combo.setCurrentIndex(max(0, combo.findData(self.s.get(key))))
            combo.currentIndexChanged.connect(lambda index, c=combo, k=key: self._save(k, c.currentData()))
            grid.addWidget(combo, row, 1)
        grid.addWidget(QLabel("Qualidade JPG / WebP"), 3, 0)
        quality = QSlider(Qt.Horizontal)
        quality.setRange(10, 100)
        quality.setValue(self.s.get("jpg_quality"))
        self.quality_label = QLabel(f"{quality.value()}%")
        quality.valueChanged.connect(lambda value: (self.quality_label.setText(f"{value}%"), self._save("jpg_quality", value)))
        grid.addWidget(quality, 3, 1)
        grid.addWidget(self.quality_label, 3, 2)
        self.body.addLayout(grid)
        self.auto = QCheckBox("Iniciar com o Windows" if sys.platform == "win32" else "Abrir ao iniciar a sessão")
        self.auto.setChecked(autostart_enabled())
        self.auto.toggled.connect(set_autostart)
        self.body.addWidget(self.auto)
        if sys.platform.startswith("linux"):
            from .. import platform_linux
            if platform_linux.is_wayland():
                notice = QLabel("No Wayland, use Abrir com → Orbe. O atalho global precisa de uma sessão X11.")
                notice.setWordWrap(True)
                self.body.addWidget(notice)
        self.body.addStretch()
        done = QPushButton("Concluir")
        done.setObjectName("primary")
        done.clicked.connect(self.close)
        self.body.addWidget(done, alignment=Qt.AlignRight)

    def _save(self, key, value):
        self.s.set(key, value)
        self.changed.emit()
