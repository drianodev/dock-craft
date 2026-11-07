import unittest
from src.backend import DockBackend
from src.preset_manager import PresetManager


class TestPresets(unittest.TestCase):
    def setUp(self):
        self.backend = DockBackend()
        self.manager = PresetManager(self.backend)

    def test_builtin_presets_loaded(self):
        presets = self.manager.get_presets()
        self.assertGreater(len(presets), 0)
        names = [p.name for p in presets]
        self.assertTrue(any('macOS' in n for n in names))
        self.assertTrue(any('Windows' in n for n in names))
        self.assertTrue(any('Ubuntu' in n for n in names))

    def test_preset_settings_validity(self):
        for preset in self.manager.get_presets():
            self.assertIsInstance(preset.settings, dict)
            self.assertIn('dock-position', preset.settings)
            self.assertIn('dash-max-icon-size', preset.settings)


if __name__ == '__main__':
    unittest.main()
