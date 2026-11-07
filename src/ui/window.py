"""
Main application window for DockCraft.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from ..backend import DockBackend
from ..preset_manager import PresetManager
from ..theme_manager import ThemeManager
from .dock_preview import DockPreviewWidget
from .page_presets import PresetsPage
from .page_themes import ThemesPage
from .page_appearance import AppearancePage
from .page_behavior import BehaviorPage


class DockCraftWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, backend: DockBackend, preset_manager: PresetManager, theme_manager: ThemeManager):
        super().__init__(application=app)
        self.backend = backend
        self.preset_manager = preset_manager
        self.theme_manager = theme_manager

        self.set_title("DockCraft")
        self.set_default_size(1020, 750)
        self.set_size_request(650, 500)

        # Toast Overlay
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        # Main Layout Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(main_box)

        # HeaderBar
        self.header_bar = Adw.HeaderBar()
        main_box.append(self.header_bar)

        # Title Widget with ViewSwitcher
        self.view_stack = Adw.ViewStack()
        
        self.view_switcher = Adw.ViewSwitcher()
        self.view_switcher.set_stack(self.view_stack)
        self.view_switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE)
        self.header_bar.set_title_widget(self.view_switcher)

        # Reload Dock Button on HeaderBar
        reload_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        reload_btn.set_tooltip_text("Recarregar Extensão do Dock")
        reload_btn.connect("clicked", lambda b: self._on_reload_clicked())
        self.header_bar.pack_start(reload_btn)

        # Reset Button on HeaderBar
        reset_btn = Gtk.Button.new_from_icon_name("view-restore-symbolic")
        reset_btn.set_tooltip_text("Restaurar Configurações Originais do Ubuntu")
        reset_btn.connect("clicked", self._on_reset_clicked)
        self.header_bar.pack_start(reset_btn)

        # About / Menu Button on HeaderBar
        about_btn = Gtk.Button.new_from_icon_name("help-about-symbolic")
        about_btn.set_tooltip_text("Sobre o DockCraft")
        about_btn.connect("clicked", self._on_about_clicked)
        self.header_bar.pack_end(about_btn)

        # Responsive Adaptive Content Box (Horizontal with Left Preview by default)
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.content_box.set_vexpand(True)
        self.content_box.set_hexpand(True)
        main_box.append(self.content_box)

        # Dock Miniature Preview Widget on the LEFT
        self.preview_widget = DockPreviewWidget(self.backend)
        self.content_box.append(self.preview_widget)

        # Separator line between Preview and Pages
        self.separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.content_box.append(self.separator)

        # Pages
        self.page_presets = PresetsPage(self.backend, self.preset_manager, self.show_toast)
        self.page_themes = ThemesPage(self.backend, self.theme_manager, self.show_toast)
        self.page_appearance = AppearancePage(self.backend, self.show_toast)
        self.page_behavior = BehaviorPage(self.backend, self.show_toast)

        self.view_stack.add_titled_with_icon(self.page_presets, "presets", "Presets", "starred-symbolic")
        self.view_stack.add_titled_with_icon(self.page_themes, "themes", "Temas", "applications-graphics-symbolic")
        self.view_stack.add_titled_with_icon(self.page_appearance, "appearance", "Aparência", "preferences-desktop-theme-symbolic")
        self.view_stack.add_titled_with_icon(self.page_behavior, "behavior", "Comportamento", "input-mouse-symbolic")

        # Right Side: ViewStack with preferences pages
        self.view_stack.set_vexpand(True)
        self.view_stack.set_hexpand(True)
        self.content_box.append(self.view_stack)

        # Adaptive Breakpoint: when window width <= 860px, move preview smoothly to TOP
        self.breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse('max-width: 860px'))
        self.breakpoint.add_setter(self.content_box, 'orientation', Gtk.Orientation.VERTICAL)
        self.breakpoint.add_setter(self.separator, 'orientation', Gtk.Orientation.HORIZONTAL)
        self.breakpoint.connect('apply', lambda b: self.preview_widget.set_mode('top'))
        self.breakpoint.connect('unapply', lambda b: self.preview_widget.set_mode('side'))
        self.add_breakpoint(self.breakpoint)

    def show_toast(self, message: str):
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

    def _on_reload_clicked(self):
        success = self.backend.restart_dock_extension()
        if success:
            self.show_toast("Extensão do dock recarregada com sucesso.")
        else:
            self.show_toast("Erro ao recarregar extensão do dock.")

    def _on_reset_clicked(self, button: Gtk.Button):
        dialog = Adw.MessageDialog.new(
            self,
            "Restaurar Padrão de Fábrica?",
            "Todas as modificações de estilo, posição e comportamento do dock serão revertidas para as opções originais do Ubuntu."
        )
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("reset", "Restaurar")
        dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)

        def on_response(dlg, response):
            if response == "reset":
                self.preset_manager.apply_preset("ubuntu_default")
                self.show_toast("Configurações do dock restauradas para o padrão do Ubuntu.")

        dialog.connect("response", on_response)
        dialog.present()

    def _on_about_clicked(self, button: Gtk.Button):
        dialog = Adw.AboutDialog.new()
        dialog.set_application_name("DockCraft")
        dialog.set_application_icon("preferences-desktop-theme-symbolic")
        dialog.set_version("1.0.0")
        dialog.set_developer_name("DockCraft Team")
        dialog.set_comments("Personalizador visual e de usabilidade para o dock do Ubuntu.")
        dialog.set_website("https://github.com/drianodev/dock-ubuntu")
        dialog.set_license_type(Gtk.License.MIT_X11)
        dialog.present(self)
