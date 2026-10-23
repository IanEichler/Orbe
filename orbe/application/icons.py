"""Shared Orbe branding for application windows and the system tray."""
import sys
from pathlib import Path
from PySide6.QtGui import QIcon


def make_icon() -> QIcon:
    assets = Path(__file__).resolve().parents[1] / "assets"
    path = assets / ("orbe.ico" if sys.platform == "win32" else "orbe.png")
    icon = QIcon(str(path))
    return icon if not icon.isNull() else QIcon(str(assets / "orbe.png"))


def make_tray_icon() -> QIcon:
    return make_icon()
