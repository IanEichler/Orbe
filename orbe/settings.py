"""Compatibility facade for preferences and their desktop screens."""
from .preferences import (Settings, DEFAULTS, APP, RUN_KEY, TRIGGERS, OUTPUTS, DPIS,
                          autostart_enabled, set_autostart, launch_command)
from .ui.preferences import SettingsWindow
from .ui.home import HomeWindow as WelcomeWindow
