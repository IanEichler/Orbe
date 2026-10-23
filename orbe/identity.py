"""Product identity and presentation text. Copyright notices remain in LICENSE."""
APP_NAME = "Orbe"
EDITION = "Edição Estúdio"
CREATOR = "Nexo Atelier"
VERSION = "2.0.0"
REPOSITORY_URL = "https://github.com/IanEichler/Orbe"


def attribution() -> str:
    return (
        f"{APP_NAME} — {EDITION}\n"
        f"Identidade e personalização: {CREATOR}.\n\n"
        "Converta arquivos e edite imagens com o menu circular. "
        "Arraste um arquivo, pressione a tecla de atalho e escolha uma opção."
    )
