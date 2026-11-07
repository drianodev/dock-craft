import unittest
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from src.backend import DockBackend
from src.preset_manager import PresetManager
from src.theme_manager import ThemeManager
from src.ui.dock_preview import DockPreviewWidget
from src.ui.page_presets import PresetsPage
from src.ui.page_themes import ThemesPage
from src.ui.page_appearance import AppearancePage
from src.ui.page_behavior import BehaviorPage


class TestUIInit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize GTK / Adwaita
        Adw.init()
        cls.backend = DockBackend()
        cls.preset_manager = PresetManager(cls.backend)
        cls.theme_manager = ThemeManager(cls.backend)

    def test_dock_preview_widget(self):
        preview = DockPreviewWidget(self.backend)
        self.assertIsNotNone(preview)

    def test_presets_page(self):
        page = PresetsPage(self.backend, self.preset_manager, lambda msg: None)
        self.assertIsNotNone(page)

    def test_themes_page(self):
        page = ThemesPage(self.backend, self.theme_manager, lambda msg: None)
        self.assertIsNotNone(page)

    def test_appearance_page(self):
        page = AppearancePage(self.backend, lambda msg: None)
        self.assertIsNotNone(page)

    def test_behavior_page(self):
        page = BehaviorPage(self.backend, lambda msg: None)
        self.assertIsNotNone(page)


if __name__ == '__main__':
    unittest.main()
