"""Background work and lifetime management, with UI completion on the main thread."""
import traceback
from pathlib import Path
from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal
from .. import report
from ..util import UserError, keep, release


def friendly_error(error):
    if isinstance(error, UserError):
        return str(error)
    if isinstance(error, PermissionError):
        return "Sem permissão para salvar. Escolha outra pasta nas preferências."
    if isinstance(error, FileNotFoundError):
        return "O arquivo foi movido ou excluído."
    if "cannot identify image" in str(error).lower():
        return "Não foi possível ler esta imagem."
    return "Não foi possível processar o arquivo. Consulte os registros do aplicativo para mais detalhes."


class JobSignals(QObject):
    done = Signal(object)
    failed = Signal(str)


class Job(QRunnable):
    def __init__(self, action, srcs, fn, extra=""):
        super().__init__()
        self.action, self.srcs, self.fn, self.extra = action, srcs, fn, extra
        self.sig = JobSignals()

    def run(self):
        try:
            result = report.summarize(self.action, self.srcs, self.fn() or [], self.extra)
            self.sig.done.emit(result)
        except Exception as error:
            if not isinstance(error, UserError):
                traceback.print_exc()
            self.sig.failed.emit(friendly_error(error))


class TaskRunner(QObject):
    completed = Signal(object)

    def __init__(self, toasts, parent=None):
        super().__init__(parent)
        self.toasts = toasts
        self.pool = QThreadPool.globalInstance()
        self.active = set()

    def submit(self, action, srcs, fn, working="Processando…", extra=""):
        state = {"card": None, "finished": False}
        job = Job(action, srcs, fn, extra)
        self.active.add(job)

        def spinner():
            if not state["finished"]:
                state["card"] = self.toasts.new()
                names = Path(srcs[0]).name if len(srcs) == 1 else f"{len(srcs)} arquivos"
                state["card"].working(working, names)

        def finish(result=None, error=None):
            state["finished"] = True
            card = state["card"] or self.toasts.new()
            if error is None:
                card.done(result)
                self.completed.emit(result)
            else:
                card.error("Não foi possível concluir", error)
            self.active.discard(job)
            release(job)

        # QObject receivers keep the signal delivery on the GUI thread, including
        # callbacks created here; QRunnable itself never touches a widget.
        job.sig.done.connect(lambda result: finish(result=result))
        job.sig.failed.connect(lambda error: finish(error=error))
        QTimer.singleShot(150, spinner)
        self.pool.start(keep(job))
