"""Opaque rounded window shared by all editors."""
from __future__ import annotations

import sys

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizeGrip, QVBoxLayout,
                               QWidget)

from .. import glass
from ..identity import APP_NAME
from .surfaces import paint_surface
from . import theme

IS_WIN = sys.platform == "win32"


class StudioWindow(QWidget):
    """Solid top-level window. Put content in `self.body`."""

    def __init__(self, title: str, parent=None, size=(760, 640)):
        super().__init__(parent)
        from PySide6.QtWidgets import QApplication
        from ..i18n import install_portuguese
        install_portuguese(QApplication.instance())
        self.setWindowTitle(f"{title} — {APP_NAME}")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setObjectName("glassRoot")
        self.setStyleSheet(glass.QSS)
        self.resize(*size)
        self._drag: QPoint | None = None
        self.radius = 18

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 8, 14, 12)
        outer.setSpacing(8)

        bar = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("title")
        bar.addWidget(self.title_label)
        bar.addStretch(1)
        close = QPushButton("✕")
        close.setObjectName("chrome")
        close.setToolTip("Fechar (Esc)")
        close.clicked.connect(self.close)
        bar.addWidget(close)
        outer.addLayout(bar)

        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        outer.addLayout(self.body, 1)

        grip_row = QHBoxLayout()
        grip_row.addStretch(1)
        grip = QSizeGrip(self)
        grip.setFixedSize(14, 14)
        grip_row.addWidget(grip)
        grip_row.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(grip_row)

    # ---- window behaviour
    def present(self):
        """Centre on the cursor's screen, then show."""
        from PySide6.QtGui import QCursor, QGuiApplication
        scr = (QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()).availableGeometry()
        self.resize(min(self.width(), scr.width() - 40), min(self.height(), scr.height() - 40))
        self.move(scr.center() - self.rect().center())
        self._placed = True
        self.show()
        if sys.platform == "darwin":
            from .. import platform_mac
            platform_mac.activate()   # menu-bar apps aren't brought forward automatically
        self.raise_()
        self.activateWindow()

    def showEvent(self, e):
        super().showEvent(e)
        if not getattr(self, "_placed", False):
            scr = self.screen().availableGeometry()
            self.move(scr.center() - self.rect().center())
            self._placed = True

    def moveEvent(self, e):
        super().moveEvent(e)
        self._stale()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        glass.apply_shape(self, glass.rounded_rect_path(QRectF(self.rect()), self.radius))
        self._stale()

    def _stale(self):
        self.update()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.position().y() < 40:
            handle = self.windowHandle()
            if handle is not None and handle.startSystemMove():
                return  # native move: snapping etc.
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = glass.rounded_rect_path(r, self.radius)
        paint_surface(p, path, theme.BACKGROUND)
