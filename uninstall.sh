#!/usr/bin/env bash
set -e

ICON_PATH="$HOME/.local/share/icons/hicolor/scalable/apps/dockcraft.svg"
DESKTOP_PATH="$HOME/.local/share/applications/com.github.dockcraft.desktop"

echo "🗑️ Desinstalando DockCraft..."

if [ -f "$ICON_PATH" ]; then
    rm "$ICON_PATH"
    echo "✓ Ícone removido."
fi

if [ -f "$DESKTOP_PATH" ]; then
    rm "$DESKTOP_PATH"
    echo "✓ Atalho de aplicativo removido."
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "✨ DockCraft desinstalado do menu de aplicativos."
