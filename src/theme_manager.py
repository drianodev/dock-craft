"""
Theme Manager for DockCraft: curated color palettes and aesthetic visual themes.
"""

from typing import Any, Dict, List, Optional
from .backend import DockBackend


class DockTheme:
    def __init__(
        self,
        theme_id: str,
        name: str,
        description: str,
        bg_color: str,
        bg_opacity: float,
        dot_color: str,
        indicator_style: str,
        badge_color: str
    ):
        self.theme_id = theme_id
        self.name = name
        self.description = description
        self.bg_color = bg_color
        self.bg_opacity = bg_opacity
        self.dot_color = dot_color
        self.indicator_style = indicator_style
        self.badge_color = badge_color

    def get_settings(self) -> Dict[str, Any]:
        return {
            'custom-background-color': True,
            'background-color': self.bg_color,
            'background-opacity': self.bg_opacity,
            'transparency-mode': 'FIXED',
            'custom-theme-customize-running-dots': True,
            'custom-theme-running-dots-color': self.dot_color,
            'running-indicator-style': self.indicator_style,
            'running-indicator-dominant-color': False,
        }


BUILTIN_THEMES = [
    DockTheme(
        theme_id="dracula",
        name="Dracula Dark",
        description="Fundo roxo-escuro característico com marcadores rosa neon vibrantes.",
        bg_color="#282a36",
        bg_opacity=0.88,
        dot_color="#ff79c6",
        indicator_style="DOTS",
        badge_color="#ff79c6"
    ),
    DockTheme(
        theme_id="cyberpunk",
        name="Cyberpunk Neon",
        description="Visual futurista de alta tecnologia com marcadores em barra ciano elétrico.",
        bg_color="#0a0f1d",
        bg_opacity=0.85,
        dot_color="#00f2fe",
        indicator_style="DASHES",
        badge_color="#00f2fe"
    ),
    DockTheme(
        theme_id="nord",
        name="Nord Arctic",
        description="Paleta nórdica escandinava com cinza ardósia e azul glacial suave.",
        bg_color="#2e3440",
        bg_opacity=0.85,
        dot_color="#88c0d0",
        indicator_style="DOTS",
        badge_color="#88c0d0"
    ),
    DockTheme(
        theme_id="tokyo_night",
        name="Tokyo Night",
        description="Tons noturnos de Tóquio com azul profundo e acentos lilás-violeta.",
        bg_color="#1a1b26",
        bg_opacity=0.88,
        dot_color="#bb9af7",
        indicator_style="DASHES",
        badge_color="#bb9af7"
    ),
    DockTheme(
        theme_id="gruvbox",
        name="Gruvbox Retro",
        description="Estética aconchegante retrô com fundo carvão e marcadores dourados.",
        bg_color="#282828",
        bg_opacity=0.90,
        dot_color="#fabd2f",
        indicator_style="DOTS",
        badge_color="#fabd2f"
    ),
    DockTheme(
        theme_id="ubuntu_yaru",
        name="Ubuntu Yaru Modern",
        description="Beringela escuro oficial com marcadores no laranja vibrante do Ubuntu.",
        bg_color="#2c001e",
        bg_opacity=0.82,
        dot_color="#e95420",
        indicator_style="DOTS",
        badge_color="#e95420"
    ),
    DockTheme(
        theme_id="frosted_glass",
        name="Vidro Fosco (Glass)",
        description="Efeito translúcido suave e arejado que destaca papéis de parede coloridos.",
        bg_color="#ffffff",
        bg_opacity=0.28,
        dot_color="#3584e4",
        indicator_style="DOTS",
        badge_color="#3584e4"
    ),
    DockTheme(
        theme_id="oled_black",
        name="OLED Pure Black",
        description="Preto 100% puro com barras em verde esmeralda, contraste extremo.",
        bg_color="#000000",
        bg_opacity=0.96,
        dot_color="#2ec27e",
        indicator_style="DASHES",
        badge_color="#2ec27e"
    ),
]


class ThemeManager:
    def __init__(self, backend: DockBackend):
        self.backend = backend
        self.themes: Dict[str, DockTheme] = {t.theme_id: t for t in BUILTIN_THEMES}

    def get_themes(self) -> List[DockTheme]:
        return list(self.themes.values())

    def apply_theme(self, theme_id: str) -> bool:
        if theme_id not in self.themes:
            return False
        theme = self.themes[theme_id]
        self.backend.apply_settings_dict(theme.get_settings())
        return True

    def get_active_theme_id(self) -> Optional[str]:
        custom = self.backend.get_value('custom-background-color')
        if not custom:
            return None
        bg = str(self.backend.get_value('background-color')).lower()
        dot = str(self.backend.get_value('custom-theme-running-dots-color')).lower()
        for theme in self.themes.values():
            if bg == theme.bg_color.lower() and dot == theme.dot_color.lower():
                return theme.theme_id
        for theme in self.themes.values():
            if bg == theme.bg_color.lower():
                return theme.theme_id
        return None

    def is_theme_active(self, theme: DockTheme) -> bool:
        return self.get_active_theme_id() == theme.theme_id
