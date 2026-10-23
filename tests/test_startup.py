"""Installation notice, persisted first launch, and second-instance delivery."""
import time
import uuid

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QSettings, Qt
from PySide6.QtNetwork import QLocalSocket
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel

from orbe.handoff import launch_payload
from orbe.preferences import Settings, TRIGGERS


@pytest.fixture(scope="module")
def desktop():
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    yield app
    from orbe.application.bootstrap import dispose_windows
    dispose_windows(app)


@pytest.fixture
def controllers(desktop, tmp_path, monkeypatch):
    import orbe.application.controller as module

    def isolated_settings():
        settings = Settings()
        settings.q = QSettings(str(tmp_path / "preferences.ini"), QSettings.IniFormat)
        return settings

    monkeypatch.setattr(module, "Settings", isolated_settings)
    instances = []

    def create():
        controller = module.OrbeApplication(desktop, "Orbe-startup-" + uuid.uuid4().hex)
        controller.watcher.timer.stop()
        instances.append(controller)
        return controller

    yield create
    for controller in instances:
        controller.watcher.timer.stop()
        controller.pool.waitForDone()
        controller.tray.hide()
        controller.menu.close()
        controller.server.close()
        for window in list(controller.windows):
            window.close()
        controller.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    desktop.processEvents()


def test_first_launch_confirms_installation_without_home_and_only_once(controllers):
    first = controllers()
    first.start()
    notice = first.installation_notice
    assert notice.isVisible() and notice.windowModality() == Qt.ApplicationModal
    assert first.home is None and first.windows == [notice]
    text = " ".join(label.text() for label in notice.findChildren(QLabel))
    assert "Instalado com sucesso!" in text
    assert "Shift" in text and "menu circular" in text and "bandeja" in text
    notice.done_button.click()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    assert first.installation_notice is None
    first.settings.q.sync()

    second = controllers()
    second.start()
    assert second.settings.get("welcomed")
    assert second.home is None and second.installation_notice is None
    assert not second.windows
    second.show_home()
    assert second.home.isVisible()  # Instructions remain available on demand.


def test_background_launch_stays_quiet_and_keeps_first_launch_pending(controllers):
    controller = controllers()
    controller.start(quiet=True, installed=True)
    assert not controller.settings.get("welcomed")
    assert not controller.windows and controller.home is None
    controller.settings.set("trigger", "ctrl")
    controller.start()
    text = " ".join(label.text() for label in controller.installation_notice.findChildren(QLabel))
    assert dict(TRIGGERS)["ctrl"] in text


def test_postinstall_handoff_shows_one_notice_in_running_app(controllers, desktop):
    import json

    controller = controllers()
    controller.settings.set("welcomed", True)
    controller.start()
    assert not controller.windows
    socket = QLocalSocket()
    socket.connectToServer(controller.server.serverName())
    assert socket.waitForConnected(1000)
    socket.write(json.dumps(launch_payload(["orbe", "--installed"], [])).encode())
    socket.flush()
    deadline = time.monotonic() + 3
    while controller.installation_notice is None and time.monotonic() < deadline:
        desktop.processEvents()
        QTest.qWait(10)
    assert controller.installation_notice.isVisible()
    assert controller.home is None
    notice = controller.installation_notice
    controller.show_installation()
    assert controller.windows == [notice]
    socket.disconnectFromServer()


def test_launch_payload_preserves_files_and_silent_startup():
    assert launch_payload(["orbe", "--installed"], []) == {"installed": True}
    assert launch_payload(["orbe", "--installed", "--quiet"], []) == {"show": False}
    assert launch_payload(["orbe"], ["foto.png"]) == {"files": ["foto.png"]}
    assert launch_payload(["orbe"], []) == {"show": True}
