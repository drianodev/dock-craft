"""
Appearance and Design page for DockCraft.
"""

from typing import Callable
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, GLib
from ..backend import DockBackend


class AppearancePage(Adw.PreferencesPage):
    def __init__(self, backend: DockBackend, on_notify: Callable[[str], None]):
        super().__init__()
        self.backend = backend
        self.on_notify = on_notify
        self._updating = False

        self.set_title("Aparência e Design")
        self.set_icon_name("preferences-desktop-theme-symbolic")

        # 1. Layout e Posicionamento
        self._build_layout_group()

        # 2. Tamanho e Ícones
        self._build_icons_group()

        # 3. Cores e Transparência
        self._build_colors_group()

        # Register listeners to sync UI when backend changes
        for key in ['dock-position', 'extend-height', 'always-center-icons', 'custom-theme-shrink',
                    'dash-max-icon-size', 'show-favorites', 'show-running', 'show-trash', 'show-mounts', 'show-show-apps-button',
                    'show-apps-at-top', 'transparency-mode', 'background-opacity',
                    'custom-background-color', 'background-color', 'running-indicator-style',
                    'running-indicator-dominant-color']:
            self.backend.add_change_listener(key, lambda k, v: GLib.idle_add(self._sync_ui_from_backend))

        self._sync_ui_from_backend()

    def _add_icon(self, row, icon_name: str):
        img = Gtk.Image.new_from_icon_name(icon_name)
        row.add_prefix(img)

    def _build_layout_group(self):
        group = Adw.PreferencesGroup()
        group.set_title("Layout e Posicionamento")
        group.set_description("Defina o formato e a localização do dock na tela.")
        self.add(group)

        # Posição na Tela
        self.pos_row = Adw.ComboRow()
        self.pos_row.set_title("Posição na Tela")
        self.pos_row.set_subtitle("Escolha em qual borda da área de trabalho o dock se posiciona.")
        self._add_icon(self.pos_row, "preferences-desktop-display-symbolic")
        self.pos_keys = ['BOTTOM', 'LEFT', 'RIGHT', 'TOP']
        pos_names = ['Inferior (Base)', 'Esquerda (Padrão Ubuntu)', 'Direita', 'Superior (Topo)']
        self.pos_row.set_model(Gtk.StringList.new(pos_names))
        self.pos_row.connect("notify::selected", self._on_pos_changed)
        group.add(self.pos_row)

        # Modo Ilha Flutuante (Floating Pill Dock)
        self.floating_row = Adw.SwitchRow()
        self.floating_row.set_title("Modo Ilha Flutuante (Floating Dock)")
        self.floating_row.set_subtitle("Transforma a barra em uma ilha flutuante com cantos arredondados (estilo macOS).")
        self._add_icon(self.floating_row, "view-paged-symbolic")
        self.floating_row.connect("notify::active", self._on_floating_changed)
        group.add(self.floating_row)

        # Centralizar Ícones
        self.center_row = Adw.SwitchRow()
        self.center_row.set_title("Centralizar Ícones")
        self.center_row.set_subtitle("Posiciona os ícones centralizados em vez de alinhados à esquerda ou topo.")
        self._add_icon(self.center_row, "format-justify-center-symbolic")
        self.center_row.connect("notify::active", self._on_center_changed)
        group.add(self.center_row)

        # Ícones Compactos (Shrink)
        self.shrink_row = Adw.SwitchRow()
        self.shrink_row.set_title("Espaçamento Compacto")
        self.shrink_row.set_subtitle("Reduz o espaçamento e margens entre os ícones para um dock mais fino.")
        self._add_icon(self.shrink_row, "zoom-fit-best-symbolic")
        self.shrink_row.connect("notify::active", self._on_shrink_changed)
        group.add(self.shrink_row)

    def _build_icons_group(self):
        group = Adw.PreferencesGroup()
        group.set_title("Ícones e Elementos")
        group.set_description("Dimensões dos ícones e visibilidade de itens especiais.")
        self.add(group)

        # Tamanho dos Ícones (Slider)
        self.size_row = Adw.ActionRow()
        self.size_row.set_title("Tamanho dos Ícones")
        self.size_row.set_subtitle("48px")
        self._add_icon(self.size_row, "preferences-desktop-icons-symbolic")

        self.size_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 16, 96, 2)
        self.size_scale.set_size_request(200, -1)
        self.size_scale.set_valign(Gtk.Align.CENTER)
        self.size_scale.set_draw_value(False)
        self.size_scale.connect("value-changed", self._on_size_changed)
        self.size_row.add_suffix(self.size_scale)
        group.add(self.size_row)

        # Exibir Aplicativos Fixados
        self.favorites_row = Adw.SwitchRow()
        self.favorites_row.set_title("Exibir Aplicativos Fixados (Favoritos)")
        self.favorites_row.set_subtitle("Mostra os ícones dos aplicativos fixados na barra do dock.")
        self._add_icon(self.favorites_row, "starred-symbolic")
        self.favorites_row.connect("notify::active", lambda w, p: self._set_backend_bool('show-favorites', w.get_active()))
        group.add(self.favorites_row)

        # Exibir Aplicativos em Execução
        self.running_row = Adw.SwitchRow()
        self.running_row.set_title("Exibir Aplicativos em Execução (Abertos)")
        self.running_row.set_subtitle("Adiciona automaticamente ao dock os aplicativos abertos, mesmo que não estejam fixados.")
        self._add_icon(self.running_row, "media-playback-start-symbolic")
        self.running_row.connect("notify::active", lambda w, p: self._set_backend_bool('show-running', w.get_active()))
        group.add(self.running_row)

        # Exibir Lixeira
        self.trash_row = Adw.SwitchRow()
        self.trash_row.set_title("Exibir Lixeira no Dock")
        self.trash_row.set_subtitle("Mostra o atalho de lixeira no dock.")
        self._add_icon(self.trash_row, "user-trash-symbolic")
        self.trash_row.connect("notify::active", lambda w, p: self._set_backend_bool('show-trash', w.get_active()))
        group.add(self.trash_row)

        # Exibir Discos Montados
        self.mounts_row = Adw.SwitchRow()
        self.mounts_row.set_title("Exibir Discos e Pen Drives")
        self.mounts_row.set_subtitle("Mostra volumes de armazenamento e dispositivos USB conectados.")
        self._add_icon(self.mounts_row, "drive-removable-media-symbolic")
        self.mounts_row.connect("notify::active", lambda w, p: self._set_backend_bool('show-mounts', w.get_active()))
        group.add(self.mounts_row)

        # Botão Mostrar Aplicativos
        self.show_apps_row = Adw.SwitchRow()
        self.show_apps_row.set_title("Exibir Botão 'Mostrar Aplicativos'")
        self.show_apps_row.set_subtitle("Mostra o botão de grade para abrir o lançador de aplicativos.")
        self._add_icon(self.show_apps_row, "view-app-grid-symbolic")
        self.show_apps_row.connect("notify::active", lambda w, p: self._set_backend_bool('show-show-apps-button', w.get_active()))
        group.add(self.show_apps_row)

        # Botão Apps no Topo/Início
        self.apps_top_row = Adw.SwitchRow()
        self.apps_top_row.set_title("Botão de Aplicativos no Início/Topo")
        self.apps_top_row.set_subtitle("Posiciona a grade de aplicativos antes de todos os ícones.")
        self._add_icon(self.apps_top_row, "go-up-symbolic")
        self.apps_top_row.connect("notify::active", lambda w, p: self._set_backend_bool('show-apps-at-top', w.get_active()))
        group.add(self.apps_top_row)

    def _build_colors_group(self):
        group = Adw.PreferencesGroup()
        group.set_title("Cores e Indicadores")
        group.set_description("Personalize transparência, cores de fundo e marcadores de status.")
        self.add(group)

        # Modo de Transparência
        self.trans_row = Adw.ComboRow()
        self.trans_row.set_title("Modo de Transparência")
        self.trans_row.set_subtitle("Padrão do tema, Fixo com opacidade customizada ou Dinâmico.")
        self._add_icon(self.trans_row, "display-projector-symbolic")
        self.trans_keys = ['DEFAULT', 'FIXED', 'DYNAMIC']
        trans_names = ['Padrão do Sistema', 'Fixo (Opacidade Customizada)', 'Dinâmico (Translúcido / Sólido)']
        self.trans_row.set_model(Gtk.StringList.new(trans_names))
        self.trans_row.connect("notify::selected", self._on_trans_changed)
        group.add(self.trans_row)

        # Opacidade do Fundo
        self.opacity_row = Adw.ActionRow()
        self.opacity_row.set_title("Opacidade do Fundo")
        self.opacity_row.set_subtitle("80%")
        self._add_icon(self.opacity_row, "color-select-symbolic")

        self.opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 1.0, 0.05)
        self.opacity_scale.set_size_request(200, -1)
        self.opacity_scale.set_valign(Gtk.Align.CENTER)
        self.opacity_scale.set_draw_value(False)
        self.opacity_scale.connect("value-changed", self._on_opacity_changed)
        self.opacity_row.add_suffix(self.opacity_scale)
        group.add(self.opacity_row)

        # Cor de Fundo Personalizada
        self.custom_color_row = Adw.SwitchRow()
        self.custom_color_row.set_title("Usar Cor de Fundo Personalizada")
        self.custom_color_row.set_subtitle("Substitui a cor escura padrão do Ubuntu Dock.")
        self._add_icon(self.custom_color_row, "applications-graphics-symbolic")
        self.custom_color_row.connect("notify::active", self._on_custom_color_toggled)
        group.add(self.custom_color_row)

        # Seletor de Cor
        self.color_picker_row = Adw.ActionRow()
        self.color_picker_row.set_title("Cor de Fundo")
        self.color_picker_row.set_subtitle("Escolha a cor primária do dock.")
        self.color_dialog = Gtk.ColorDialog()
        self.color_btn = Gtk.ColorDialogButton(dialog=self.color_dialog)
        self.color_btn.set_valign(Gtk.Align.CENTER)
        self.color_btn.connect("notify::rgba", self._on_color_picked)
        self.color_picker_row.add_suffix(self.color_btn)
        group.add(self.color_picker_row)

        # Estilo do Indicador de Apps
        self.indicator_row = Adw.ComboRow()
        self.indicator_row.set_title("Estilo do Indicador de Apps")
        self.indicator_row.set_subtitle("Marcador visual abaixo dos aplicativos em execução.")
        self._add_icon(self.indicator_row, "media-record-symbolic")
        self.indicator_keys = ['DOTS', 'DASHES', 'SQUARES', 'SEGMENTED', 'CILIORA']
        indicator_names = [
            'Pontos (DOTS - Clássico)',
            'Barras / Traços (DASHES - Estilo Windows/Moderno)',
            'Quadrados (SQUARES)',
            'Segmentado (SEGMENTED)',
            'Ciliora (CILIORA)'
        ]
        self.indicator_row.set_model(Gtk.StringList.new(indicator_names))
        self.indicator_row.connect("notify::selected", self._on_indicator_changed)
        group.add(self.indicator_row)

        # Indicador com Cor Dominante do App
        self.dominant_color_row = Adw.SwitchRow()
        self.dominant_color_row.set_title("Indicador com Cor do Ícone")
        self.dominant_color_row.set_subtitle("O marcador assume a cor predominante do ícone de cada app.")
        self._add_icon(self.dominant_color_row, "color-gradient-symbolic")
        self.dominant_color_row.connect("notify::active", lambda w, p: self._set_backend_bool('running-indicator-dominant-color', w.get_active()))
        group.add(self.dominant_color_row)

    def _sync_ui_from_backend(self):
        if self._updating:
            return False
        self._updating = True
        try:
            # Pos
            pos = self.backend.get_value('dock-position')
            if pos in self.pos_keys:
                self.pos_row.set_selected(self.pos_keys.index(pos))

            # Floating (extend-height = false is floating)
            extend = self.backend.get_value('extend-height')
            self.floating_row.set_active(not extend)

            # Center
            center = self.backend.get_value('always-center-icons')
            self.center_row.set_active(center)

            # Shrink
            shrink = self.backend.get_value('custom-theme-shrink')
            self.shrink_row.set_active(shrink)

            # Icon size
            size = self.backend.get_value('dash-max-icon-size')
            self.size_scale.set_value(size)
            self.size_row.set_subtitle(f"{int(size)}px")

            # Toggles
            self.favorites_row.set_active(self.backend.get_value('show-favorites'))
            self.running_row.set_active(self.backend.get_value('show-running'))
            self.trash_row.set_active(self.backend.get_value('show-trash'))
            self.mounts_row.set_active(self.backend.get_value('show-mounts'))
            self.show_apps_row.set_active(self.backend.get_value('show-show-apps-button'))
            self.apps_top_row.set_active(self.backend.get_value('show-apps-at-top'))

            # Transparency
            trans = self.backend.get_value('transparency-mode')
            if trans in self.trans_keys:
                self.trans_row.set_selected(self.trans_keys.index(trans))

            # Opacity
            opacity = self.backend.get_value('background-opacity')
            self.opacity_scale.set_value(opacity)
            self.opacity_row.set_subtitle(f"{int(opacity * 100)}%")

            # Custom color
            custom_bg = self.backend.get_value('custom-background-color')
            self.custom_color_row.set_active(custom_bg)
            self.color_picker_row.set_sensitive(custom_bg)

            hex_color = self.backend.get_value('background-color')
            rgba = Gdk.RGBA()
            if rgba.parse(hex_color):
                self.color_btn.set_rgba(rgba)

            # Indicators
            ind = self.backend.get_value('running-indicator-style')
            if ind in self.indicator_keys:
                self.indicator_row.set_selected(self.indicator_keys.index(ind))

            self.dominant_color_row.set_active(self.backend.get_value('running-indicator-dominant-color'))

        except Exception as e:
            print(f"Error syncing UI: {e}")
        finally:
            self._updating = False
        return False

    def _set_backend_bool(self, key: str, value: bool):
        if not self._updating:
            self.backend.set_value(key, value)

    def _on_pos_changed(self, row, param):
        if self._updating:
            return
        idx = row.get_selected()
        if 0 <= idx < len(self.pos_keys):
            self.backend.set_value('dock-position', self.pos_keys[idx])

    def _on_floating_changed(self, row, param):
        if self._updating:
            return
        # Floating ON means extend-height is False
        self.backend.set_value('extend-height', not row.get_active())

    def _on_center_changed(self, row, param):
        if self._updating:
            return
        self.backend.set_value('always-center-icons', row.get_active())

    def _on_shrink_changed(self, row, param):
        if self._updating:
            return
        self.backend.set_value('custom-theme-shrink', row.get_active())

    def _on_size_changed(self, scale):
        val = int(scale.get_value())
        self.size_row.set_subtitle(f"{val}px")
        if not self._updating:
            self.backend.set_value('dash-max-icon-size', val)

    def _on_trans_changed(self, row, param):
        if self._updating:
            return
        idx = row.get_selected()
        if 0 <= idx < len(self.trans_keys):
            self.backend.set_value('transparency-mode', self.trans_keys[idx])

    def _on_opacity_changed(self, scale):
        val = scale.get_value()
        self.opacity_row.set_subtitle(f"{int(val * 100)}%")
        if not self._updating:
            self.backend.set_value('background-opacity', val)

    def _on_custom_color_toggled(self, row, param):
        active = row.get_active()
        self.color_picker_row.set_sensitive(active)
        if not self._updating:
            self.backend.set_value('custom-background-color', active)

    def _on_color_picked(self, btn, param):
        if self._updating:
            return
        rgba = btn.get_rgba()
        r = int(rgba.red * 255)
        g = int(rgba.green * 255)
        b = int(rgba.blue * 255)
        hex_str = f"#{r:02x}{g:02x}{b:02x}"
        self.backend.set_value('background-color', hex_str)

    def _on_indicator_changed(self, row, param):
        if self._updating:
            return
        idx = row.get_selected()
        if 0 <= idx < len(self.indicator_keys):
            self.backend.set_value('running-indicator-style', self.indicator_keys[idx])
