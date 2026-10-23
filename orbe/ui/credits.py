"""Orbe product information with access to the bundled license notices."""
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel, QPushButton, QHBoxLayout
from ..application.icons import make_icon
from ..identity import APP_NAME, VERSION, attribution
from .shell import StudioWindow


class CreditsWindow(StudioWindow):
    def __init__(self):
        super().__init__("Sobre o Orbe", size=(480, 340))
        heading = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(make_icon().pixmap(72, 72))
        heading.addWidget(logo)
        title = QLabel(f"{APP_NAME} {VERSION}")
        title.setObjectName("brand")
        heading.addWidget(title, 1)
        self.body.addLayout(heading)
        text = QLabel(attribution())
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.body.addWidget(text)
        self.body.addStretch()
        row = QHBoxLayout()
        license_button = QPushButton("Ver licença")
        root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
        license_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(root / "LICENSE"))))
        row.addWidget(license_button)
        row.addStretch()
        close = QPushButton("Fechar")
        close.clicked.connect(self.close)
        row.addWidget(close)
        self.body.addLayout(row)
