#!/bin/bash
# Kompletní instalační skript pro Raspberry Pi - čistá instalace
# PrintMaster - https://github.com/Quertz/printmaster

GITHUB_REPO="Quertz/printmaster"
PROJECT_NAME="PrintMaster"

echo "=========================================="
echo "$PROJECT_NAME - INSTALACE PRO RASPBERRY PI"
echo "https://github.com/$GITHUB_REPO"
echo "=========================================="
echo ""

# Kontrola, zda běžíme jako root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Nespouštějte tento skript jako root (sudo)"
    echo "Skript si o sudo požádá, když bude potřeba"
    exit 1
fi

# Detekce OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    echo "Detekován systém: $PRETTY_NAME"
else
    echo "❌ Nepodařilo se detekovat operační systém"
    exit 1
fi

# Aktualizace systému
echo ""
echo "=========================================="
echo "1. AKTUALIZACE SYSTÉMU"
echo "=========================================="
echo "Toto může chvíli trvat..."

sudo apt update
if [ $? -ne 0 ]; then
    echo "❌ Chyba při aktualizaci seznamu balíčků"
    exit 1
fi

sudo apt upgrade -y
if [ $? -ne 0 ]; then
    echo "⚠️  Chyba při aktualizaci systému, ale pokračuji..."
fi

echo "✓ Systém aktualizován"

# Instalace Pythonu a základních nástrojů
echo ""
echo "=========================================="
echo "2. INSTALACE PYTHONU A NÁSTROJŮ"
echo "=========================================="

PACKAGES="python3 python3-pip python3-venv git curl libusb-1.0-0"

echo "Instaluji: $PACKAGES"
sudo apt install -y $PACKAGES

if [ $? -ne 0 ]; then
    echo "❌ Chyba při instalaci balíčků"
    exit 1
fi

echo "✓ Python a nástroje nainstalovány"

# Kontrola Pythonu
PYTHON_VERSION=$(python3 --version)
echo "✓ $PYTHON_VERSION"

# Instalace Python knihoven
echo ""
echo "=========================================="
echo "3. INSTALACE PYTHON KNIHOVEN"
echo "=========================================="

echo "Instaluji Python závislosti..."
pip3 install --break-system-packages python-escpos requests icalendar feedparser python-dateutil

if [ $? -ne 0 ]; then
    echo "❌ Chyba při instalaci Python knihoven"
    exit 1
fi

echo "✓ Python knihovny nainstalovány"

# Kontrola USB přístupu
echo ""
echo "=========================================="
echo "4. NASTAVENÍ USB PŘÍSTUPU"
echo "=========================================="

# Přidání uživatele do skupiny lp (printer)
sudo usermod -a -G lp $USER
echo "✓ Uživatel $USER přidán do skupiny 'lp'"

# Vytvoření udev pravidla pro USB tiskárnu
echo "Vytvářím udev pravidlo pro USB tiskárnu..."
sudo bash -c 'cat > /etc/udev/rules.d/99-escpos.rules << EOF
# USB thermal printers
SUBSYSTEM=="usb", ATTRS{idVendor}=="*", ATTRS{idProduct}=="*", MODE="0666"
EOF'

sudo udevadm control --reload-rules
sudo udevadm trigger

echo "✓ USB přístup nastaven"

# Vytvoření pracovního adresáře
echo ""
echo "=========================================="
echo "5. PŘÍPRAVA PRACOVNÍHO ADRESÁŘE"
echo "=========================================="

INSTALL_DIR="$HOME/printmaster"

if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Adresář $INSTALL_DIR již existuje"
    echo "Chcete jej odstranit a provést čistou instalaci? (ano/ne)"
    read -r response
    if [[ "$response" =~ ^([aA][nN][oO]|[aA]|[yY][eE][sS]|[yY])$ ]]; then
        # Záloha config.ini pokud existuje
        if [ -f "$INSTALL_DIR/config.ini" ]; then
            cp "$INSTALL_DIR/config.ini" "$HOME/config.ini.backup"
            echo "✓ Konfigurace zálohována do ~/config.ini.backup"
        fi
        rm -rf "$INSTALL_DIR"
        echo "✓ Starý adresář odstraněn"
    else
        echo "Instalace zrušena"
        exit 0
    fi
fi

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "✓ Pracovní adresář: $INSTALL_DIR"

# Stažení souborů z GitHubu
echo ""
echo "=========================================="
echo "6. STAŽENÍ SOUBORŮ Z GITHUB"
echo "=========================================="

echo "Stahuji z https://github.com/$GITHUB_REPO ..."

git clone "https://github.com/$GITHUB_REPO.git" .

if [ $? -ne 0 ]; then
    echo "❌ Chyba při klonování repozitáře"
    echo "Zkontrolujte internetové připojení a URL repozitáře"
    exit 1
fi

echo "✓ Repozitář naklonován"

# Obnovení konfigurace pokud existuje záloha
if [ -f "$HOME/config.ini.backup" ]; then
    echo "Chcete obnovit předchozí konfiguraci? (ano/ne)"
    read -r restore_config
    if [[ "$restore_config" =~ ^([aA][nN][oO]|[aA]|[yY][eE][sS]|[yY])$ ]]; then
        cp "$HOME/config.ini.backup" "$INSTALL_DIR/config.ini"
        echo "✓ Konfigurace obnovena"
    fi
