"""
Behavior and Usability page for DockCraft.
"""

from typing import Callable
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from ..backend import DockBackend


class BehaviorPage(Adw.PreferencesPage):
    def __init__(self, backend: DockBackend, on_notify: Callable[[str], None]):
        super().__init__()
        self.backend = backend
        self.on_notify = on_notify
        self._updating = False

        self.set_title("Usabilidade & Comportamento")
        self.set_icon_name("input-mouse-symbolic")

        # 1. Ações do Mouse e Janelas
        self._build_mouse_group()

        # 2. Ocultamento Automático
        self._build_autohide_group()

        # 3. Monitores e Áreas de Trabalho
        self._build_workspaces_group()

        # Register listeners to sync UI when backend changes
        for key in ['click-action', 'scroll-action', 'scroll-switch-workspace', 'scroll-to-focused-application',
                    'autohide', 'intellihide', 'isolate-monitors', 'isolate-workspaces', 'multi-monitor']:
            self.backend.add_change_listener(key, lambda k, v: GLib.idle_add(self._sync_ui_from_backend))

        self._sync_ui_from_backend()

    def _add_icon(self, row, icon_name: str):
        img = Gtk.Image.new_from_icon_name(icon_name)
        row.add_prefix(img)

    def _build_mouse_group(self):
        group = Adw.PreferencesGroup()
        group.set_title("Ações do Mouse e Cliques")
        group.set_description("Configure o que acontece ao interagir com os ícones de aplicativos.")
        self.add(group)

        # Ação ao Clicar no Ícone
        self.click_row = Adw.ComboRow()
        self.click_row.set_title("Ação ao Clicar no Aplicativo")
        self.click_row.set_subtitle("Permite minimizar a janela com 1 clique (comportamento tipo Windows/macOS).")
        self._add_icon(self.click_row, "input-mouse-symbolic")
        
        self.click_keys = [
            'focus-minimize-or-previews',
            'minimize-or-previews',
            'cycle-windows',
            'focus-or-appspread',
            'minimize',
            'launch'
        ]
        click_names = [
            'Focar / Minimizar / Mostrar Miniaturas (Recomendado)',
            'Minimizar ou Pré-visualizar Janelas',
            'Alternar Entre Janelas Abertas (Cycle)',
            'Focar ou Espalhar Janelas (Padrão Ubuntu)',
            'Apenas Minimizar Janela',
            'Abrir Nova Instância do App'
        ]
        self.click_row.set_model(Gtk.StringList.new(click_names))
        self.click_row.connect("notify::selected", self._on_click_changed)
        group.add(self.click_row)

        # Ação ao Usar Scroll do Mouse
        self.scroll_row = Adw.ComboRow()
        self.scroll_row.set_title("Ação ao Rolar o Scroll do Mouse")
        self.scroll_row.set_subtitle("Comportamento ao girar a rodinha do mouse sobre um ícone do dock.")
        self._add_icon(self.scroll_row, "input-mouse-scroll-symbolic")

        self.scroll_keys = ['cycle-windows', 'switch-workspace', 'do-nothing']
        scroll_names = [
            'Alternar Entre Janelas Abertas do App (Cycle - Recomendado)',
            'Mudar de Área de Trabalho (Workspace)',
            'Não Fazer Nada (Desativado)'
        ]
        self.scroll_row.set_model(Gtk.StringList.new(scroll_names))
        self.scroll_row.connect("notify::selected", self._on_scroll_changed)
        group.add(self.scroll_row)

        # Mudar Workspace ao rolar na barra
        self.scroll_workspace_row = Adw.SwitchRow()
        self.scroll_workspace_row.set_title("Mudar Área de Trabalho ao Rolar na Barra")
        self.scroll_workspace_row.set_subtitle("Girar o scroll sobre espaços vazios do dock alterna entre as áreas de trabalho.")
        self._add_icon(self.scroll_workspace_row, "preferences-desktop-workspaces-symbolic")
        self.scroll_workspace_row.connect("notify::active", lambda w, p: self._set_backend_bool('scroll-switch-workspace', w.get_active()))
        group.add(self.scroll_workspace_row)

        # Focar janela ao rolar
        self.scroll_focus_row = Adw.SwitchRow()
        self.scroll_focus_row.set_title("Focar Automaticamente na Janela ao Rolar")
        self.scroll_focus_row.set_subtitle("Traz a janela do aplicativo diretamente para o primeiro plano ao girar o scroll.")
        self._add_icon(self.scroll_focus_row, "window-new-symbolic")
        self.scroll_focus_row.connect("notify::active", lambda w, p: self._set_backend_bool('scroll-to-focused-application', w.get_active()))
        group.add(self.scroll_focus_row)

    def _build_autohide_group(self):
        group = Adw.PreferencesGroup()
        group.set_title("Ocultamento do Dock")
        group.set_description("Comportamento do dock quando janelas estão abertas ou maximizadas.")
        self.add(group)

        # Autohide
        self.autohide_row = Adw.SwitchRow()
        self.autohide_row.set_title("Ocultar Automaticamente (Autohide)")
        self.autohide_row.set_subtitle("O dock fica oculto até o cursor do mouse tocar a borda da tela.")
        self._add_icon(self.autohide_row, "window-minimize-symbolic")
        self.autohide_row.connect("notify::active", self._on_autohide_changed)
        group.add(self.autohide_row)

        # Intellihide
        self.intellihide_row = Adw.SwitchRow()
        self.intellihide_row.set_title("Ocultamento Inteligente (Intellihide)")
        self.intellihide_row.set_subtitle("Oculta o dock somente se alguma janela ocupar ou cobrir o espaço dele.")
        self._add_icon(self.intellihide_row, "window-pop-out-symbolic")
        self.intellihide_row.connect("notify::active", self._on_intellihide_changed)
        group.add(self.intellihide_row)

    def _build_workspaces_group(self):
        group = Adw.PreferencesGroup()
        group.set_title("Multitarefas e Monitores")
        group.set_description("Filtros para quem utiliza múltiplos monitores ou vários espaços de trabalho.")
        self.add(group)

        # Isolar Monitores
        self.isolate_monitors_row = Adw.SwitchRow()
        self.isolate_monitors_row.set_title("Isolar Monitores")
        self.isolate_monitors_row.set_subtitle("Exibir no dock apenas os aplicativos que estão abertos na tela atual.")
        self._add_icon(self.isolate_monitors_row, "preferences-desktop-display-symbolic")
        self.isolate_monitors_row.connect("notify::active", lambda w, p: self._set_backend_bool('isolate-monitors', w.get_active()))
        group.add(self.isolate_monitors_row)

        # Isolar Áreas de Trabalho
        self.isolate_workspaces_row = Adw.SwitchRow()
        self.isolate_workspaces_row.set_title("Isolar Áreas de Trabalho")
        self.isolate_workspaces_row.set_subtitle("Exibir no dock apenas os aplicativos pertencentes ao workspace ativo.")
        self._add_icon(self.isolate_workspaces_row, "preferences-desktop-workspaces-symbolic")
        self.isolate_workspaces_row.connect("notify::active", lambda w, p: self._set_backend_bool('isolate-workspaces', w.get_active()))
        group.add(self.isolate_workspaces_row)

        # Multi-monitor
        self.multi_monitor_row = Adw.SwitchRow()
        self.multi_monitor_row.set_title("Dock em Todas as Telas")
        self.multi_monitor_row.set_subtitle("Exibe uma barra de dock em todos os monitores conectados simultaneamente.")
        self._add_icon(self.multi_monitor_row, "video-display-symbolic")
        self.multi_monitor_row.connect("notify::active", lambda w, p: self._set_backend_bool('multi-monitor', w.get_active()))
        group.add(self.multi_monitor_row)

    def _sync_ui_from_backend(self):
        if self._updating:
            return False
        self._updating = True
        try:
            # Click
            click = self.backend.get_value('click-action')
            if click in self.click_keys:
                self.click_row.set_selected(self.click_keys.index(click))

            # Scroll
            scroll = self.backend.get_value('scroll-action')
            if scroll in self.scroll_keys:
                self.scroll_row.set_selected(self.scroll_keys.index(scroll))

            self.scroll_workspace_row.set_active(self.backend.get_value('scroll-switch-workspace'))
            self.scroll_focus_row.set_active(self.backend.get_value('scroll-to-focused-application'))

            # Autohide & Intellihide
            self.autohide_row.set_active(self.backend.get_value('autohide'))
            self.intellihide_row.set_active(self.backend.get_value('intellihide'))

            # Isolations
            self.isolate_monitors_row.set_active(self.backend.get_value('isolate-monitors'))
            self.isolate_workspaces_row.set_active(self.backend.get_value('isolate-workspaces'))
            self.multi_monitor_row.set_active(self.backend.get_value('multi-monitor'))

        except Exception as e:
            print(f"Error syncing behavior UI: {e}")
        finally:
            self._updating = False
        return False

    def _set_backend_bool(self, key: str, value: bool):
        if not self._updating:
            self.backend.set_value(key, value)

    def _on_click_changed(self, row, param):
        if self._updating:
            return
        idx = row.get_selected()
        if 0 <= idx < len(self.click_keys):
            self.backend.set_value('click-action', self.click_keys[idx])

    def _on_scroll_changed(self, row, param):
        if self._updating:
            return
        idx = row.get_selected()
        if 0 <= idx < len(self.scroll_keys):
            self.backend.set_value('scroll-action', self.scroll_keys[idx])

    def _on_autohide_changed(self, row, param):
        if self._updating:
            return
        self.backend.set_value('autohide', row.get_active())

    def _on_intellihide_changed(self, row, param):
        if self._updating:
            return
        self.backend.set_value('intellihide', row.get_active())
