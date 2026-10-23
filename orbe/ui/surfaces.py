"""Opaque application surfaces with the existing rounded shapes and palette."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen
from . import theme


def paint_surface(painter, path, color=None):
    painter.save()
    painter.fillPath(path, QColor(color or theme.SURFACE))
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(QColor(theme.BORDER), 1.2))
    painter.drawPath(path)
    painter.restore()
