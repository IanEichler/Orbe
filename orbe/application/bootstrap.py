"""Process startup and Qt lifecycle; no file-operation or editor logic here."""
from __future__ import annotations
import faulthandler
import os
import sys
import time
import traceback
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QEvent, QThreadPool, Qt, QTimer, Signal
from PySide6.QtNetwork import QLocalSocket
from PySide6.QtWidgets import QApplication
from ..identity import APP_NAME, VERSION
from ..handoff import ipc_name, launch_payload
from .controller import OrbeApplication
from .icons import make_icon


class DesktopApplication(QApplication):
    file_opened = Signal(str)

    def __init__(self, argv):
        super().__init__(argv)
        self.early_files = []

    def event(self, event):
        if event.type() == QEvent.FileOpen and event.file():
            self.early_files.append(event.file())
            self.file_opened.emit(event.file())
            return True
        return super().event(event)


def setup_logging():
    if sys.platform == "darwin":
        base = Path.home()/"Library"/"Logs"/APP_NAME
    else:
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home()/".local"/"share")/APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    path = base/"log.txt"
    if path.exists() and path.stat().st_size>1_000_000:
        path.replace(base/"log.old.txt")
    stream = path.open("a", encoding="utf-8", buffering=1)
    stream.write(f"\n==== {APP_NAME} {VERSION} · {time.strftime('%Y-%m-%d %H:%M:%S')} ====\n")
    if sys.stderr is None or getattr(sys,"frozen",False) or sys.executable.lower().endswith("pythonw.exe"):
        sys.stdout = sys.stderr = stream
    faulthandler.enable(stream)
    sys.excepthook = lambda kind,value,tb: stream.write("Unhandled: "+"".join(traceback.format_exception(kind,value,tb)))
    return path


def send_to_running(payload):
    import json
    socket = QLocalSocket()
    socket.connectToServer(ipc_name())
    if not socket.waitForConnected(300):
        return False
    socket.write(json.dumps(payload).encode("utf-8"))
    socket.flush()
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


def dispose_windows(qapp):
    """Release native windows before Qt's application and font services exit."""
    QThreadPool.globalInstance().waitForDone()
    qapp.processEvents()
    for widget in qapp.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    QThreadPool.globalInstance().waitForDone()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()


def main(argv=None):
    argv = sys.argv if argv is None else argv
    setup_logging()
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("NexoAtelier.Orbe")
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_DontUseNativeDialogs, True)
    qapp = DesktopApplication(argv)
    from ..i18n import install_portuguese
    install_portuguese(qapp)
    if sys.platform == "darwin":
        from .. import platform_mac
        platform_mac.become_accessory()
    qapp.setApplicationName(APP_NAME)
    qapp.setApplicationVersion(VERSION)
    qapp.setQuitOnLastWindowClosed(False)
    qapp.setWindowIcon(make_icon())
    if "--selftest" in argv:
        from .diagnostics import selftest
        result = selftest()
        # Finish background work and destroy windows while Qt is alive.
        dispose_windows(qapp)
        return result
    files = [os.path.abspath(arg) for arg in argv[1:] if not arg.startswith("-") and Path(arg).is_file()]
    if send_to_running(launch_payload(argv, files)):
        return 0
    controller = OrbeApplication(qapp)
    qapp.file_opened.connect(lambda path: controller.queue_files([path]))
    if qapp.early_files:
        controller.queue_files(qapp.early_files)
    if files:
        QTimer.singleShot(120, lambda: controller.queue_files(files))
    else:
        QTimer.singleShot(120, lambda: controller.start(
            quiet="--quiet" in argv, installed="--installed" in argv))
    result = qapp.exec()
    controller.watcher.timer.stop()
    controller.pool.waitForDone()
    qapp.processEvents()
    controller.tray.hide()
    controller.server.close()
    dispose_windows(qapp)
    return result


OrbeQApplication = DesktopApplication
