"""A bounded local protocol for files handed over by a second launch."""
import json
from pathlib import Path
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtNetwork import QLocalServer
from ..handoff import ipc_name


class InstanceServer(QObject):
    files_received = Signal(list)
    home_requested = Signal()
    installation_requested = Signal()

    def __init__(self, parent=None, name=None):
        super().__init__(parent)
        self.server = QLocalServer(self)
        name = name or ipc_name()
        QLocalServer.removeServer(name)
        if not self.server.listen(name):
            raise RuntimeError(self.server.errorString())
        self.server.newConnection.connect(self._accept)

    def _accept(self):
        socket = self.server.nextPendingConnection()
        if socket is None:
            return
        buffer = bytearray()
        finished = False

        def consume():
            nonlocal finished
            if finished:
                return
            try:
                buffer.extend(bytes(socket.readAll()))
            except RuntimeError:
                return
            if len(buffer) > 65536:
                finished = True
                socket.abort()
                socket.deleteLater()
                return
            try:
                payload = json.loads(buffer.decode("utf-8"))
            except (UnicodeError, ValueError):
                return
            finished = True
            if isinstance(payload, dict):
                candidates = payload.get("files", [])
                files = [path for path in candidates if isinstance(path, str) and Path(path).is_file()] if isinstance(candidates, list) else []
                if files:
                    self.files_received.emit(files)
                elif payload.get("installed"):
                    self.installation_requested.emit()
                elif payload.get("show"):
                    self.home_requested.emit()
            socket.disconnectFromServer()
            socket.deleteLater()

        socket.readyRead.connect(consume)
        socket.disconnected.connect(consume)
        for delay in (0, 50, 200, 600):
            QTimer.singleShot(delay, consume)
