"""
Main application entry point for DockCraft.
"""

import sys
import os
import signal
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from .backend import DockBackend
from .preset_manager import PresetManager
from .theme_manager import ThemeManager
from .ui.window import DockCraftWindow

APP_ID = "com.github.dockcraft"


class DockCraftApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        self.backend: DockBackend = None
        self.preset_manager: PresetManager = None
        self.theme_manager: ThemeManager = None
        self.window: DockCraftWindow = None

    def do_activate(self):
        if not self.window:
            try:
                self.backend = DockBackend()
                self.preset_manager = PresetManager(self.backend)
                self.theme_manager = ThemeManager(self.backend)
                self.window = DockCraftWindow(self, self.backend, self.preset_manager, self.theme_manager)
            except Exception as e:
                print(f"Erro fatal ao inicializar DockCraft: {e}", file=sys.stderr)
                sys.exit(1)

        self.window.present()


def main():
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Set application identity for Wayland and GNOME Shell window tracking
    GLib.set_prgname(APP_ID)
    GLib.set_application_name("DockCraft")

    app = DockCraftApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
