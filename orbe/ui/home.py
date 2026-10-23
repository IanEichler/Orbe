"""On-demand usage instructions and file entry for Orbe."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from .shell import StudioWindow
from . import theme


class FileDropZone(QFrame):
    files_selected = Signal(list)
    choose_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 9, 12, 9)
        hint = QLabel("Solte arquivos aqui ou")
        hint.setObjectName("dim")
        row.addWidget(hint)
        row.addStretch()
        choose = QPushButton("Escolher arquivos…")
        choose.setObjectName("primary")
        choose.clicked.connect(self.choose_requested.emit)
        row.addWidget(choose)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.files_selected.emit(paths)
        else:
            event.ignore()


class HomeWindow(StudioWindow):
    choose_requested = Signal()
    files_selected = Signal(list)
    settings_requested = Signal()
    credits_requested = Signal()
    enabled_changed = Signal(bool)

    def __init__(self, settings=None, trigger_label="Shift", enabled=True):
        super().__init__("Bem-vindo ao Orbe", size=(560, 430))
        self.results = []
        self.step_title = None
        self.switch_title = None
        steps = (
            ("1", "Comece a arrastar um arquivo", "no Explorador de Arquivos ou na área de trabalho"),
            ("2", f"Pressione {trigger_label}", "o menu circular aparece junto ao cursor"),
            ("3", "Solte em uma opção", "o resultado é salvo sem alterar o original"),
            ("⇄", f"Pressione {trigger_label} novamente", "para alternar entre Converter e Ferramentas"),
        )
        for index, (number, title, detail) in enumerate(steps):
            row = QHBoxLayout()
            badge = QLabel(number)
            badge.setAlignment(Qt.AlignCenter)
            badge.setFixedSize(34, 34)
            badge.setStyleSheet(f"color: {theme.PRIMARY_TEXT}; background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {theme.ACCENT_A}, stop:1 {theme.ACCENT_B}); border-radius:17px; font-weight:700; font-size:12pt;")
            row.addWidget(badge)
            row.addSpacing(8)
            texts = QVBoxLayout()
            texts.setSpacing(1)
            heading = QLabel(title)
            heading.setStyleSheet("font-size:12pt; font-weight:600;")
            subtitle = QLabel(detail)
            subtitle.setObjectName("dim")
            texts.addWidget(heading)
            texts.addWidget(subtitle)
            row.addLayout(texts, 1)
            self.body.addLayout(row)
            if index == 1:
                self.step_title = heading
            if index == 3:
                self.switch_title = heading
        self.body.addStretch()
        self.drop_zone = FileDropZone()
        self.drop_zone.choose_requested.connect(self.choose_requested.emit)
        self.drop_zone.files_selected.connect(self.files_selected.emit)
        self.body.addWidget(self.drop_zone)
        self.activity = QLabel("O Orbe continua na bandeja ao fechar esta janela.")
        self.activity.setObjectName("dim")
        self.activity.setWordWrap(True)
        self.body.addWidget(self.activity)
        footer = QHBoxLayout()
        self.enabled_button = QPushButton("Atalho ativo")
        self.enabled_button.setCheckable(True)
        self.enabled_button.setChecked(enabled)
        self.enabled_button.toggled.connect(self._toggle_label)
        self.enabled_button.toggled.connect(self.enabled_changed.emit)
        self._toggle_label(enabled)
        footer.addWidget(self.enabled_button)
        for text, action in (("Preferências", self.settings_requested.emit), ("Sobre", self.credits_requested.emit)):
            button = QPushButton(text)
            button.clicked.connect(action)
            footer.addWidget(button)
        footer.addStretch()
        done = QPushButton("Entendi")
        done.setObjectName("primary")
        done.clicked.connect(self.close)
        footer.addWidget(done)
        self.body.addLayout(footer)

    def _toggle_label(self, enabled):
        self.enabled_button.setText("Atalho ativo" if enabled else "Atalho pausado")

    def set_trigger(self, text):
        self.step_title.setText(f"Pressione {text}")
        self.switch_title.setText(f"Pressione {text} novamente")

    def record(self, result):
        self.results.append(result)
        self.results = self.results[-20:]
        self.activity.setText(f"✓ {result.title}")
        self.activity.setToolTip(result.detail)
