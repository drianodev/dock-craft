"""
Backend for interacting with Ubuntu Dock settings (dash-to-dock) via GSettings.
"""

from typing import Any, Callable, Dict, List, Optional
import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib


SCHEMA_ID = 'org.gnome.shell.extensions.dash-to-dock'

# Key definitions and metadata
KEY_METADATA = {
    'dock-position': {'type': 'string', 'default': 'BOTTOM'},
    'extend-height': {'type': 'boolean', 'default': False},
    'dash-max-icon-size': {'type': 'int', 'default': 48},
    'autohide': {'type': 'boolean', 'default': True},
    'intellihide': {'type': 'boolean', 'default': True},
    'always-center-icons': {'type': 'boolean', 'default': True},
    'transparency-mode': {'type': 'string', 'default': 'DEFAULT'},
    'background-opacity': {'type': 'double', 'default': 0.8},
    'custom-background-color': {'type': 'boolean', 'default': False},
    'background-color': {'type': 'string', 'default': '#000000'},
    'running-indicator-style': {'type': 'string', 'default': 'DOTS'},
    'running-indicator-dominant-color': {'type': 'boolean', 'default': False},
    'show-trash': {'type': 'boolean', 'default': True},
    'show-mounts': {'type': 'boolean', 'default': False},
    'show-show-apps-button': {'type': 'boolean', 'default': True},
    'show-apps-at-top': {'type': 'boolean', 'default': False},
    'click-action': {'type': 'string', 'default': 'focus-minimize-or-previews'},
    'scroll-action': {'type': 'string', 'default': 'cycle-windows'},
    'scroll-switch-workspace': {'type': 'boolean', 'default': True},
    'scroll-to-focused-application': {'type': 'boolean', 'default': True},
    'custom-theme-shrink': {'type': 'boolean', 'default': True},
    'show-favorites': {'type': 'boolean', 'default': True},
    'show-running': {'type': 'boolean', 'default': True},
    'isolate-monitors': {'type': 'boolean', 'default': True},
    'isolate-workspaces': {'type': 'boolean', 'default': False},
    'unity-backlit-items': {'type': 'boolean', 'default': False},
    'custom-theme-customize-running-dots': {'type': 'boolean', 'default': False},
    'custom-theme-running-dots-color': {'type': 'string', 'default': '#ffffff'},
    'custom-theme-running-dots-border-color': {'type': 'string', 'default': '#ffffff'},
    'custom-theme-running-dots-border-width': {'type': 'int', 'default': 0},
    'force-straight-corner': {'type': 'boolean', 'default': False},
    'apply-custom-theme': {'type': 'boolean', 'default': False},
}


