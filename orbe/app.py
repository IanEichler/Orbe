"""Public application entry point and desktop integrations."""
from .application.bootstrap import (main, setup_logging, send_to_running,
                                     DesktopApplication as OrbeQApplication)
from .application.controller import OrbeApplication, OrbeApp
from .application.diagnostics import selftest, check_text_renders
from .application.jobs import Job, friendly_error
from .application.icons import make_icon, make_tray_icon
from .identity import APP_NAME, VERSION
from .handoff import ipc_name
from . import convert, imaging, tools, report, glass
from .radial import Item, RadialMenu
IPC_NAME = ipc_name()
