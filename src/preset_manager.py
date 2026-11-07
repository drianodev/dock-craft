"""
Preset manager for DockCraft: handles built-in and user presets.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from .backend import DockBackend


class Preset:
    def __init__(self, key_id: str, name: str, description: str, icon: str, settings: Dict[str, Any], is_builtin: bool = False):
        self.key_id = key_id
        self.name = name
        self.description = description
        self.icon = icon
        self.settings = settings
        self.is_builtin = is_builtin

    @classmethod
    def from_dict(cls, key_id: str, data: Dict[str, Any], is_builtin: bool = False) -> 'Preset':
        return cls(
            key_id=key_id,
            name=data.get('name', key_id),
            description=data.get('description', ''),
            icon=data.get('icon', 'preferences-system-symbolic'),
            settings=data.get('settings', {}),
            is_builtin=is_builtin
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'settings': self.settings
        }


class PresetManager:
    def __init__(self, backend: DockBackend):
        self.backend = backend
        self.builtin_dir = Path(__file__).resolve().parent.parent / 'presets'
        self.user_dir = Path.home() / '.config' / 'dockcraft' / 'presets'
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.presets: Dict[str, Preset] = {}
        self.load_all_presets()

    def load_all_presets(self):
        self.presets.clear()
        
        # Load built-in presets
        if self.builtin_dir.exists():
            for file in sorted(self.builtin_dir.glob('*.json')):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        preset_id = file.stem
                        self.presets[preset_id] = Preset.from_dict(preset_id, data, is_builtin=True)
                except Exception as e:
                    print(f"Error loading built-in preset {file}: {e}")

        # Load user presets
        if self.user_dir.exists():
            for file in sorted(self.user_dir.glob('*.json')):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        preset_id = f"user_{file.stem}"
                        self.presets[preset_id] = Preset.from_dict(preset_id, data, is_builtin=False)
                except Exception as e:
                    print(f"Error loading user preset {file}: {e}")

    def get_presets(self) -> List[Preset]:
        return list(self.presets.values())

    def apply_preset(self, preset_id: str) -> bool:
        if preset_id not in self.presets:
            return False
        preset = self.presets[preset_id]
        self.backend.apply_settings_dict(preset.settings)
        return True

    def save_current_as_preset(self, name: str, description: str = "") -> Optional[Preset]:
        current_settings = self.backend.get_all_settings()
        slug = "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")
        if not slug:
            slug = "custom_preset"
        
        file_path = self.user_dir / f"{slug}.json"
        preset_id = f"user_{slug}"
        preset = Preset(
            key_id=preset_id,
            name=name,
            description=description or "Preset personalizado do usuário",
            icon="starred-symbolic",
            settings=current_settings,
            is_builtin=False
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(preset.to_dict(), f, indent=2, ensure_ascii=False)
            
        self.presets[preset_id] = preset
        return preset

    def delete_user_preset(self, preset_id: str) -> bool:
        if preset_id not in self.presets:
            return False
        preset = self.presets[preset_id]
        if preset.is_builtin:
            return False
        
        slug = preset_id.replace("user_", "", 1)
        file_path = self.user_dir / f"{slug}.json"
        if file_path.exists():
            file_path.unlink()
        del self.presets[preset_id]
        return True