class DockBackend:
    def __init__(self):
        schema_source = Gio.SettingsSchemaSource.get_default()
        if not schema_source or not schema_source.lookup(SCHEMA_ID, True):
            raise RuntimeError(f"GSettings schema '{SCHEMA_ID}' não foi encontrado no sistema.")
        
        self.settings = Gio.Settings.new(SCHEMA_ID)
        self._callbacks: Dict[str, List[Callable[[str, Any], None]]] = {}
        self._changed_handler_id = self.settings.connect('changed', self._on_setting_changed)

        # Safeguard 3: GNOME Shell 46 & ubuntu-dock real-time window tracking fix.
        # Upstream ubuntu-dock only hooks into window creation and restacking signals
        # (global.display 'restacked') when isolate-monitors or isolate-workspaces is True.
        # When both are False, ubuntu-dock does not receive events when unpinned apps launch,
        # so they never appear on the dock until manual extension reload.
        # Ensuring isolate-monitors is True enables the event listener without hiding apps across workspaces.
        if not self.get_value('isolate-monitors') and not self.get_value('isolate-workspaces'):
            self.set_value('isolate-monitors', True)

    def _on_setting_changed(self, settings: Gio.Settings, key: str):
        if key in self._callbacks:
            val = self.get_value(key)
            for cb in self._callbacks[key]:
                try:
                    cb(key, val)
                except Exception as e:
                    print(f"Error in callback for {key}: {e}")

    def add_change_listener(self, key: str, callback: Callable[[str, Any], None]):
        """Register a callback for when a specific key changes."""
        if key not in self._callbacks:
            self._callbacks[key] = []
        self._callbacks[key].append(callback)

    def get_value(self, key: str) -> Any:
        meta = KEY_METADATA.get(key)
        if not meta:
            # Fallback direct get
            variant = self.settings.get_value(key)
            return variant.unpack()
        
        val_type = meta['type']
        if val_type == 'string':
            return self.settings.get_string(key)
        elif val_type == 'boolean':
            return self.settings.get_boolean(key)
        elif val_type == 'int':
            return self.settings.get_int(key)
        elif val_type == 'double':
            return self.settings.get_double(key)
        else:
            return self.settings.get_value(key).unpack()

    def set_value(self, key: str, value: Any) -> bool:
        # Safeguard 1: in Ubuntu 24.04 (GNOME 46), unity-backlit-items=true causes an upstream
        # TypeError in appIconIndicators.js:324 because applyGlossyEffect is undefined in ubuntu-dock,
        # which crashes _createAppItem and makes pinned apps disappear. We enforce False here.
        if key == 'unity-backlit-items':
            value = False

        # Safeguard 2: in GNOME 46, RunningIndicatorMetro calls this._bodyColor.shade()
        # in appIconIndicators.js:619, which throws "TypeError: this._bodyColor.shade is not a function",
        # crashing icon allocation and preventing running apps from being added/drawn on the dock.
        # We safely map METRO to DASHES (which draws identical clean horizontal bar indicators safely).
        if key == 'running-indicator-style' and str(value).upper() == 'METRO':
            value = 'DASHES'

        # Safeguard 3: Prevent dropping the 'restacked' signal listener in ubuntu-dock
        if key == 'isolate-monitors' and not value and not self.get_value('isolate-workspaces'):
            value = True

        meta = KEY_METADATA.get(key)
        try:
            if meta:
                val_type = meta['type']
                if val_type == 'string':
                    return self.settings.set_string(key, str(value))
                elif val_type == 'boolean':
                    return self.settings.set_boolean(key, bool(value))
                elif val_type == 'int':
                    return self.settings.set_int(key, int(value))
                elif val_type == 'double':
                    return self.settings.set_double(key, float(value))
            
            # Auto-detect or variant fallback
            if isinstance(value, bool):
                return self.settings.set_boolean(key, value)
            elif isinstance(value, int):
                return self.settings.set_int(key, value)
            elif isinstance(value, float):
                return self.settings.set_double(key, value)
            elif isinstance(value, str):
                return self.settings.set_string(key, value)
            else:
                return self.settings.set_value(key, GLib.Variant('v', value))
        except Exception as e:
            print(f"Failed to set {key} to {value}: {e}")
            return False

    def get_all_settings(self) -> Dict[str, Any]:
        """Returns a snapshot of all relevant dock settings."""
        snapshot = {}
        for key in KEY_METADATA:
            try:
                snapshot[key] = self.get_value(key)
            except Exception as e:
                print(f"Error reading key {key}: {e}")
        return snapshot

    def apply_settings_dict(self, settings_dict: Dict[str, Any]):
        """Applies a batch of settings (e.g. from a preset)."""
        for key, value in settings_dict.items():
            if key in KEY_METADATA:
                self.set_value(key, value)

    def reset_to_defaults(self):
        """Resets all relevant keys to their schema default values."""
        for key in KEY_METADATA:
            self.settings.reset(key)

    def get_favorite_apps(self) -> List[str]:
        """Returns the list of pinned apps from org.gnome.shell favorite-apps."""
        try:
            gnome_shell_settings = Gio.Settings.new('org.gnome.shell')
            return list(gnome_shell_settings.get_strv('favorite-apps'))
        except Exception as e:
            print(f"Error getting favorite-apps: {e}")
            return []

    def set_favorite_apps(self, app_list: List[str]) -> bool:
        """Updates the list of pinned apps in org.gnome.shell favorite-apps."""
        try:
            gnome_shell_settings = Gio.Settings.new('org.gnome.shell')
            return gnome_shell_settings.set_strv('favorite-apps', app_list)
        except Exception as e:
            print(f"Error setting favorite-apps: {e}")
            return False

    def restart_dock_extension(self) -> bool:
        """Safely reloads the ubuntu-dock GNOME extension."""
        import subprocess
        try:
            subprocess.run(['gnome-extensions', 'disable', 'ubuntu-dock@ubuntu.com'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import time
            time.sleep(0.3)
            subprocess.run(['gnome-extensions', 'enable', 'ubuntu-dock@ubuntu.com'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"Error restarting dock extension: {e}")
            return False
