#!/bin/bash
# PrintMaster - Jednořádková rychlá instalace
# https://github.com/Quertz/printmaster

set -e  # Ukončit při jakékoliv chybě

GITHUB_REPO="Quertz/printmaster"
INSTALL_SCRIPT_URL="https://raw.githubusercontent.com/$GITHUB_REPO/main/install.sh"

echo "=========================================="
echo "PrintMaster - Rychlá instalace"
echo "https://github.com/$GITHUB_REPO"
echo "=========================================="
echo ""

# Kontrola internetového připojení
echo "Kontroluji připojení k GitHubu..."
if ! ping -c 1 github.com &> /dev/null; then
    echo "❌ Není dostupné internetové připojení"
    echo "Zkontrolujte připojení a zkuste znovu"
    exit 1
fi

echo "✓ Připojení OK"
echo ""

# Stažení instalačního skriptu
echo "Stahuji instalační skript..."
curl -sSL "$INSTALL_SCRIPT_URL" -o /tmp/printmaster-install.sh

if [ $? -ne 0 ]; then
    echo "❌ Chyba při stahování instalačního skriptu"
    echo "URL: $INSTALL_SCRIPT_URL"
    exit 1
fi

echo "✓ Instalační skript stažen"
echo ""

# Nastavení práv a spuštění
chmod +x /tmp/printmaster-install.sh
bash /tmp/printmaster-install.sh

# Cleanup
rm -f /tmp/printmaster-install.sh

exit 0