#!/bin/bash
# Kompletní instalační skript pro Raspberry Pi a macOS
# PrintMaster - https://github.com/Quertz/printmaster

GITHUB_REPO="Quertz/printmaster"
PROJECT_NAME="PrintMaster"

echo "=========================================="
echo "$PROJECT_NAME - INSTALACE"
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
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        echo "Detekován systém: $PRETTY_NAME"
    else
        DISTRO="unknown"
        echo "Detekován systém: Linux (neznámá distribuce)"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    MACOS_VERSION=$(sw_vers -productVersion)
    echo "Detekován systém: macOS $MACOS_VERSION"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "❌ Windows není podporován"
    echo "Použijte WSL (Windows Subsystem for Linux) nebo Linux/macOS"
    exit 1
else
    echo "❌ Nepodařilo se detekovat operační systém: $OSTYPE"
    exit 1
fi

# Aktualizace systému
echo ""
echo "=========================================="
echo "1. AKTUALIZACE SYSTÉMU"
echo "=========================================="

if [ "$OS" = "linux" ]; then
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
    
elif [ "$OS" = "macos" ]; then
    # Kontrola Homebrew
    if ! command -v brew &> /dev/null; then
        echo "Homebrew není nainstalován. Instaluji..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        if [ $? -ne 0 ]; then
            echo "❌ Chyba při instalaci Homebrew"
            exit 1
        fi
        
        # Přidání Homebrew do PATH (pro Apple Silicon)
        if [[ $(uname -m) == 'arm64' ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    fi
    
    echo "Aktualizuji Homebrew..."
    brew update
    echo "✓ Homebrew aktualizován"
fi

# Instalace Pythonu a základních nástrojů
echo ""
echo "=========================================="
echo "2. INSTALACE PYTHONU A NÁSTROJŮ"
echo "=========================================="

if [ "$OS" = "linux" ]; then
    PACKAGES="python3 python3-pip python3-venv git curl libusb-1.0-0"
    
    echo "Instaluji: $PACKAGES"
    sudo apt install -y $PACKAGES
    
    if [ $? -ne 0 ]; then
        echo "❌ Chyba při instalaci balíčků"
        exit 1
    fi
    
elif [ "$OS" = "macos" ]; then
    echo "Instaluji Python 3, git a libusb..."
    brew install python3 git libusb
    
    if [ $? -ne 0 ]; then
        echo "❌ Chyba při instalaci balíčků"
        exit 1
    fi
fi

echo "✓ Python a nástroje nainstalovány"

# Kontrola Pythonu
PYTHON_VERSION=$(python3 --version 2>&1)
echo "✓ $PYTHON_VERSION"

# Instalace Python knihoven
echo ""
echo "=========================================="
echo "3. INSTALACE PYTHON KNIHOVEN"
echo "=========================================="

echo "Instaluji Python závislosti..."

if [ "$OS" = "linux" ]; then
    pip3 install --break-system-packages python-escpos requests icalendar feedparser python-dateutil
elif [ "$OS" = "macos" ]; then
    pip3 install python-escpos requests icalendar feedparser python-dateutil
fi

if [ $? -ne 0 ]; then
    echo "❌ Chyba při instalaci Python knihoven"
    echo "Zkouším alternativní metodu..."
    python3 -m pip install --user python-escpos requests icalendar feedparser python-dateutil
    
    if [ $? -ne 0 ]; then
        echo "❌ Instalace stále selhává"
        exit 1
    fi
fi

echo "✓ Python knihovny nainstalovány"

# Nastavení USB přístupu
echo ""
echo "=========================================="
echo "4. NASTAVENÍ USB PŘÍSTUPU"
echo "=========================================="

if [ "$OS" = "linux" ]; then
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
    
elif [ "$OS" = "macos" ]; then
    echo "ℹ️  Na macOS není potřeba speciální nastavení USB"
    echo "✓ USB by mělo fungovat automaticky"
fi

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
    
    if [ "$OS" = "macos" ]; then
        # Na macOS použijeme plnou cestu k pythonu
        PYTHON_PATH=$(which python3)
        CRON_CMD="$cron_minute $cron_hour * * * cd $INSTALL_DIR && $PYTHON_PATH update.py >> $INSTALL_DIR/log.txt 2>&1"
    fi
    
    # Odstranění starých cron úloh pro tento projekt
    (crontab -l 2>/dev/null | grep -v "printmaster" | grep -v "update.py") > /tmp/mycron 2>/dev/null
    echo "$CRON_CMD" >> /tmp/mycron
    crontab /tmp/mycron
    rm /tmp/mycron
    
    echo "✓ Cron úloha přidána: každý den v ${cron_hour}:${cron_minute}"
    
    if [ "$OS" = "macos" ]; then
        echo ""
        echo "ℹ️  Na macOS může být potřeba povolit cron v:"
        echo "   Předvolby systému → Zabezpečení a ochrana soukromí → Plný přístup k disku"
    fi
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
    
    if [ "$OS" = "linux" ]; then
        lsusb
    elif [ "$OS" = "macos" ]; then
        system_profiler SPUSBDataType | grep -A 10 "Printer\|Thermal"
        echo ""
        echo "Nebo použijte: ioreg -p IOUSB -w0 -l"
    fi
    
    echo ""
    echo "Připojte tiskárnu a zkontrolujte její Vendor ID a Product ID"
    if [ "$OS" = "linux" ]; then
        echo "Formát: Bus XXX Device XXX: ID VVVV:PPPP (VVVV=Vendor, PPPP=Product)"
    elif [ "$OS" = "macos" ]; then
        echo "Hledejte: Vendor ID a Product ID v hexadecimálním formátu"
    fi
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

Systém: $OS $([ "$OS" = "macos" ] && echo "$MACOS_VERSION" || echo "")

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

### Linux:
\`\`\`bash
lsusb
\`\`\`

### macOS:
\`\`\`bash
system_profiler SPUSBDataType
# nebo
ioreg -p IOUSB -w0 -l | grep -A 10 Printer
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
echo "📦 $PROJECT_NAME nainstalován v: $INSTALL_DIR"
echo "🌐 GitHub: https://github.com/$GITHUB_REPO"
echo "💻 Systém: $OS"
echo ""
echo "🚀 DALŠÍ KROKY:"
echo ""

if [ "$OS" = "linux" ]; then
    echo "1. Restartujte systém nebo se odhlašte a přihlašte (kvůli skupinám):"
    echo "   sudo reboot"
    echo ""
    echo "2. Po restartu spusťte konfiguraci:"
elif [ "$OS" = "macos" ]; then
    echo "1. Spusťte konfiguraci:"
fi

echo "   cd $INSTALL_DIR"
echo "   ./start.sh"
echo ""
echo "2. Nebo spusťte přímo:"
echo "   python3 runme.py"
echo ""
echo "📖 Rychlý start: cat QUICKSTART.md"
echo ""

if [ "$OS" = "macos" ]; then
    echo "ℹ️  POZNÁMKA PRO macOS:"
    echo "   - Tiskárna může vyžadovat instalaci driverů od výrobce"
    echo "   - Pro cron může být potřeba povolit přístup v Zabezpečení"
    echo ""
fi

# Nabídnout restart (pouze Linux)
if [ "$OS" = "linux" ]; then
    echo "Chcete restartovat systém nyní? (doporučeno) (ano/ne)"
    read -r do_reboot
    
    if [[ "$do_reboot" =~ ^([aA][nN][oO]|[aA]|[yY][eE][sS]|[yY])$ ]]; then
        echo "Restartuji za 5 sekund..."
        sleep 5
        sudo reboot
    fi
fi
