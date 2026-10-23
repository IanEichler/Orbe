"""Opaque radial menu with rounded sectors and drag/drop handling."""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEasingCurve, QPoint, QPointF, QRectF, Qt, QTimer, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget

from .. import glass
from .surfaces import paint_surface
from . import theme
from ..util import resolve_shortcuts, ui_family


@dataclass
class Item:
    label: str
    glyph: str = ""
    run: Callable[[list[str]], None] | None = None
    key: str = ""
    hint: str = ""


SIZE = 400          # window size (room for shadow + hover pop)
R_OUT = 158         # outer radius of petals
R_IN = 60           # inner radius of petals
R_HUB = 50          # hub radius
GAP_DEG = 3.2
CORNER = 10


def sector_path(c: QPointF, r0: float, r1: float, a0: float, a1: float) -> QPainterPath:
    """Annular sector between angles a0..a1 (degrees, Qt convention: 0 = 3 o'clock, CCW)."""
    return _rounded_sector(c.x(), c.y(), r0, r1, a0, a1)


@lru_cache(maxsize=128)
def _rounded_sector(cx, cy, r0, r1, a0, a1):
    path = QPainterPath()
    outer = QRectF(cx - r1, cy - r1, 2 * r1, 2 * r1)
    inner = QRectF(cx - r0, cy - r0, 2 * r0, 2 * r0)
    corner = min(CORNER, (r1-r0)/3, math.radians(a1-a0)*r0/3)
    outer_delta = math.degrees(corner/r1)
    inner_delta = math.degrees(corner/r0)

    def point(radius, angle):
        radians = math.radians(angle)
        return QPointF(cx+radius*math.cos(radians), cy-radius*math.sin(radians))

    path.moveTo(point(r1, a0+outer_delta))
    path.arcTo(outer, a0+outer_delta, a1-a0-2*outer_delta)
    path.quadTo(point(r1, a1), point(r1-corner, a1))
    path.lineTo(point(r0+corner, a1))
    path.quadTo(point(r0, a1), point(r0, a1-inner_delta))
    path.arcTo(inner, a1-inner_delta, a0-a1+2*inner_delta)
    path.quadTo(point(r0, a0), point(r0+corner, a0))
    path.lineTo(point(r1-corner, a0))
    path.quadTo(point(r1, a0), point(r1, a0+outer_delta))
    path.closeSubpath()
    return path


def angles(n: int, i: int) -> tuple[float, float]:
    span = 360.0 / n
    start = 90 + span / 2 - (i + 1) * span   # first petal centred at 12 o'clock, clockwise
    return start + GAP_DEG / 2, start + span - GAP_DEG / 2


