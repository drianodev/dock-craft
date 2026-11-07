"""
Themes page for DockCraft: curated color palettes and aesthetic visual themes.
"""

from typing import Callable, List
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk
from ..backend import DockBackend
from ..theme_manager import ThemeManager, DockTheme


class ThemesPage(Adw.PreferencesPage):
    def __init__(self, backend: DockBackend, theme_manager: ThemeManager, on_notify: Callable[[str], None]):
        super().__init__()
        self.backend = backend
        self.theme_manager = theme_manager
        self.on_notify = on_notify

        self.set_title("Temas e Cores")
        self.set_icon_name("applications-graphics-symbolic")

        self.theme_rows: List[Adw.ActionRow] = []

        # Curated Themes Group
        self.themes_group = Adw.PreferencesGroup()
        self.themes_group.set_title("Temas Curados para o Dock")
        self.themes_group.set_description("Paletas de cores desenhadas com harmonia entre cor de fundo, opacidade e marcadores.")
        self.add(self.themes_group)

        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._build_theme_cards()

        # Listen to backend changes to update active theme badges
        for key in ['background-color', 'custom-background-color', 'custom-theme-running-dots-color']:
            self.backend.add_change_listener(key, lambda k, v: GLib.idle_add(self._update_active_badges))

    def _build_theme_cards(self):
        themes = self.theme_manager.get_themes()
        combined_css = []

        for theme in themes:
            row = Adw.ActionRow()
            row._theme = theme
            row.set_title(theme.name)
            row.set_subtitle(theme.description)

            # Palette swatch preview widget
            swatch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            swatch_box.set_valign(Gtk.Align.CENTER)

            # Background color badge
            bg_pill = Gtk.Box()
            bg_pill.set_size_request(26, 26)
            bg_pill.add_css_class(f"swatch-bg-{theme.theme_id}")
            
            # Dot color badge
            dot_pill = Gtk.Box()
            dot_pill.set_size_request(8, 8)
            dot_pill.set_valign(Gtk.Align.CENTER)
            dot_pill.set_halign(Gtk.Align.CENTER)
            dot_pill.add_css_class(f"swatch-dot-{theme.theme_id}")

            combined_css.append(f"""
            .swatch-bg-{theme.theme_id} {{
                background-color: {theme.bg_color};
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
            .swatch-dot-{theme.theme_id} {{
                background-color: {theme.dot_color};
                border-radius: 50%;
            }}
            """)

            bg_pill.append(dot_pill)
            swatch_box.append(bg_pill)
            row.add_prefix(swatch_box)

            # Apply Button
            apply_btn = Gtk.Button(label="Aplicar Tema")
            apply_btn.add_css_class("pill")
            apply_btn.set_valign(Gtk.Align.CENTER)
            apply_btn.connect("clicked", lambda b, tid=theme.theme_id, tname=theme.name: self._apply_theme(tid, tname))
            row._apply_btn = apply_btn
            row.add_suffix(apply_btn)

            self.theme_rows.append(row)
            self.themes_group.add(row)

        full_css = "\n".join(combined_css)
        if hasattr(self.css_provider, 'load_from_string'):
            self.css_provider.load_from_string(full_css)
        else:
            self.css_provider.load_from_data(full_css.encode('utf-8'))

        self._update_active_badges()

    def _apply_theme(self, theme_id: str, theme_name: str):
        success = self.theme_manager.apply_theme(theme_id)
        if success:
            self._update_active_badges()
            self.on_notify(f"Tema '{theme_name}' aplicado ao dock!")
        else:
            self.on_notify(f"Erro ao aplicar o tema '{theme_name}'.")

    def _update_active_badges(self):
        active_id = self.theme_manager.get_active_theme_id()
        for row in self.theme_rows:
            theme = getattr(row, '_theme', None)
            btn = getattr(row, '_apply_btn', None)
            if theme and btn:
                if theme.theme_id == active_id:
                    btn.set_label("✓ Ativo")
                    btn.add_css_class("success")
                    btn.remove_css_class("suggested-action")
                else:
                    btn.set_label("Aplicar Tema")
                    btn.remove_css_class("success")
