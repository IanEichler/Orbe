"""Opaque dark-grey desktop palette, preserving the existing rounded controls."""
IRIDESCENT = ["#ff6b9d", "#ffb36b", "#ffe66b", "#7dffb0", "#6bd5ff", "#8a7bff", "#e07bff", "#ff6b9d"]
BACKGROUND = "#292b2f"
SURFACE = "#33363b"
BORDER = "#565c65"
TEXT = "#f1f2f4"
TEXT_DIM = "#b6bdc8"
MUTED = TEXT_DIM
ACCENT_A = "#2b6acb"
ACCENT_B = "#2557bd"
ACCENT_C = "#514bd2"
ACCENT = ACCENT_B
SECONDARY = ACCENT_C
PRIMARY_TEXT = "#ffffff"
CONTROL = "#3e4248"
HOVER = "#4a5058"
GOOD = "#92ddb0"
GOOD_BACKGROUND = "#294637"
ERROR = "#ffaaaa"
ERROR_BACKGROUND = "#482e32"


def stylesheet():
    from ..util import ui_family
    return f'''
    * {{ color: {TEXT}; font-family: "{ui_family(False)}", sans-serif; font-size: 10pt; }}
    QWidget#glassRoot {{ background: transparent; }}
    QLabel#title {{ font-size: 11pt; font-weight: 600; }}
    QLabel#dim, QLabel.dim {{ color: {MUTED}; font-size: 9pt; }}
    QLabel#section {{ color: {MUTED}; font-size: 8.5pt; font-weight: 600; letter-spacing: 1px; }}
    QLabel#brand {{ font-size: 22pt; font-weight: 700; }}
    QLabel#big {{ font-size: 17pt; font-weight: 700; }}
    QLabel#good {{ color: {GOOD}; font-weight: 600; }}
    QLabel#warn {{ color: #f3bd7b; font-weight: 600; }}
    QPushButton {{ background: {CONTROL}; border: 1px solid {BORDER}; border-radius: 15px; padding: 6px 15px; min-height: 18px; }}
    QPushButton:hover {{ background: {HOVER}; border-color: #79828f; }}
    QPushButton:pressed {{ background: #555c65; }}
    QPushButton:checked {{ color: #dce9ff; background: #30496e; border-color: #779bd5; }}
    QPushButton:disabled {{ color: #858d99; background: #35383d; }}
    QPushButton#primary {{ color: {PRIMARY_TEXT}; background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {ACCENT_A}, stop:0.55 {ACCENT_B}, stop:1 {ACCENT_C}); border: 1px solid {ACCENT_B}; font-weight: 600; padding: 7px 20px; border-radius: 16px; }}
    QPushButton#primary:hover {{ border-color: #8db4ff; }}
    QPushButton#primary:disabled {{ color: #929ba9; background: #3b4555; border-color: {BORDER}; }}
    QPushButton#chrome {{ background: transparent; border: none; padding: 2px 8px; font-size: 11pt; border-radius: 6px; }}
    QPushButton#chrome:hover {{ color: {ERROR}; background: #59363c; }}
    QPushButton#swatch {{ border-radius: 12px; padding: 0; min-width: 24px; max-width: 24px; min-height: 24px; max-height: 24px; }}
    QPushButton#swatch:checked {{ border: 2px solid {ACCENT_B}; }}
    QSlider::groove:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT_A}, stop:1 {ACCENT_C}); border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: #ffffff; width: 14px; height: 14px; margin: -6px 0; border-radius: 7px; border: 1px solid {ACCENT_B}; }}
    QSpinBox, QLineEdit, QComboBox {{ background: #222428; border: 1px solid {BORDER}; border-radius: 10px; padding: 4px 8px; selection-background-color: {ACCENT_B}; selection-color: white; }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {ACCENT_B}; }}
    QFrame#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; }}
    QFrame#dropZone {{ background: {SURFACE}; border: 1px dashed #747d8a; border-radius: 12px; }}
    QComboBox QAbstractItemView {{ background: {SURFACE}; color: {TEXT}; border: 1px solid {BORDER}; selection-background-color: #30496e; selection-color: {TEXT}; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 5px; border: 1px solid #85909f; background: #222428; }}
    QCheckBox::indicator:checked {{ background: {ACCENT_B}; border-color: {ACCENT_B}; }}
    QTableWidget {{ background: #222428; alternate-background-color: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; gridline-color: {BORDER}; }}
    QHeaderView, QTableCornerButton::section {{ background: {CONTROL}; border: none; }}
    QHeaderView::section {{ background: {CONTROL}; border: none; padding: 4px; font-weight: 600; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; }}
    QScrollBar::handle:vertical {{ background: #717b89; border-radius: 4px; min-height: 30px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QToolTip {{ background: {SURFACE}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 6px; padding: 4px; }}
    QMenu {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px; }}
    QMenu::item {{ padding: 6px 18px; border-radius: 5px; }}
    QMenu::item:selected {{ background: #30496e; }}
    '''
