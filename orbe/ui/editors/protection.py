"""Orbe image and document editor. See LICENSE for notices."""
from __future__ import annotations
from ...i18n import translate

from typing import Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QCheckBox, QGridLayout, QLabel, QLineEdit

from ... import imaging

Notify = Callable[..., None]

from .common import ToolWindow

class ProtectWindow(ToolWindow):
    tool_name = "Protect"

    def __init__(self, path, notify):
        super().__init__("Proteger PDF", path, notify, size=(520, 330))
        g = QGridLayout()
        self.pw = QLineEdit()
        self.pw2 = QLineEdit()
        for e in (self.pw, self.pw2):
            e.setEchoMode(QLineEdit.Password)
        g.addWidget(QLabel(translate("Password")), 0, 0)
        g.addWidget(self.pw, 0, 1)
        g.addWidget(QLabel(translate("Confirm")), 1, 0)
        g.addWidget(self.pw2, 1, 1)
        show = QCheckBox(translate("Show"))
        show.toggled.connect(lambda on: [e.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password)
                                         for e in (self.pw, self.pw2)])
        g.addWidget(show, 0, 2)
        self.body.addLayout(g)
        self.msg = QLabel(translate("AES-256 encryption. Anyone opening the PDF will need this password."))
        self.msg.setObjectName("dim")
        self.msg.setWordWrap(True)
        self.body.addWidget(self.msg)
        self.body.addStretch(1)
        self.body.addLayout(self.footer("Protect", self.save))
        self.pw.textChanged.connect(self._check)
        self.pw2.textChanged.connect(self._check)
        self._check()
        QTimer.singleShot(0, self.pw.setFocus)

    def _check(self):
        a, b = self.pw.text(), self.pw2.text()
        ok = len(a) >= 4 and a == b
        self.primary_btn.setEnabled(ok)
        if a and len(a) < 4:
            self.msg.setText(translate("Use at least 4 characters."))
        elif b and a != b:
            self.msg.setText(translate("Passwords don't match yet."))
        elif ok:
            strength = "forte" if len(a) >= 12 else "razoável" if len(a) >= 8 else "fraca"
            self.msg.setText(translate(f"Tudo certo · senha {strength}"))
        else:
            self.msg.setText(translate("AES-256 encryption. Anyone opening the PDF will need this password."))

    def save(self):
        pw, path = self.pw.text(), self.path
        self.run(lambda: [imaging.protect_pdf(path, pw)], "Criptografando…")
