#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_PATH="$PROJECT_DIR/bin/dockcraft"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
APP_DIR="$HOME/.local/share/applications"

echo "🎨 Instalando DockCraft para o usuário atual..."

# Ensure target directories exist
mkdir -p "$ICON_DIR"
mkdir -p "$APP_DIR"

# Install icon
cp "$PROJECT_DIR/data/icons/dockcraft.svg" "$ICON_DIR/dockcraft.svg"
echo "✓ Ícone instalado em $ICON_DIR/dockcraft.svg"

# Generate desktop file with absolute executable path
cat > "$APP_DIR/com.github.dockcraft.desktop" <<EOF
[Desktop Entry]
Name=DockCraft
GenericName=Personalizador do Dock do Ubuntu
Comment=Personalize o design, estilo flutuante, indicadores e usabilidade do dock do Ubuntu
Exec=$BIN_PATH
Icon=dockcraft
Terminal=false
Type=Application
Categories=Utility;Settings;DesktopSettings;GTK;
Keywords=dock;ubuntu;dash-to-dock;personalizacao;customizer;macos;windows;
StartupNotify=true
StartupWMClass=com.github.dockcraft
EOF

chmod +x "$APP_DIR/com.github.dockcraft.desktop"
chmod +x "$BIN_PATH"

# Update icon cache and desktop database if tools exist
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
fi

echo "✨ DockCraft instalado com sucesso!"
echo "Você já pode pesquisar por 'DockCraft' no menu Mostrar Aplicativos ou executar: ./bin/dockcraft"
