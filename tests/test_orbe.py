"""Behavioral checks for the new action boundary, desktop wiring and source safety."""
import hashlib
import math
import time
import uuid
from pathlib import Path
import pytest
from PIL import Image
from PySide6.QtCore import QMimeData, QPoint, QPointF, QThread, QUrl, Qt
from PySide6.QtGui import QDropEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel
from orbe.application.actions import Selection, conversion_task, pdf_task, tools_for
from orbe.application.jobs import TaskRunner
from orbe.identity import CREATOR
from orbe.ui.home import HomeWindow
from orbe.ui.credits import CreditsWindow
from orbe.ui.orbit import Item, RadialMenu, SIZE
from orbe.util import UserError


@pytest.fixture(scope="module")
def desktop():
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    yield app
    from orbe.application.bootstrap import dispose_windows
    dispose_windows(app)


@pytest.fixture
def image(tmp_path):
    path = tmp_path / "original.png"
    Image.new("RGB", (120,80), "#84d7ca").save(path)
    return path


def wait_for(app, predicate):
    deadline = time.monotonic()+8
    while not predicate() and time.monotonic()<deadline:
        app.processEvents()
        QTest.qWait(10)
    assert predicate(), "Desktop operation did not finish"


def test_batch_conversion_preserves_sources_and_combines_pages(tmp_path, image):
    second = tmp_path/"second.png"
    Image.new("RGB", (100,90), "#bce892").save(second)
    sources = [image, second]
    before = [hashlib.sha256(path.read_bytes()).digest() for path in sources]
    task = conversion_task(Selection.read(sources), "PDF")
    outputs = task.run()
    from orbe.convert import fitz
    with fitz.open(outputs[0]) as pdf:
        assert pdf.page_count == 2
    assert len(outputs) == 1
    assert before == [hashlib.sha256(path.read_bytes()).digest() for path in sources]
    assert outputs[0] != task.run()[0]


def test_selection_rejects_missing_unsupported_and_empty_files(tmp_path):
    for paths in ([], [tmp_path/"missing.png"], [tmp_path/"unsupported.zip"]):
        with pytest.raises(UserError):
            Selection.read(paths)


def test_action_boundary_rejects_invalid_conversion_and_single_merge(image, tmp_path):
    with pytest.raises(UserError):
        conversion_task(Selection.read([image]), "DOCX")
    from orbe import convert
    pdf = convert.convert(image, "image", "PDF")[0]
    selection = Selection.read([pdf])
    assert "Merge" not in {action.name for action in tools_for(selection)}
    with pytest.raises(UserError):
        pdf_task(selection, "Merge")


def test_home_file_entry_emits_copy_without_modifying_source(desktop, image):
    home = HomeWindow()
    received = []
    home.files_selected.connect(received.append)
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(image))])
    event = QDropEvent(QPointF(40,40), Qt.CopyAction | Qt.MoveAction, mime, Qt.LeftButton, Qt.ShiftModifier)
    home.drop_zone.dropEvent(event)
    assert event.isAccepted() and event.dropAction() == Qt.CopyAction
    assert [[Path(path) for path in group] for group in received] == [[image]] and image.exists()
    home.close()


