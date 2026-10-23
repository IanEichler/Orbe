"""Declarative action catalog and plans, independent of desktop widgets."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from .. import convert, imaging
from ..util import UserError, category, resolve_shortcuts


@dataclass(frozen=True)
class Selection:
    paths: tuple[str, ...]
    kind: str

    @classmethod
    def read(cls, paths):
        resolved = resolve_shortcuts([str(path) for path in paths])
        if not resolved:
            raise UserError("Escolha pelo menos um arquivo.")
        kind = category(resolved[0])
        if kind is None:
            raise UserError("Escolha imagens, PDFs, documentos Word ou arquivos de texto.")
        compatible = tuple(dict.fromkeys(path for path in resolved if category(path) == kind))
        for path in compatible:
            if not Path(path).is_file():
                raise UserError(f"Arquivo não encontrado: {Path(path).name}")
        return cls(compatible, kind)


@dataclass(frozen=True)
class Action:
    name: str
    label: str
    glyph: str
    hint: str
    kinds: tuple[str, ...]
    editor: str = ""
    batch_editor: bool = False


ACTIONS = (
    Action("Compress", "Comprimir", "⇲", "Reduza o tamanho", ("image", "pdf"), "CompressWindow", True),
    Action("Resize", "Dimensões", "⤢", "Ajuste largura e altura", ("image",), "ResizeWindow", True),
    Action("Crop", "Recortar", "⌗", "Escolha um enquadramento", ("image",), "CropWindow"),
    Action("Edit", "Ajustar", "☼", "Luz, cores e rotação", ("image",), "EditWindow"),
    Action("Annotate", "Anotar", "✎", "Texto, formas e setas", ("image",), "AnnotateWindow"),
    Action("Redact", "Ocultar", "▮", "Oculte trechos da imagem", ("image",), "RedactWindow"),
    Action("Add BG", "Fundo", "▣", "Uma nova composição", ("image",), "AddBgWindow"),
    Action("Metadata", "Metadados", "ⓘ", "Consulte ou remova dados", ("image", "pdf"), "MetadataWindow"),
    Action("Split", "Separar", "✂", "Um arquivo por página", ("pdf",)),
    Action("Rotate", "Girar", "⟳", "Gire páginas em 90°", ("pdf",)),
    Action("Merge", "Unir", "⧉", "Combine vários PDFs", ("pdf",)),
    Action("Protect", "Proteger", "⚿", "Adicione uma senha", ("pdf",), "ProtectWindow"),
    Action("Extract", "Extrair", "⧈", "Salve imagens do PDF", ("pdf",)),
)
BY_NAME = {action.name: action for action in ACTIONS}
PDF_ORDER = ("Compress", "Split", "Rotate", "Merge", "Protect", "Extract", "Metadata")


def tools_for(selection: Selection):
    if selection.kind == "pdf":
        return tuple(BY_NAME[name] for name in PDF_ORDER if name != "Merge" or len(selection.paths) > 1)
    return tuple(action for action in ACTIONS if selection.kind in action.kinds)


@dataclass(frozen=True)
class Task:
    key: str
    sources: tuple[str, ...]
    run: Callable[[], list]
    working: str


def conversion_task(selection: Selection, target: str) -> Task:
    allowed = convert.targets_for(selection.kind, Path(selection.paths[0]).suffix)
    if target not in allowed:
        raise UserError(f"Conversão indisponível: {target}.")
    paths = selection.paths
    if selection.kind == "image" and target == "PDF" and len(paths) > 1:
        operation = lambda: convert.images_to_single_pdf(paths)
    else:
        operation = lambda: [out for path in paths for out in convert.convert(path, selection.kind, target)]
    return Task(f"convert:{target}", paths, operation, f"Convertendo para {target}…")


PDF_OPERATIONS = {
    "Compress": lambda path: [imaging.compress_pdf(path)],
    "Split": imaging.split_pdf,
    "Rotate": lambda path: [imaging.rotate_pdf(path)],
    "Extract": imaging.extract_pdf_images,
}


def pdf_task(selection: Selection, name: str) -> Task:
    if selection.kind != "pdf":
        raise UserError("Esta ação precisa de arquivos PDF.")
    paths = selection.paths
    if name == "Merge":
        if len(paths) < 2:
            raise UserError("Escolha pelo menos dois PDFs para unir.")
        operation = lambda: [imaging.merge_pdfs(paths)]
    elif name in PDF_OPERATIONS:
        operation = lambda: [out for path in paths for out in PDF_OPERATIONS[name](path)]
    else:
        raise UserError("Ferramenta de PDF indisponível.")
    return Task(f"tool:{name}", paths, operation, f"{BY_NAME[name].label}…")
