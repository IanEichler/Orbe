"""One-time installation confirmation with a short usage reminder."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton

from .shell import StudioWindow


class InstallationNotice(StudioWindow):
    def __init__(self, trigger_label="Shift"):
        super().__init__("Orbe instalado", size=(480, 270))
        self.setWindowModality(Qt.ApplicationModal)

        heading = QLabel("Instalado com sucesso!")
        heading.setObjectName("big")
        self.body.addWidget(heading)

        instructions = QLabel(
            f"Para usar, arraste um arquivo, pressione {trigger_label} e solte "
            "em uma opção do menu circular.\n\n"
            f"Pressione {trigger_label} novamente para alternar entre Converter "
            "e Ferramentas."
        )
        instructions.setWordWrap(True)
        self.body.addWidget(instructions)

        status = QLabel("O Orbe fica ativo na bandeja e preserva seus arquivos originais.")
        status.setObjectName("dim")
        status.setWordWrap(True)
        self.body.addWidget(status)
        self.body.addStretch()

        footer = QHBoxLayout()
        footer.addStretch()
        self.done_button = QPushButton("Entendi")
        self.done_button.setObjectName("primary")
        self.done_button.clicked.connect(self.close)
        footer.addWidget(self.done_button)
        self.body.addLayout(footer)
