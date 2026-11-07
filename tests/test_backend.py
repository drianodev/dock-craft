import unittest
from src.backend import DockBackend, KEY_METADATA


class TestBackend(unittest.TestCase):
    def setUp(self):
        self.backend = DockBackend()

    def test_get_keys(self):
        for key in ['dock-position', 'dash-max-icon-size', 'autohide', 'transparency-mode']:
            val = self.backend.get_value(key)
            self.assertIsNotNone(val)

    def test_get_all_settings(self):
        settings = self.backend.get_all_settings()
        self.assertIsInstance(settings, dict)
        self.assertIn('dock-position', settings)
        self.assertIn('dash-max-icon-size', settings)
        self.assertIn('show-favorites', settings)

    def test_favorite_apps(self):
        favs = self.backend.get_favorite_apps()
        self.assertIsInstance(favs, list)
        self.assertGreater(len(favs), 0)

    def test_unity_backlit_safeguard(self):
        # Attempting to set unity-backlit-items=True should be forced to False
        self.backend.set_value('unity-backlit-items', True)
        self.assertFalse(self.backend.get_value('unity-backlit-items'))

    def test_metro_indicator_safeguard(self):
        # Attempting to set running-indicator-style='METRO' should be safely mapped to 'DASHES'
        self.backend.set_value('running-indicator-style', 'METRO')
        self.assertEqual(self.backend.get_value('running-indicator-style'), 'DASHES')

    def test_show_running_setting(self):
        self.backend.set_value('show-running', True)
        self.assertTrue(self.backend.get_value('show-running'))


if __name__ == '__main__':
    unittest.main()