class RadialMenu(QWidget):
    activated = Signal(object, list)     # Item, paths
    dismissed = Signal()

    def __init__(self, build_rings: Callable[[list[str]], dict[str, list[Item]]],
                 describe: Callable[[list[str]], str]):
        super().__init__(None)
        self.build_rings = build_rings
        self.describe = describe
        self.trigger_label, self.trigger_key = "Shift", Qt.Key_Shift
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint |
                            Qt.WindowDoesNotAcceptFocus | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.resize(SIZE, SIZE)

        self.paths: list[str] = []
        self.rings: dict[str, list[Item]] = {}
        self.ring_names: list[str] = []
        self.ring_idx = 0
        self.hover = -1          # petal index, -2 = hub, -1 = none
        self.cursor_pos = QPointF(SIZE / 2, SIZE / 2)
        self.hub_text = ""
        self.got_drag = False
        self.hub_armed = False
        self.click_mode = False  # opened from tray/menu instead of a drag
        self._t = 1.0            # pop-in animation 0..1
        self._swap = 1.0         # ring-swap animation 0..1
        self.spring: list[float] = []   # per-petal hover amount 0..1 (eased every frame)
        self.hub_spring = 0.0

        self.anim = QVariantAnimation(self, startValue=0.0, endValue=1.0, duration=190,
                                      easingCurve=QEasingCurve.OutBack)
        self.anim.valueChanged.connect(self._set_t)
        self.swap_anim = QVariantAnimation(self, startValue=0.0, endValue=1.0, duration=220,
                                           easingCurve=QEasingCurve.OutCubic)
        self.swap_anim.valueChanged.connect(self._set_swap)
        self.hub_timer = QTimer(self, singleShot=True, interval=420, timeout=self.next_ring)
        self.frame = QTimer(self, interval=16, timeout=self._tick)   # 60 fps springs

    def set_trigger(self, name, label):
        self.trigger_label = label
        self.trigger_key = {"shift": Qt.Key_Shift, "ctrl": Qt.Key_Control, "alt": Qt.Key_Alt}.get(name, Qt.Key_Shift)
        self.update()

    # ------------------------------------------------------------ show / hide
    def popup(self, pos: QPoint | None = None, paths: list[str] | None = None):
        pos = pos or QCursor.pos()
        tl = pos - QPoint(SIZE // 2, SIZE // 2)
        scr = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
        g = scr.geometry()
        tl.setX(min(max(tl.x(), g.left()), g.right() - SIZE))
        tl.setY(min(max(tl.y(), g.top()), g.bottom() - SIZE))
        self.move(tl)
        self.hover = -1
        self.got_drag = False
        self.hub_armed = False  # drags start on the hub; don't flip until they leave it
        self.click_mode = paths is not None
        early = []
        if paths is None and sys.platform == "darwin":
            from .. import platform_mac
            early = platform_mac.drag_files()
            if early:
                print(f"menu: {len(early)} file(s) from the drag pasteboard", flush=True)
        if paths is not None:
            self._load(paths)
        elif early:
            self._load(early)           # slices show at once; drop still comes via dragEnter
        else:
            self.paths, self.rings, self.ring_names = [], {}, []
            self.hub_text = "Solte aqui"
        self._t = 0.0
        self._shape()
        self.show()
        self.raise_()
        self.anim.start()
        self.frame.start()
        if self.click_mode:
            # behave like a popup: a click anywhere outside dismisses it
            QTimer.singleShot(0, self.grabMouse)

    def close_menu(self):
        if self.isVisible():
            self.hide()
            self.frame.stop()
            self.hub_timer.stop()
            self.dismissed.emit()

    def hideEvent(self, e):
        self.frame.stop()
        if QWidget.mouseGrabber() is self:
            self.releaseMouse()
        super().hideEvent(e)

    def _load(self, paths: list[str]):
        paths = resolve_shortcuts(paths)
        self.paths = paths
        self.rings = {k: v for k, v in self.build_rings(paths).items() if v}
        self.ring_names = list(self.rings)
        self.ring_idx = 0
        self.hub_text = self.describe(paths)
        self.spring = [0.0] * len(self.items)
        self._shape()
        self.update()

    def _shape(self):
        """No compositor (XFCE etc.): cut the window to the menu's outline."""
        if not glass.no_compositor():
            return
        c = QPointF(SIZE / 2, SIZE / 2)
        path = QPainterPath()
        path.addEllipse(c, R_HUB + 2, R_HUB + 2)
        n = len(self.items) or 0
        if n:
            for i in range(n):
                a0, a1 = angles(n, i)
                path = path.united(sector_path(c, R_IN - 2, R_OUT + 14, a0 - 1, a1 + 1))
        else:
            outer = QPainterPath()
            outer.addEllipse(c, R_OUT + 14, R_OUT + 14)
            path = path.united(outer)       # united, not added: odd-even fill would punch a hole
        glass.apply_shape(self, path)

    def next_ring(self):
        if len(self.ring_names) > 1:
            self.ring_idx = (self.ring_idx + 1) % len(self.ring_names)
            self.hover = -1
            self.spring = [0.0] * len(self.items)
            self._swap = 0.0
            self.swap_anim.start()
            self._shape()
            self.update()

    def _set_t(self, v):
        self._t = float(v)
        self.update()

    def _set_swap(self, v):
        self._swap = float(v)
        self.update()

    def _tick(self):
        moved = False
        for i in range(len(self.spring)):
            target = 1.0 if i == self.hover else 0.0
            v = self.spring[i]
            nv = v + (target - v) * 0.32
            if abs(nv - target) < 0.003:
                nv = target
            if nv != v:
                self.spring[i] = nv
                moved = True
        ht = 1.0 if self.hover == -2 else 0.0
        nh = self.hub_spring + (ht - self.hub_spring) * 0.3
        if abs(nh - ht) < 0.003:
            nh = ht
        if nh != self.hub_spring:
            self.hub_spring = nh
            moved = True
        if moved:
            self.update()

    # ------------------------------------------------------------ geometry
    @property
    def items(self) -> list[Item]:
        if not self.ring_names:
            return []
        return self.rings[self.ring_names[self.ring_idx]]

    def _angles(self, n: int, i: int) -> tuple[float, float]:
        return angles(n, i)

    def hit(self, pos: QPointF) -> int:
        c = QPointF(SIZE / 2, SIZE / 2)
        dx, dy = pos.x() - c.x(), c.y() - pos.y()
        d = math.hypot(dx, dy)
        if d <= R_HUB + 4:
            return -2
        if d > R_OUT + 30 or not self.items:
            return -1
        ang = math.degrees(math.atan2(dy, dx)) % 360
        n = len(self.items)
        rel = (90 + 180.0 / n - ang) % 360
        return int(rel // (360.0 / n)) % n

    def _set_hover(self, h: int, pos: QPointF | None = None):
        if pos is not None:
            self.cursor_pos = QPointF(pos)
        if h != self.hover:
            self.hover = h
            if h >= 0:
                self.hub_armed = True  # visited a petal: hovering the hub may now flip rings
            if h == -2 and self.hub_armed and len(self.ring_names) > 1:
                self.hub_timer.start()
            else:
                self.hub_timer.stop()
        self.update()

    # ------------------------------------------------------------ drag & drop
    @staticmethod
    def _local_paths(md) -> list[str]:
        if not md.hasUrls():
            return []
        return [u.toLocalFile() for u in md.urls() if u.isLocalFile() and u.toLocalFile()]

    def dragEnterEvent(self, e):
        paths = self._local_paths(e.mimeData())
        if not paths:
            e.ignore()
            return
        self.got_drag = True
        if resolve_shortcuts(paths) != self.paths:
            self._load(paths)
        e.setDropAction(Qt.CopyAction)  # never let a Shift(=move) drop delete the source
        e.accept()

    def dragMoveEvent(self, e):
        self._set_hover(self.hit(e.position()), e.position())
        e.setDropAction(Qt.CopyAction)
        e.accept()

    def dragLeaveEvent(self, e):
        self._set_hover(-1)

    def dropEvent(self, e):
        idx = self.hit(e.position())
        items = self.items
        if 0 <= idx < len(items):
            e.setDropAction(Qt.CopyAction)
            e.accept()
            item, paths = items[idx], list(self.paths)
            self.hide()
            # return to Explorer's drag loop immediately; do the work after
            QTimer.singleShot(0, lambda: self.activated.emit(item, paths))
        else:
            e.ignore()
            self.close_menu()

    # ------------------------------------------------------------ click mode
    def mouseMoveEvent(self, e):
        if self.click_mode:
            self._set_hover(self.hit(e.position()), e.position())

    def mouseReleaseEvent(self, e):
        if not self.click_mode:
            return
        if e.button() == Qt.RightButton:
            self.close_menu()
            return
        idx = self.hit(e.position())
        if idx == -2:
            self.next_ring()
        elif 0 <= idx < len(self.items):
            item, paths = self.items[idx], list(self.paths)
            self.hide()
            QTimer.singleShot(0, lambda: self.activated.emit(item, paths))
        else:
            self.close_menu()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close_menu()
        elif e.key() in (Qt.Key_Tab, self.trigger_key):
            self.next_ring()

    def leaveEvent(self, e):
        if self.click_mode:
            self._set_hover(-1)

    # ------------------------------------------------------------ painting
    def _text_colors(self):
        return QColor(theme.TEXT), QColor(theme.MUTED), None

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        c = QPointF(SIZE / 2, SIZE / 2)
        t = self._t
        p.translate(c)
        s = 0.80 + 0.20 * t
        p.scale(s, s)
        p.translate(-c)

        items = self.items
        n = len(items)
        self._paint_fallback(p, c, n)

        fg, fg_dim, shadow_col = self._text_colors()
        rot = (1 - self._swap) * -22
        for i, it in enumerate(items):
            a0, a1 = angles(n, i)
            h = self.spring[i] if i < len(self.spring) else 0.0
            if h > 0.001:
                self._paint_hover(p, c, a0, a1, h)
            self._petal_label(p, c, it, (a0 + a1) / 2 + rot, (R_IN + R_OUT) / 2 + h * 4, h,
                              fg, shadow_col)
        if not n and self.paths:
            self._paint_unsupported(p, c, fg, fg_dim, shadow_col)

        self._paint_hub(p, c, fg, fg_dim, shadow_col)

    def _paint_unsupported(self, p: QPainter, c: QPointF, fg: QColor, fg_dim: QColor,
                           shadow_col: QColor):
        """Nothing to offer: say so in the top band, clear of the cursor and the drag image."""
        ext = Path(self.paths[0]).suffix.lower() or "este arquivo"
        f = QFont(ui_family(True))
        f.setPixelSize(13)
        f.setBold(True)
        p.setFont(f)
        r_mid = (R_IN + R_OUT) / 2
        self._text(p, QRectF(c.x() - R_OUT, c.y() - r_mid - 18, 2 * R_OUT, 18),
                   f"Formato não compatível: {ext}", fg, shadow_col)
        f.setPixelSize(10)
        f.setBold(False)
        p.setFont(f)
        self._text(p, QRectF(c.x() - R_OUT, c.y() - r_mid + 1, 2 * R_OUT, 16),
                   "Imagens · PDF · Word · Texto", fg_dim, None)

    def _paint_fallback(self, p, c, n):
        hub = QPainterPath()
        hub.addEllipse(c, R_HUB, R_HUB)
        paint_surface(p, hub, theme.BACKGROUND)
        for i in range(n):
            a0, a1 = angles(n, i)
            paint_surface(p, sector_path(c, R_IN, R_OUT, a0, a1))

    def _paint_hover(self, p: QPainter, c: QPointF, a0: float, a1: float, h: float):
        mid = math.radians((a0 + a1) / 2)
        r_mid = (R_IN + R_OUT) / 2
        pc = QPointF(c.x() + r_mid * math.cos(mid), c.y() - r_mid * math.sin(mid))
        k = 1 + 0.07 * h                     # elastic "pop" towards the cursor
        push = 6 * h
        off = QPointF(push * math.cos(mid), -push * math.sin(mid))
        path = sector_path(c, R_IN - 1, R_OUT + 1, a0, a1)
        p.save()
        p.translate(pc + off)
        p.scale(k, k)
        p.translate(-pc)
        paint_surface(p, path, theme.ACCENT_B)
        p.restore()

    def _paint_hub(self, p: QPainter, c: QPointF, fg: QColor, fg_dim: QColor, shadow_col: QColor):
        p.setPen(glass.iridescent_pen(c, 1.2, 255, angle=60))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(c, R_HUB - 0.5, R_HUB - 0.5)

        items = self.items
        hov = items[self.hover] if 0 <= self.hover < len(items) else None
        if hov is not None:
            top, sub = hov.label if not hov.glyph else hov.label.title(), hov.hint or ""
        else:
            ring_name = self.ring_names[self.ring_idx] if self.ring_names else ""
            top = self.hub_text
            if len(self.ring_names) > 1:
                other = self.ring_names[(self.ring_idx + 1) % len(self.ring_names)]
                sub = f"{self.trigger_label} {other.upper()}"
            else:
                sub = ring_name.upper()
        f = QFont(ui_family(True))
        f.setPixelSize(14)
        f.setBold(True)
        p.setFont(f)
        rect_top = QRectF(c.x() - R_HUB + 4, c.y() - 21, 2 * R_HUB - 8, 20)
        self._text(p, rect_top, top, fg, shadow_col)
        f.setPixelSize(10)
        f.setBold(False)
        p.setFont(f)
        self._text(p, QRectF(c.x() - R_HUB + 6, c.y() + 2, 2 * R_HUB - 12, 28), sub, fg_dim, None,
                   Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap)

    @staticmethod
    def _text(p: QPainter, r: QRectF, text: str, col: QColor, shadow: QColor | None,
              flags=Qt.AlignCenter):
        if shadow is not None:
            p.setPen(shadow)
            p.drawText(r.translated(0, 1), flags, text)
        p.setPen(col)
        p.drawText(r, flags, text)

    def _petal_label(self, p: QPainter, c: QPointF, it: Item, ang: float, r: float,
                     h: float, fg: QColor, shadow_col: QColor):
        rad = math.radians(ang)
        push = 6 * h
        pt = QPointF(c.x() + (r + push) * math.cos(rad), c.y() - (r + push) * math.sin(rad))
        p.save()
        p.setOpacity(p.opacity() * (0.25 + 0.75 * self._swap))
        col = QColor(255, 255, 255) if h > 0.5 else fg   # hovered petal is warm-lit: white text
        f = QFont(ui_family(True))
        if it.glyph:
            f.setPixelSize(int(18 + 3 * h))
            p.setFont(f)
            self._text(p, QRectF(pt.x() - 30, pt.y() - 24, 60, 24), it.glyph, col, shadow_col,
                       Qt.AlignHCenter | Qt.AlignBottom)
            f.setPixelSize(10)
            f.setBold(True)
            f.setLetterSpacing(QFont.AbsoluteSpacing, 0.7)
            p.setFont(f)
            self._text(p, QRectF(pt.x() - 42, pt.y() + 1, 84, 16), it.label.upper(), col, shadow_col)
        else:
            f.setPixelSize(int(14 + 2 * h))
            f.setBold(True)
            f.setLetterSpacing(QFont.AbsoluteSpacing, 0.9)
            p.setFont(f)
            self._text(p, QRectF(pt.x() - 42, pt.y() - 12, 84, 24), it.label, col, shadow_col)
        p.restore()
