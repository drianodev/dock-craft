"""
Ultra-modern live interactive miniature preview of the Ubuntu desktop and dock.
Supports adaptive layout (Left side by default, Top on small screens),
themes, collapsing, hover effects and desktop window simulations.
"""

from typing import List, Tuple
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, Gio, GLib
from ..backend import DockBackend


class DockPreviewWidget(Gtk.Box):
    def __init__(self, backend: DockBackend):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.backend = backend
        self._is_collapsed = False
        self.mode = 'side'

        self.set_margin_top(10)
        self.set_margin_bottom(12)
        self.set_margin_start(14)
        self.set_margin_end(14)

        # Header with Title, Status Badges, and Collapse/Expand Button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.append(header_box)

        # Title with live pulsing indicator dot
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_box.set_halign(Gtk.Align.START)
        title_box.set_hexpand(True)

        live_dot = Gtk.Box()
        live_dot.set_size_request(8, 8)
        live_dot.add_css_class("dockcraft-live-pulse")
        live_dot.set_valign(Gtk.Align.CENTER)
        title_box.append(live_dot)

        title = Gtk.Label(label="Pré-visualização")
        title.add_css_class("heading")
        title_box.append(title)

        self.status_badge = Gtk.Label()
        self.status_badge.add_css_class("caption")
        self.status_badge.add_css_class("dim-label")
        title_box.append(self.status_badge)

        header_box.append(title_box)

        # Collapse / Expand Button (for compact top mode)
        self.toggle_btn = Gtk.Button.new_from_icon_name("pan-up-symbolic")
        self.toggle_btn.set_tooltip_text("Recolher / Expandir Pré-visualização")
        self.toggle_btn.add_css_class("flat")
        self.toggle_btn.add_css_class("circular")
        self.toggle_btn.connect("clicked", self._on_toggle_collapse)
        self.toggle_btn.set_visible(False)
        header_box.append(self.toggle_btn)

        # Mock Screen Container
        self.screen_frame = Gtk.Frame()
        self.screen_frame.add_css_class("card")
        self.screen_frame.set_size_request(-1, 185)
        self.screen_frame.set_hexpand(True)

        self.screen_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.screen_box.add_css_class("dockcraft-screen-mock")
        self.screen_box.set_hexpand(True)
        self.screen_box.set_vexpand(True)
        self.screen_frame.set_child(self.screen_box)
        self.append(self.screen_frame)

        # GNOME Top Bar simulation
        self.top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.top_bar.add_css_class("dockcraft-top-bar")
        self.top_bar.set_size_request(-1, 20)

        act_label = Gtk.Label(label="Atividades")
        act_label.add_css_class("dockcraft-top-label")
        act_label.set_halign(Gtk.Align.START)
        self.top_bar.append(act_label)

        clock_label = Gtk.Label(label="17:00")
        clock_label.add_css_class("dockcraft-top-label")
        clock_label.set_hexpand(True)
        clock_label.set_halign(Gtk.Align.CENTER)
        self.top_bar.append(clock_label)

        tray_box = Gtk.Box(spacing=6)
        tray_box.set_halign(Gtk.Align.END)
        for sym in ["network-wireless-symbolic", "audio-volume-high-symbolic", "system-shutdown-symbolic"]:
            img = Gtk.Image.new_from_icon_name(sym)
            img.set_pixel_size(10)
            img.add_css_class("dockcraft-top-icon")
            tray_box.append(img)
        self.top_bar.append(tray_box)

        self.screen_box.append(self.top_bar)

        # Wallpaper & Desktop Area
        self.desktop_area = Gtk.Overlay()
        self.desktop_area.set_vexpand(True)
        self.desktop_area.set_hexpand(True)

        # Mock Floating Window Silhouette on Desktop
        self.mock_window = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.mock_window.add_css_class("dockcraft-mock-window")
        self.mock_window.set_size_request(130, 70)
        self.mock_window.set_halign(Gtk.Align.CENTER)
        self.mock_window.set_valign(Gtk.Align.CENTER)

        # Mini window titlebar dots
        win_titlebar = Gtk.Box(spacing=4)
        win_titlebar.set_margin_start(6)
        win_titlebar.set_margin_top(4)
        for c in ["#ff5f56", "#ffbd2e", "#27c93f"]:
            dot = Gtk.Box()
            dot.set_size_request(5, 5)
            dot.add_css_class("dockcraft-win-dot")
            win_titlebar.append(dot)
        self.mock_window.append(win_titlebar)

        self.desktop_area.set_child(self.mock_window)
        self.screen_box.append(self.desktop_area)

        # Dock Layer (overlayed onto the desktop)
        self.dock_layout = Gtk.Box()
        self.dock_layout.set_vexpand(True)
        self.dock_layout.set_hexpand(True)

        self.dock_container = Gtk.Box()
        self.dock_bar = Gtk.Box(spacing=6)
        self.dock_bar.add_css_class("dockcraft-dock-bar")
        self.dock_container.append(self.dock_bar)
        self.dock_layout.append(self.dock_container)

        self.desktop_area.add_overlay(self.dock_layout)

        # Info Box (visible in Side Mode on the left panel)
        self.info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.info_box.set_margin_top(4)

        info_frame = Gtk.Frame()
        info_frame.add_css_class("card")
        info_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        info_inner.set_margin_top(10)
        info_inner.set_margin_bottom(10)
        info_inner.set_margin_start(12)
        info_inner.set_margin_end(12)

        info_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        summary_icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic")
        summary_icon.set_pixel_size(14)
        info_header.append(summary_icon)

        info_title = Gtk.Label(label="Estado do Dock")
        info_title.add_css_class("heading")
        info_title.set_halign(Gtk.Align.START)
        info_header.append(info_title)
        info_inner.append(info_header)

        self.info_pos_label = Gtk.Label()
        self.info_pos_label.add_css_class("caption")
        self.info_pos_label.set_halign(Gtk.Align.START)
        info_inner.append(self.info_pos_label)

        self.info_mode_label = Gtk.Label()
        self.info_mode_label.add_css_class("caption")
        self.info_mode_label.set_halign(Gtk.Align.START)
        info_inner.append(self.info_mode_label)

        self.info_size_label = Gtk.Label()
        self.info_size_label.add_css_class("caption")
        self.info_size_label.set_halign(Gtk.Align.START)
        info_inner.append(self.info_size_label)

        self.info_trans_label = Gtk.Label()
        self.info_trans_label.add_css_class("caption")
        self.info_trans_label.set_halign(Gtk.Align.START)
        info_inner.append(self.info_trans_label)

        info_frame.set_child(info_inner)
        self.info_box.append(info_frame)
        self.append(self.info_box)

        # Dynamic CSS Provider
        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.set_mode('side')
        self.update_preview()

        # Listen to backend changes
        for key in ['dock-position', 'extend-height', 'dash-max-icon-size',
                    'always-center-icons', 'transparency-mode', 'background-opacity',
                    'custom-background-color', 'background-color', 'running-indicator-style',
                    'custom-theme-customize-running-dots', 'custom-theme-running-dots-color',
                    'show-favorites', 'show-running', 'show-trash', 'show-mounts', 'show-show-apps-button',
                    'show-apps-at-top', 'custom-theme-shrink']:
            self.backend.add_change_listener(key, lambda k, v: GLib.idle_add(self.update_preview))

    def set_mode(self, mode: str):
        """Switches between 'side' (left panel) and 'top' (compact top bar) layout."""
        self.mode = mode
        if mode == 'side':
            self.set_size_request(330, -1)
            self.set_hexpand(False)
            self.set_vexpand(True)
            self.screen_frame.set_size_request(-1, 185)
            self.info_box.set_visible(True)
            self.toggle_btn.set_visible(False)
            self.status_badge.set_visible(False)
        else:  # top
            self.set_size_request(-1, -1)
            self.set_hexpand(True)
            self.set_vexpand(False)
            self.screen_frame.set_size_request(-1, 140)
            self.info_box.set_visible(False)
            self.toggle_btn.set_visible(True)
            self.status_badge.set_visible(True)
        self.update_preview()

    def _on_toggle_collapse(self, button: Gtk.Button):
        self._is_collapsed = not self._is_collapsed
        self.screen_frame.set_visible(not self._is_collapsed)
        if self._is_collapsed:
            self.toggle_btn.set_icon_name("pan-down-symbolic")
            self.toggle_btn.set_tooltip_text("Expandir Pré-visualização")
        else:
            self.toggle_btn.set_icon_name("pan-up-symbolic")
            self.toggle_btn.set_tooltip_text("Recolher Pré-visualização")

    def _get_preview_icons(self) -> List[Tuple[str, bool]]:
        icons = []
        show_apps = self.backend.get_value('show-show-apps-button')
        apps_at_top = self.backend.get_value('show-apps-at-top')
        show_favs = self.backend.get_value('show-favorites')
        show_trash = self.backend.get_value('show-trash')
        show_mounts = self.backend.get_value('show-mounts')

        if show_apps and apps_at_top:
            icons.append(("view-app-grid-symbolic", False))

        if show_favs:
            user_favs = self.backend.get_favorite_apps()
            loaded = 0
            for desktop_id in user_favs:
                if loaded >= 7:
                    break
                app_info = Gio.DesktopAppInfo.new(desktop_id)
                if app_info:
                    icon_obj = app_info.get_icon()
                    icon_name = icon_obj.to_string() if icon_obj else "application-x-executable"
                    icons.append((icon_name, loaded % 2 == 0))
                    loaded += 1

            if loaded == 0:
                icons.extend([
                    ("system-file-manager", True),
                    ("web-browser", True),
                    ("utilities-terminal", False),
                    ("org.gnome.Settings", False)
                ])

        if show_mounts:
            icons.append(("drive-removable-media-symbolic", False))

        if show_trash:
            icons.append(("user-trash-symbolic", False))

        if show_apps and not apps_at_top:
            icons.append(("view-app-grid-symbolic", False))

        return icons

    def update_preview(self):
        pos = self.backend.get_value('dock-position')
        extend_height = self.backend.get_value('extend-height')
        center_icons = self.backend.get_value('always-center-icons')
        bg_opacity = self.backend.get_value('background-opacity')
        custom_bg = self.backend.get_value('custom-background-color')
        bg_color = self.backend.get_value('background-color') if custom_bg else "#1e1e24"
        indicator_style = self.backend.get_value('running-indicator-style')
        icon_size = self.backend.get_value('dash-max-icon-size')

        custom_dots = self.backend.get_value('custom-theme-customize-running-dots')
        if custom_dots:
            dot_color = self.backend.get_value('custom-theme-running-dots-color')
        else:
            dot_color = "#3584e4"

        pos_label = {
            'BOTTOM': 'Inferior (Base)',
            'LEFT': 'Lateral Esquerda',
            'RIGHT': 'Lateral Direita',
            'TOP': 'Superior (Topo)'
        }.get(pos, pos)
        mode_label = 'Barra Expandida' if extend_height else 'Ilha Flutuante'

        self.status_badge.set_text(f"• {pos_label} • {mode_label} • {int(icon_size)}px")

        # Update Summary Labels in Info Box
        self.info_pos_label.set_text(f"• Posição: {pos_label}")
        self.info_mode_label.set_text(f"• Formato: {mode_label}")
        self.info_size_label.set_text(f"• Ícones: {int(icon_size)}px (Centro: {'Sim' if center_icons else 'Não'})")
        self.info_trans_label.set_text(f"• Opacidade: {int(bg_opacity * 100)}% (Fundo: {bg_color})")

        # Re-populate dock icons
        child = self.dock_bar.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.dock_bar.remove(child)
            child = next_child

        icons = self._get_preview_icons()
        is_vertical = pos in ['LEFT', 'RIGHT']

        for icon_name, is_running in icons:
            item_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL if not is_vertical else Gtk.Orientation.HORIZONTAL,
                spacing=2
            )
            item_box.set_halign(Gtk.Align.CENTER)
            item_box.set_valign(Gtk.Align.CENTER)
            item_box.add_css_class("dockcraft-mock-item")

            img = Gtk.Image.new_from_icon_name(icon_name)
            img.set_pixel_size(18 if self.mode == 'side' else 20)
            img.add_css_class("dockcraft-mock-icon")
            item_box.append(img)

            if is_running:
                dot = Gtk.Box()
                dot.add_css_class("dockcraft-mock-dot")
                dot.set_halign(Gtk.Align.CENTER)
                dot.set_valign(Gtk.Align.CENTER)
                item_box.append(dot)
            else:
                spacer = Gtk.Box()
                if not is_vertical:
                    spacer.set_size_request(-1, 3)
                else:
                    spacer.set_size_request(3, -1)
                item_box.append(spacer)

            self.dock_bar.append(item_box)

        # Dock position layout
        if pos == 'LEFT':
            self.dock_layout.set_orientation(Gtk.Orientation.HORIZONTAL)
            self.dock_bar.set_orientation(Gtk.Orientation.VERTICAL)
            self.dock_container.set_orientation(Gtk.Orientation.VERTICAL)
            self.dock_container.set_halign(Gtk.Align.START)
            self.dock_container.set_hexpand(False)
            self.dock_container.set_vexpand(True)
            self.dock_container.set_valign(Gtk.Align.FILL if extend_height else (Gtk.Align.CENTER if center_icons else Gtk.Align.START))
        elif pos == 'RIGHT':
            self.dock_layout.set_orientation(Gtk.Orientation.HORIZONTAL)
            self.dock_bar.set_orientation(Gtk.Orientation.VERTICAL)
            self.dock_container.set_orientation(Gtk.Orientation.VERTICAL)
            self.dock_container.set_halign(Gtk.Align.END)
            self.dock_container.set_hexpand(True)
            self.dock_container.set_vexpand(True)
            self.dock_container.set_valign(Gtk.Align.FILL if extend_height else (Gtk.Align.CENTER if center_icons else Gtk.Align.START))
        elif pos == 'TOP':
            self.dock_layout.set_orientation(Gtk.Orientation.VERTICAL)
            self.dock_bar.set_orientation(Gtk.Orientation.HORIZONTAL)
            self.dock_container.set_orientation(Gtk.Orientation.HORIZONTAL)
            self.dock_container.set_valign(Gtk.Align.START)
            self.dock_container.set_vexpand(False)
            self.dock_container.set_hexpand(True)
            self.dock_container.set_halign(Gtk.Align.FILL if extend_height else (Gtk.Align.CENTER if center_icons else Gtk.Align.START))
        else:  # BOTTOM
            self.dock_layout.set_orientation(Gtk.Orientation.VERTICAL)
            self.dock_bar.set_orientation(Gtk.Orientation.HORIZONTAL)
            self.dock_container.set_orientation(Gtk.Orientation.HORIZONTAL)
            self.dock_container.set_valign(Gtk.Align.END)
            self.dock_container.set_vexpand(True)
            self.dock_container.set_hexpand(True)
            self.dock_container.set_halign(Gtk.Align.FILL if extend_height else (Gtk.Align.CENTER if center_icons else Gtk.Align.START))

        # Dynamic CSS
        pill_radius = "0px" if extend_height else "16px"
        pill_margin = "0px" if extend_height else "6px"

        hex_clean = bg_color.lstrip('#')
        if len(hex_clean) == 6:
            r = int(hex_clean[0:2], 16)
            g = int(hex_clean[2:4], 16)
            b = int(hex_clean[4:6], 16)
            rgba = f"rgba({r}, {g}, {b}, {bg_opacity})"
        else:
            rgba = f"rgba(30, 30, 36, {bg_opacity})"

        is_bar = indicator_style in ["METRO", "DASHES"]
        dot_radius = "1px" if is_bar else "50%"
        dot_width = "12px" if is_bar else "4px"
        dot_height = "2px" if is_bar else "4px"

        css = f"""
        .dockcraft-screen-mock {{
            background: radial-gradient(circle at 40% 20%, #4a1f6d 0%, #170d2b 70%, #0c0817 100%);
            border-radius: 12px;
            padding: 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .dockcraft-top-bar {{
            background-color: rgba(12, 10, 18, 0.90);
            padding: 2px 10px;
            border-top-left-radius: 11px;
            border-top-right-radius: 11px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .dockcraft-top-label {{
            font-size: 8px;
            font-weight: bold;
            color: rgba(255, 255, 255, 0.9);
        }}
        .dockcraft-top-icon {{
            color: rgba(255, 255, 255, 0.7);
        }}
        .dockcraft-mock-window {{
            background: rgba(30, 30, 42, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 8px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        }}
        .dockcraft-win-dot {{
            border-radius: 50%;
            background-color: rgba(255, 255, 255, 0.25);
        }}
        .dockcraft-dock-bar {{
            background-color: {rgba};
            border-radius: {pill_radius};
            margin: {pill_margin};
            padding: 4px 10px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.55);
            border: 1px solid rgba(255, 255, 255, 0.18);
            transition: all 200ms ease;
        }}
        .dockcraft-mock-dot {{
            background-color: {dot_color};
            border-radius: {dot_radius};
            min-width: {dot_width};
            min-height: {dot_height};
        }}
        .dockcraft-mock-icon {{
            color: #ffffff;
        }}
        .dockcraft-live-pulse {{
            background-color: #2ec27e;
            border-radius: 50%;
        }}
        """
        if hasattr(self.css_provider, 'load_from_string'):
            self.css_provider.load_from_string(css)
        else:
            self.css_provider.load_from_data(css.encode('utf-8'))
        return False
