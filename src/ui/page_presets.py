"""
Presets and Pinned Apps management page for DockCraft.
"""

from typing import Callable, List, Optional
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib
from ..backend import DockBackend
from ..preset_manager import PresetManager, Preset


class PresetsPage(Adw.PreferencesPage):
    def __init__(self, backend: DockBackend, preset_manager: PresetManager, on_notify: Callable[[str], None]):
        super().__init__()
        self.backend = backend
        self.preset_manager = preset_manager
        self.on_notify = on_notify

        self.set_title("Presets e Estilos")
        self.set_icon_name("starred-symbolic")

        # 1. Quick Actions Group
        self._build_quick_actions()

        # 2. Built-in Presets Group
        self.builtin_group = Adw.PreferencesGroup()
        self.builtin_group.set_title("Estilos Prontos (1-Clique)")
        self.builtin_group.set_description("Transforme a aparência e o comportamento do dock com perfis desenhados à mão.")
        self.add(self.builtin_group)

        # 3. Pinned Apps / Favoritos Manager Group
        self._build_favorites_group()

        # 4. User Presets Group
        self.user_group = Adw.PreferencesGroup()
        self.user_group.set_title("Meus Presets Personalizados")
        self.user_group.set_description("Presets personalizados salvos por você.")
        self.add(self.user_group)

        # 5. Actions Group (Save current)
        self.actions_group = Adw.PreferencesGroup()
        self.actions_group.set_title("Salvar Configuração Atual")
        self.add(self.actions_group)

        self.builtin_rows = []
        self.user_rows = []
        self._build_save_row()
        self.refresh_presets()

        # Listen to backend changes to update active preset badges
        for k in ['dock-position', 'extend-height', 'always-center-icons', 'dash-max-icon-size', 'show-trash', 'autohide']:
            self.backend.add_change_listener(k, lambda k, v: GLib.idle_add(self._update_active_badges))

    def _build_quick_actions(self):
        group = Adw.PreferencesGroup()
        group.set_title("Ações Rápidas")
        self.add(group)

        row = Adw.ActionRow()
        row.set_title("Recarregar Extensão do Dock")
        row.set_subtitle("Reinicia a extensão do Ubuntu Dock instantaneamente para resolver qualquer problema visual.")
        
        icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic")
        row.add_prefix(icon)

        reload_btn = Gtk.Button(label="Recarregar")
        reload_btn.add_css_class("flat")
        reload_btn.set_valign(Gtk.Align.CENTER)
        reload_btn.connect("clicked", self._on_reload_dock_clicked)
        row.add_suffix(reload_btn)

        group.add(row)

    def _build_favorites_group(self):
        self.fav_group = Adw.PreferencesGroup()
        self.fav_group.set_title("Aplicativos Fixados no Dock")
        self.fav_group.set_description("Gerenciamento e visibilidade dos seus aplicativos favoritos fixados.")
        self.add(self.fav_group)

        # Toggle show-favorites
        self.show_fav_row = Adw.SwitchRow()
        self.show_fav_row.set_title("Exibir Aplicativos Fixados")
        self.show_fav_row.set_subtitle("Mantém os atalhos fixos visíveis no dock.")
        img = Gtk.Image.new_from_icon_name("starred-symbolic")
        self.show_fav_row.add_prefix(img)
        self.show_fav_row.set_active(self.backend.get_value('show-favorites'))
        self.show_fav_row.connect("notify::active", self._on_toggle_show_favorites)
        self.fav_group.add(self.show_fav_row)

        # Expander row listing pinned apps
        self.apps_expander = Adw.ExpanderRow()
        self.apps_expander.set_title("Ver Lista de Apps Fixados")
        self._refresh_pinned_apps_list()
        self.fav_group.add(self.apps_expander)

    def _refresh_pinned_apps_list(self):
        # Clear previous rows inside expander
        child = self.apps_expander.get_first_child()
        # In AdwExpanderRow, use get_first_child or remove child
        favs = self.backend.get_favorite_apps()
        self.apps_expander.set_subtitle(f"{len(favs)} aplicativo(s) fixado(s)")

        for desktop_id in favs:
            info = Gio.DesktopAppInfo.new(desktop_id)
            name = (info.get_display_name() or info.get_name()) if info else desktop_id
            icon_name = (info.get_icon().to_string() if info and info.get_icon() else "application-x-executable")

            app_row = Adw.ActionRow()
            app_row.set_title(name)
            app_row.set_subtitle(desktop_id)
            img = Gtk.Image.new_from_icon_name(icon_name)
            app_row.add_prefix(img)
            self.apps_expander.add_row(app_row)

    def _on_toggle_show_favorites(self, switch_row, param):
        active = switch_row.get_active()
        self.backend.set_value('show-favorites', active)
        status = "visíveis" if active else "ocultos"
        self.on_notify(f"Aplicativos fixados agora estão {status}.")

    def _on_reload_dock_clicked(self, button: Gtk.Button):
        success = self.backend.restart_dock_extension()
        if success:
            self.on_notify("Extensão do dock recarregada com sucesso!")
        else:
            self.on_notify("Não foi possível recarregar a extensão.")

    def _build_save_row(self):
        row = Adw.ActionRow()
        row.set_title("Salvar Dock Atual como Preset")
        row.set_subtitle("Crie um backup das suas configurações visuais e comportamentais atuais.")
        row.add_prefix(Gtk.Image.new_from_icon_name("document-save-symbolic"))

        save_btn = Gtk.Button(label="Salvar Preset")
        save_btn.add_css_class("suggested-action")
        save_btn.set_valign(Gtk.Align.CENTER)
        save_btn.connect("clicked", self._on_save_preset_clicked)
        row.add_suffix(save_btn)
        self.actions_group.add(row)

    def refresh_presets(self):
        # Clear groups
        for row in self.builtin_rows:
            self.builtin_group.remove(row)
        self.builtin_rows.clear()

        for row in self.user_rows:
            self.user_group.remove(row)
        self.user_rows.clear()

        self.preset_manager.load_all_presets()
        presets = self.preset_manager.get_presets()
        builtin_presets = [p for p in presets if p.is_builtin]
        user_presets = [p for p in presets if not p.is_builtin]

        for preset in builtin_presets:
            row = self._create_preset_row(preset)
            self.builtin_rows.append(row)
            self.builtin_group.add(row)

        if not user_presets:
            empty_row = Adw.ActionRow()
            empty_row.set_title("Nenhum preset salvo ainda")
            empty_row.set_subtitle("Clique em 'Salvar Preset' acima para guardar seu visual favorito.")
            self.user_rows.append(empty_row)
            self.user_group.add(empty_row)
        else:
            for preset in user_presets:
                row = self._create_preset_row(preset)
                self.user_rows.append(row)
                self.user_group.add(row)

        self._update_active_badges()

    def _get_active_preset_id(self) -> Optional[str]:
        """Returns the single ID of the preset that best matches current settings, or None."""
        presets = self.preset_manager.get_presets()
        best_preset_id = None
        best_score = 0

        eval_keys = [
            'dock-position',
            'extend-height',
            'always-center-icons',
            'dash-max-icon-size',
            'autohide',
            'intellihide',
            'show-trash',
            'show-show-apps-button',
            'show-favorites',
            'show-running',
            'running-indicator-style',
            'click-action',
        ]

        for preset in presets:
            match_count = 0
            mismatch = False
            for k in eval_keys:
                if k in preset.settings:
                    val = self.backend.get_value(k)
                    if val == preset.settings[k]:
                        match_count += 1
                    else:
                        # Core differentiating keys must match exactly
                        if k in ['dock-position', 'extend-height', 'always-center-icons', 'dash-max-icon-size', 'show-trash']:
                            mismatch = True
                            break

            if not mismatch and match_count > best_score:
                best_score = match_count
                best_preset_id = preset.key_id

        return best_preset_id

    def _update_active_badges(self):
        active_id = self._get_active_preset_id()
        for row in self.builtin_rows + self.user_rows:
            preset = getattr(row, '_preset', None)
            btn = getattr(row, '_apply_btn', None)
            if preset and btn:
                if preset.key_id == active_id:
                    btn.set_label("✓ Ativo")
                    btn.add_css_class("success")
                    btn.remove_css_class("suggested-action")
                else:
                    btn.set_label("Aplicar")
                    btn.remove_css_class("success")

    def _create_preset_row(self, preset: Preset) -> Adw.ActionRow:
        row = Adw.ActionRow()
        row._preset = preset
        row.set_title(preset.name)
        row.set_subtitle(preset.description)
        row.add_prefix(Gtk.Image.new_from_icon_name(preset.icon))

        # Apply Button
        apply_btn = Gtk.Button(label="Aplicar")
        apply_btn.add_css_class("pill")
        apply_btn.set_valign(Gtk.Align.CENTER)
        apply_btn.connect("clicked", lambda b, pid=preset.key_id, pname=preset.name: self._apply_preset(pid, pname))
        row._apply_btn = apply_btn
        row.add_suffix(apply_btn)

        # If user preset, add delete button
        if not preset.is_builtin:
            del_btn = Gtk.Button.new_from_icon_name("user-trash-symbolic")
            del_btn.add_css_class("flat")
            del_btn.set_valign(Gtk.Align.CENTER)
            del_btn.set_tooltip_text("Excluir Preset")
            del_btn.connect("clicked", lambda b, pid=preset.key_id: self._delete_user_preset(pid))
            row.add_suffix(del_btn)

        return row

    def _apply_preset(self, preset_id: str, preset_name: str):
        success = self.preset_manager.apply_preset(preset_id)
        if success:
            self._update_active_badges()
            self.on_notify(f"Preset '{preset_name}' aplicado com sucesso!")
        else:
            self.on_notify(f"Erro ao aplicar preset '{preset_name}'.")

    def _delete_user_preset(self, preset_id: str):
        self.preset_manager.delete_user_preset(preset_id)
        self.refresh_presets()
        self.on_notify("Preset excluído.")

    def _on_save_preset_clicked(self, button: Gtk.Button):
        root = self.get_root()
        dialog = Adw.MessageDialog.new(root, "Salvar Preset Atual", "Escolha um nome para o seu preset personalizado.")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("save", "Salvar")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        entry = Gtk.Entry()
        entry.set_placeholder_text("Ex: Meu Dock Minimalista")
        entry.set_margin_top(12)
        entry.set_margin_bottom(12)
        dialog.set_extra_child(entry)

        def on_response(dlg, response):
            if response == "save":
                name = entry.get_text().strip()
                if name:
                    preset = self.preset_manager.save_current_as_preset(name)
                    if preset:
                        self.refresh_presets()
                        self.on_notify(f"Preset '{name}' salvo com sucesso!")

        dialog.connect("response", on_response)
        dialog.present()
