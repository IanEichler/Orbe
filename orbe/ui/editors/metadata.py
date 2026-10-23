"""Orbe image and document editor. See LICENSE for notices."""
from __future__ import annotations
from ...i18n import translate

from typing import Callable

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFrame, QGridLayout, QHeaderView, QLabel, QPushButton, QTableWidget, QTableWidgetItem

from ... import imaging

Notify = Callable[..., None]

from .common import ToolWindow

class MetadataWindow(ToolWindow):
    tool_name = "Metadata"

    def __init__(self, path, notify, is_pdf: bool = False):
        super().__init__("Metadados", path, notify, size=(640, 380))
        self.is_pdf = is_pdf
        info = imaging.read_pdf_metadata(path) if is_pdf else imaging.read_image_metadata(path)
        summary = {} if is_pdf else imaging.metadata_summary(path)
        self.n_fields, self.has_gps = (len(info), False) if is_pdf else imaging.count_metadata(path)

        card = QFrame()
        card.setObjectName("card")
        cl = QGridLayout(card)
        cl.setContentsMargins(14, 12, 14, 12)
        cl.setHorizontalSpacing(16)
        rows = summary or {k: v for k, v in info.items() if k in ("title", "author", "creator", "producer", "Pages")}
        if not rows:
            rows = {"": "Nenhum metadado pessoal encontrado."}
        for i, (k, v) in enumerate(rows.items()):
            kl = QLabel(translate(k))
            kl.setObjectName("dim")
            cl.addWidget(kl, i, 0)
            vl = QLabel(v)
            vl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            cl.addWidget(vl, i, 1)
            if k == "Location":
                vl.setObjectName("warn")
                mb = QPushButton(translate("Open map"))
                lat, lon = v.split(", ")
                mb.clicked.connect(lambda _=False, a=lat, b=lon: QDesktopServices.openUrl(
                    QUrl(f"https://www.openstreetmap.org/?mlat={a}&mlon={b}#map=15/{a}/{b}")))
                cl.addWidget(mb, i, 2)
        self.body.addWidget(card)
        if self.has_gps:
            warn = QLabel(translate("⚠  This photo reveals where it was taken."))
            warn.setObjectName("warn")
            self.body.addWidget(warn)

        self.toggle = QPushButton(translate(f"Mostrar todos os campos ({self.n_fields})"))
        self.toggle.setCheckable(True)
        self.body.addWidget(self.toggle, 0, Qt.AlignLeft)
        t = QTableWidget(len(info), 2)
        t.setHorizontalHeaderLabels(["Campo", "Valor"])
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t.horizontalHeader().setStretchLastSection(True)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        for r, (k, v) in enumerate(info.items()):
            t.setItem(r, 0, QTableWidgetItem(translate(k)))
            t.setItem(r, 1, QTableWidgetItem(v))
        t.setVisible(False)

        def show_all(on):
            t.setVisible(on)
            self.resize(self.width(), 640 if on else 380)
        self.toggle.toggled.connect(show_all)
        self.body.addWidget(t, 1)
        self.body.addStretch(0)

        extra = []
        if self.has_gps:
            loc = QPushButton(translate("Remove location only"))
            loc.clicked.connect(self.strip_location)
            extra.append(loc)
        self.body.addLayout(self.footer("Remove all metadata", self.strip, None, extra))

    def strip(self):
        path, is_pdf = self.path, self.is_pdf
        detail = f"{self.n_fields} campo{'s' if self.n_fields != 1 else ''} removido{'s' if self.n_fields != 1 else ''}" + (" incluindo a localização GPS" if self.has_gps else "")

        def work():
            return [imaging.strip_pdf_metadata(path) if is_pdf else imaging.strip_image_metadata(path)]
        self.run(work, "Removendo metadados…", detail)

    def strip_location(self):
        path = self.path
        self.run(lambda: [imaging.strip_location(path)], "Removendo localização…", "GPS removido; dados da câmera preservados")


# ================================================================ COMPRESS