def test_radial_click_and_ring_switch_select_the_expected_action(desktop, image):
    menu = RadialMenu(lambda paths: {"Converter":[Item("JPG", key="convert:JPG")], "Ferramentas":[Item("Crop", key="tool:Crop")]}, lambda paths:"1 arquivo")
    menu._load([str(image)])
    menu.click_mode = True
    menu.show()
    received = []
    menu.activated.connect(lambda item, paths: received.append((item.key, paths)))
    menu.next_ring()
    QTest.mouseClick(menu, Qt.LeftButton, pos=QPoint(SIZE//2, SIZE//2-120))
    wait_for(desktop, lambda: bool(received))
    assert received == [("tool:Crop", [str(image)])]
    menu.close()


def test_async_operation_reports_on_gui_thread(desktop, image):
    calls = []

    class Card:
        def working(self, *args):
            pass
        def done(self, result):
            calls.append((result, QThread.currentThread() == desktop.thread()))
        def error(self, *args):
            pytest.fail(str(args))

    class Toasts:
        def new(self):
            return Card()

    runner = TaskRunner(Toasts())
    task = conversion_task(Selection.read([image]), "JPG")
    runner.submit(task.key, list(task.sources), task.run, task.working)
    wait_for(desktop, lambda: bool(calls))
    assert calls[0][1] and calls[0][0].outs[0].is_file()
    assert not runner.active


def test_about_presents_orbe_and_keeps_license_available(desktop):
    from PySide6.QtWidgets import QPushButton
    window = CreditsWindow()
    text = " ".join(widget.text() for widget in window.findChildren(QLabel))
    assert "Orbe" in text and CREATOR in text
    assert any(button.text() == "Ver licença" for button in window.findChildren(QPushButton))
    assert "MIT License" in (Path(__file__).resolve().parents[1] / "LICENSE").read_text()
    window.close()


def test_controller_routes_new_menu_to_real_conversion(desktop, image, monkeypatch):
    import orbe.application.controller as controller_module
    from orbe.preferences import DEFAULTS

    class MemorySettings:
        def get(self, key):
            return DEFAULTS[key]
        def apply(self):
            pass

    monkeypatch.setattr(controller_module, "Settings", MemorySettings)
    controller = controller_module.OrbeApplication(desktop, "Orbe-test-"+uuid.uuid4().hex)
    controller.watcher.timer.stop()
    try:
        rings = controller.build_rings([str(image)])
        item = next(item for item in rings["Converter"] if item.key=="convert:JPG")
        controller.run_item(item, [str(image)])
        wait_for(desktop, lambda: bool(controller.history))
        assert controller.history[0].outs[0].suffix == ".jpg"
        assert image.exists()
    finally:
        controller.tray.hide()
        controller.menu.close()
        controller.server.close()
        for card in list(controller.toasts.cards):
            card.dismiss()
        controller.deleteLater()


def test_portuguese_tool_choices_keep_internal_behaviour(desktop, image):
    from orbe import tools
    from PySide6.QtWidgets import QButtonGroup
    redact = tools.RedactWindow(str(image), lambda *args: None)
    assert redact.mode.button(0).text() == "Tarja preta"
    redact.mode.button(1).click()
    assert redact._mode() == "pixelate"
    redact.mode.button(2).click()
    assert redact._mode() == "blur"
    annotation = tools.AnnotateWindow(str(image), lambda *args: None)
    text_button = next(button for group in annotation.findChildren(QButtonGroup)
                       for button in group.buttons() if button.text() == "T Texto")
    text_button.click()
    assert annotation.tool == "Text"
    redact.close()
    annotation.close()


def test_background_save_uses_portuguese_filename_and_preserves_original(desktop, image):
    from orbe import tools
    before = image.read_bytes()
    received = []
    window = tools.AddBgWindow(str(image), lambda *args: received.append(args))
    assert window.primary_btn.text() == "Salvar com fundo"
    assert window.asp.button(0).text() == "Automático"
    window.save()
    output = received[0][2][0]
    assert output.name == "original Com fundo.png" and output.is_file()
    assert image.read_bytes() == before


def test_jpeg_compression_preview_is_localized_and_changes_format(desktop, image, tmp_path):
    from orbe import tools
    source = tmp_path / "foto.jpg"
    Image.open(image).convert("RGB").save(source)
    window = tools.CompressWindow([str(source)], lambda *args: None)
    assert window.primary_btn.text() == "Comprimir"
    assert window.side.itemText(0) == "Tamanho original"
    window.webp.setChecked(True)
    window.estimate()
    assert window._settings()[1] == "WEBP"
    window.close()


def test_password_validation_and_protection_stay_in_portuguese(desktop, image):
    from orbe import tools, convert
    pdf = convert.convert(image, "image", "PDF")[0]
    window = tools.ProtectWindow(str(pdf), lambda *args: None)
    window.pw.setText("abc")
    assert window.msg.text() == "Use pelo menos 4 caracteres."
    window.pw.setText("minha-senha-forte")
    window.pw2.setText("outra-senha")
    assert window.msg.text() == "As senhas ainda não coincidem."
    assert not window.primary_btn.isEnabled()
    window.pw2.setText("minha-senha-forte")
    assert window.msg.text() == "Tudo certo · senha forte"
    assert window.primary_btn.text() == "Proteger" and window.primary_btn.isEnabled()
    window.close()


def test_qt_file_and_colour_dialog_buttons_are_in_portuguese(desktop):
    from orbe.i18n import install_portuguese
    from PySide6.QtWidgets import QColorDialog, QDialogButtonBox, QFileDialog
    assert install_portuguese(desktop)
    file_dialog = QFileDialog()
    file_dialog.setOption(QFileDialog.DontUseNativeDialog)
    file_dialog.setFileMode(QFileDialog.ExistingFiles)
    box = file_dialog.findChild(QDialogButtonBox)
    assert box.button(QDialogButtonBox.Cancel).text().replace("&", "") == "Cancelar"
    assert box.button(QDialogButtonBox.Open).text().replace("&", "") == "Abrir"
    colour_dialog = QColorDialog()
    colour_dialog.setOption(QColorDialog.DontUseNativeDialog)
    box = colour_dialog.findChild(QDialogButtonBox)
    assert box.button(QDialogButtonBox.Cancel).text().replace("&", "") == "Cancelar"
    file_dialog.deleteLater()
    colour_dialog.deleteLater()


def test_results_and_numeric_formatting_use_portuguese(image):
    from orbe import report
    from orbe.util import human_size, sibling
    assert human_size(1536) == "1,5 KB"
    assert report.size_change(1000, 500)[1] == "50% menor"
    assert sibling(image, "Clean").name == "original Sem metadados.png"
    result = report.summarize("tool:Metadata", [image], [image])
    assert result.title == "Metadados removidos" and result.good == "cópia sem dados pessoais"


def test_technical_error_is_logged_without_english_in_user_message():
    from orbe.application.jobs import friendly_error
    assert "Não foi possível" in friendly_error(RuntimeError("unsupported image format"))
    assert friendly_error(UserError("Este PDF está protegido por senha.")) == "Este PDF está protegido por senha."