fi

# Nastavení práv
echo ""
echo "=========================================="
echo "7. NASTAVENÍ OPRÁVNĚNÍ"
echo "=========================================="

chmod +x runme.py update.py 2>/dev/null

if [ -f "install.sh" ]; then
    chmod +x install.sh
fi

echo "✓ Oprávnění nastavena"

# Konfigurace cron
echo ""
echo "=========================================="
echo "8. AUTOMATICKÉ SPOUŠTĚNÍ"
echo "=========================================="

echo "Chcete nastavit automatické spouštění každé ráno? (ano/ne)"
read -r setup_cron

if [[ "$setup_cron" =~ ^([aA][nN][oO]|[aA]|[yY][eE][sS]|[yY])$ ]]; then
    echo "V kolik hodin? (0-23) [7]:"
    read -r cron_hour
    cron_hour=${cron_hour:-7}
    
    echo "V kolik minut? (0-59) [0]:"
    read -r cron_minute
    cron_minute=${cron_minute:-0}
    
    CRON_CMD="$cron_minute $cron_hour * * * cd $INSTALL_DIR && /usr/bin/python3 update.py >> $INSTALL_DIR/log.txt 2>&1"
    
    # Odstranění starých cron úloh pro tento projekt
    crontab -l 2>/dev/null | grep -v "printmaster" | grep -v "update.py" > /tmp/mycron
    echo "$CRON_CMD" >> /tmp/mycron
    crontab /tmp/mycron
    rm /tmp/mycron
    
    echo "✓ Cron úloha přidána: každý den v ${cron_hour}:${cron_minute}"
else
    echo "ℹ️  Automatické spouštění není nastaveno"
    echo "   Můžete jej nastavit později pomocí: crontab -e"
fi

# Test USB tiskárny
echo ""
echo "=========================================="
echo "9. TEST USB ZAŘÍZENÍ"
echo "=========================================="

echo "Chcete zjistit USB ID vaší tiskárny? (ano/ne)"
read -r test_usb

if [[ "$test_usb" =~ ^([aA][nN][oO]|[aA]|[yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo "Seznam USB zařízení:"
    echo "-------------------"
    lsusb
    echo ""
    echo "Připojte tiskárnu a zkontrolujte její Vendor ID a Product ID"
    echo "Formát: Bus XXX Device XXX: ID VVVV:PPPP (VVVV=Vendor, PPPP=Product)"
fi

# Vytvoření pomocných skriptů
echo ""
echo "=========================================="
echo "10. VYTVOŘENÍ POMOCNÝCH SKRIPTŮ"
echo "=========================================="

cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
# Ruční spuštění ranního přehledu
cd "$(dirname "$0")"
python3 runme.py
EOF

chmod +x "$INSTALL_DIR/start.sh"

cat > "$INSTALL_DIR/test.sh" << 'EOF'
#!/bin/bash
# Testovací spuštění (bez tisku)
cd "$(dirname "$0")"
python3 runme.py
EOF

chmod +x "$INSTALL_DIR/test.sh"

cat > "$INSTALL_DIR/update-now.sh" << 'EOF'
#!/bin/bash
# Ruční kontrola aktualizací
cd "$(dirname "$0")"
python3 update.py
EOF

chmod +x "$INSTALL_DIR/update-now.sh"

echo "✓ Pomocné skripty vytvořeny:"
echo "  - start.sh      (ruční spuštění)"
echo "  - test.sh       (testovací režim)"
echo "  - update-now.sh (kontrola aktualizací)"

# Vytvoření README
cat > "$INSTALL_DIR/QUICKSTART.md" << EOF
# $PROJECT_NAME - Rychlý start

## Spuštění

\`\`\`bash
cd $INSTALL_DIR
./start.sh
\`\`\`

## Testování (bez tisku)

\`\`\`bash
./test.sh
\`\`\`

## Kontrola aktualizací

\`\`\`bash
./update-now.sh
\`\`\`

## Konfigurace

Editujte \`config.ini\` pro změnu nastavení.

## Zjištění USB ID tiskárny

\`\`\`bash
lsusb
\`\`\`

## Podpora

GitHub: https://github.com/$GITHUB_REPO
Issues: https://github.com/$GITHUB_REPO/issues
EOF

echo "✓ Rychlý start průvodce: QUICKSTART.md"

# Dokončení
echo ""
echo "=========================================="
echo "✓✓✓ INSTALACE DOKONČENA ✓✓✓"
echo "=========================================="


echo ""
echo "=========================================="
echo "⚠️  ŘEŠENÍ ČASTÝCH PROBLÉMŮ"
echo "=========================================="
echo ""
echo "Problém: 'Permission denied' při tisku"
echo "Řešení:  sudo usermod -a -G lp $USER && sudo reboot"
echo ""
echo "Problém: 'No backend available' (tiskárna nenalezena)"
echo "Řešení:  Zkontrolujte lsusb a správné USB ID v config.ini"
echo ""
echo "Problém: Python knihovny nejdou nainstalovat"
echo "Řešení:  Zkuste: pip3 install --user [knihovna]"
echo ""
echo "Problém: Cron nefunguje"
echo "Řešení:  Zkontrolujte: crontab -l"
echo "         Log: cat ~/ranni-prehled/log.txt"
echo ""