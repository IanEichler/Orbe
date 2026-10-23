"""Desktop orchestration: UI events become validated actions and background jobs."""
from __future__ import annotations
from pathlib import Path
import traceback
from PySide6.QtCore import QDir, QObject, QTimer
from PySide6.QtGui import QAction, QCursor, QGuiApplication
from PySide6.QtWidgets import QFileDialog, QMenu, QSystemTrayIcon
from .. import convert, report, tools
from ..identity import APP_NAME
from ..preferences import Settings, TRIGGERS
from ..radial import Item, RadialMenu
from ..toasts import ToastStack
from ..trigger import OrbeWatcher
from ..util import UserError, file_size, human_size
from ..ui import theme
from ..ui.home import HomeWindow
from ..ui.installation import InstallationNotice
from ..ui.credits import CreditsWindow
from ..ui.preferences import SettingsWindow
from .actions import Selection, BY_NAME, tools_for, conversion_task, pdf_task
from .instance import InstanceServer
from .jobs import TaskRunner, friendly_error
from .icons import make_icon


class OrbeApplication(QObject):
    def __init__(self, qapp, instance_name=None):
        super().__init__(qapp)
        self.qapp = qapp
        self.settings = Settings()
        self.settings.apply()
        self.windows = []
        self.home = None
        self.installation_notice = None
        self.history = []
        self.toasts = ToastStack()
        self.runner = TaskRunner(self.toasts, self)
        self.pool = self.runner.pool
        self.runner.completed.connect(self._record)
        self.menu = RadialMenu(self.build_rings, self.describe)
        self.menu.activated.connect(self.run_item)
        self.watcher = OrbeWatcher(lambda: self.menu.isVisible() and not self.menu.click_mode,
                                        lambda: self.menu.got_drag, self)
        self.watcher.set_key(self.settings.get("trigger"))
        self.watcher.show_menu.connect(self.menu.popup)
        self.watcher.toggle_ring.connect(self.menu.next_ring)
        self.watcher.hide_menu.connect(self.menu.close_menu)
        self.watcher.start()
        self.instance = InstanceServer(self, instance_name)
        self.server = self.instance.server
        self.instance.files_received.connect(self.queue_files)
        self.instance.home_requested.connect(self.show_home)
        self.instance.installation_requested.connect(self.show_installation)
        self._pending = []
        self._pending_timer = QTimer(self, singleShot=True, interval=280, timeout=self._flush_pending)
        self._create_tray()

    def _create_tray(self):
        self.tray = QSystemTrayIcon(make_icon(), self)
        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet(theme.stylesheet())
        self.tray_menu.addAction("Abrir Orbe", self.show_home)
        self.tray_menu.addAction("Escolher arquivos…", self.open_dialog)
        self.tray_menu.addSeparator()
        self.act_enabled = QAction("Atalho ativo", self.tray_menu, checkable=True, checked=True)
        self.act_enabled.toggled.connect(self.set_enabled)
        self.tray_menu.addAction(self.act_enabled)
        self.tray_menu.addAction("Preferências…", self.open_settings)
        self.tray_menu.addAction("Como usar", self.show_home)
        self.tray_menu.addAction("Sobre o Orbe…", lambda: self.open_window(CreditsWindow()))
        self.tray_menu.addSeparator()
        self.tray_menu.addAction("Sair do Orbe", self.qapp.quit)
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self._tray_click)
        self._settings_changed()
        self.tray.show()

    def set_enabled(self, enabled):
        self.watcher.enabled = enabled
        if self.act_enabled.isChecked() != enabled:
            self.act_enabled.setChecked(enabled)
        if self.home and self.home.enabled_button.isChecked() != enabled:
            self.home.enabled_button.setChecked(enabled)

    def trigger_label(self):
        return dict(TRIGGERS).get(self.settings.get("trigger"), "Shift")

    def describe(self, paths):
        return human_size(file_size(paths[0])) if len(paths)==1 else f"{len(paths)} arquivos"

    def build_rings(self, paths):
        try:
            selection = Selection.read(paths)
        except UserError:
            return {"Não compatível": []}
        targets = convert.targets_for(selection.kind, Path(selection.paths[0]).suffix)
        conversion_items = []
        for target in targets:
            hint = f"Converter para {target}"
            if selection.kind == "image" and target == "PDF" and len(selection.paths)>1:
                hint = f"{len(selection.paths)} imagens → 1 PDF"
            conversion_items.append(Item(target, key=f"convert:{target}", hint=hint))
        rings = {"Converter": conversion_items}
        actions = tools_for(selection)
        if actions:
            rings["Ferramentas"] = [Item(action.label, action.glyph, key=f"tool:{action.name}", hint=action.hint) for action in actions]
        return rings

    def run_item(self, item, paths):
        try:
            selection = Selection.read(paths)
            kind, name = item.key.split(":", 1)
            if kind == "convert":
                task = conversion_task(selection, name)
            elif kind == "tool":
                action = BY_NAME.get(name)
                if action is None or action not in tools_for(selection):
                    raise UserError("Esta ferramenta não está disponível para a seleção.")
                if selection.kind == "pdf" and name not in ("Metadata", "Protect"):
                    task = pdf_task(selection, name)
                else:
                    factory = getattr(tools, action.editor)
                    sources = list(selection.paths) if action.batch_editor else selection.paths[0]
                    kwargs = {"is_pdf": True} if name == "Metadata" and selection.kind == "pdf" else {}
                    self.open_window(factory(sources, self.notify, **kwargs))
                    return
            else:
                raise UserError("Ação desconhecida.")
            self.submit(task.key, list(task.sources), task.run, task.working)
        except Exception as error:
            if not isinstance(error, UserError):
                traceback.print_exc()
            self.toasts.error("Não foi possível abrir a ação", friendly_error(error))

    def submit(self, action, srcs, fn, working="Processando…", extra=""):
        self.runner.submit(action, srcs, fn, working, extra)

    def notify(self, action, srcs, outs, extra=""):
        result = report.summarize(action, srcs, outs, extra)
        self.toasts.new().done(result)
        self._record(result)

    def _record(self, result):
        self.history.append(result)
        self.history = self.history[-20:]
        if self.home:
            self.home.record(result)

    def open_window(self, window):
        if hasattr(window, "submit"):
            window.submit = self.submit
        self.windows.append(window)
        window.destroyed.connect(lambda *_: self.windows.remove(window) if window in self.windows else None)
        window.present()
        return window

    def show_home(self):
        if self.home:
            self.home.show()
            self.home.raise_()
            self.home.activateWindow()
            return
        home = HomeWindow(self.settings, self.trigger_label(), self.watcher.enabled)
        self.home = home
        home.choose_requested.connect(self.open_dialog)
        home.files_selected.connect(self.show_click_menu)
        home.settings_requested.connect(self.open_settings)
        home.credits_requested.connect(lambda: self.open_window(CreditsWindow()))
        home.enabled_changed.connect(self.set_enabled)
        home.destroyed.connect(lambda *_: setattr(self, "home", None))
        for result in self.history:
            home.record(result)
        self.open_window(home)

    def start(self, quiet=False, installed=False):
        if not quiet and (installed or not self.settings.get("welcomed")):
            self.show_installation()

    def show_installation(self):
        if self.installation_notice:
            self.installation_notice.show()
            self.installation_notice.raise_()
            self.installation_notice.activateWindow()
            return
        notice = InstallationNotice(self.trigger_label())
        self.installation_notice = notice
        notice.destroyed.connect(lambda *_: setattr(self, "installation_notice", None))
        self.open_window(notice)
        self.settings.set("welcomed", True)

    def show_welcome(self):
        self.start()

    def open_settings(self):
        window = SettingsWindow(self.settings)
        window.changed.connect(self._settings_changed)
        self.open_window(window)

    def _settings_changed(self):
        self.watcher.set_key(self.settings.get("trigger"))
        self.menu.set_trigger(self.settings.get("trigger"), self.trigger_label())
        self.tray.setToolTip(f"Orbe · arraste + {self.trigger_label()}")
        if self.home:
            self.home.set_trigger(self.trigger_label())

    def _tray_click(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_home()

    def open_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(None, "Escolher arquivos para o Orbe", QDir.homePath(), options=QFileDialog.DontUseNativeDialog)
        if paths:
            self.show_click_menu(paths)

    def show_click_menu(self, paths):
        try:
            Selection.read(paths)
        except UserError as error:
            self.toasts.error("Escolha outro arquivo", str(error))
            return
        self.menu.popup(QCursor.pos(), paths)

    def queue_files(self, files):
        for path in files:
            if path not in self._pending:
                self._pending.append(path)
        self._pending_timer.start()

    def _flush_pending(self):
        files, self._pending = self._pending, []
        if files:
            self.show_click_menu(files)


# Public shorthand for desktop integrations.
OrbeApp = OrbeApplication
