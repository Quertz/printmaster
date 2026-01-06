#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatická kontrola a instalace aktualizací z GitHubu
PrintMaster - https://github.com/Quertz/printmaster
"""

import os
import sys
import json
import requests
import subprocess
import configparser
from datetime import datetime

VERSION_FILE = '.version'
CURRENT_VERSION = '1.0.0'
GITHUB_REPO = 'Quertz/printmaster'

def load_config():
    """Načte konfiguraci"""
    config = configparser.ConfigParser()
    
    if os.path.exists('config.ini'):
        config.read('config.ini', encoding='utf-8')
    
    return config

def get_current_version():
    """Vrátí aktuální verzi"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    return CURRENT_VERSION

def save_version(version):
    """Uloží verzi do souboru"""
    with open(VERSION_FILE, 'w') as f:
        f.write(version)

def check_github_version(repo):
    """Zkontroluje nejnovější verzi na GitHubu"""
    if not repo:
        repo = GITHUB_REPO
    
    try:
        # Získání nejnovějšího release
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            latest_version = data['tag_name'].lstrip('v')
            download_url = data['zipball_url']
            release_notes = data.get('body', '')
            
            return {
                'version': latest_version,
                'url': download_url,
                'notes': release_notes,
                'published': data['published_at']
            }
        else:
            print(f"GitHub API odpovědělo stavem: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Chyba při kontrole aktualizací: {e}")
        return None

def compare_versions(v1, v2):
    """Porovná dvě verze (True pokud v2 je novější než v1)"""
    try:
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        return v2_parts > v1_parts
    except:
        return False

def download_and_install_update(download_url):
    """Stáhne a nainstaluje aktualizaci"""
    import tempfile
    import zipfile
    import shutil
    
    print("Stahuji aktualizaci...")
    
    try:
        # Stažení ZIP souboru
        response = requests.get(download_url, timeout=30)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            tmp_file.write(response.content)
            zip_path = tmp_file.name
        
        # Vytvoření záložní kopie
        backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        files_to_backup = ['print_daily.py', 'runme.py', 'update.py']
        for file in files_to_backup:
            if os.path.exists(file):
                shutil.copy2(file, os.path.join(backup_dir, file))
        
        print(f"Záloha vytvořena v: {backup_dir}")
        
        # Rozbalení aktualizace
        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)
            
            # Najít kořenový adresář (GitHub vytváří složku s názvem repo)
            extracted_dirs = os.listdir(tmp_dir)
            if extracted_dirs:
                source_dir = os.path.join(tmp_dir, extracted_dirs[0])
                
                # Kopírování souborů
                for file in files_to_backup:
                    src = os.path.join(source_dir, file)
                    if os.path.exists(src):
                        shutil.copy2(src, file)
                        print(f"✓ Aktualizován: {file}")
        
        # Smazání dočasného ZIP
        os.remove(zip_path)
        
        print("✓ Aktualizace úspěšně nainstalována!")
        return True
        
    except Exception as e:
        print(f"Chyba při instalaci aktualizace: {e}")
        print(f"Obnovuji ze zálohy...")
        
        # Obnovení ze zálohy
        if os.path.exists(backup_dir):
            for file in files_to_backup:
                backup_file = os.path.join(backup_dir, file)
                if os.path.exists(backup_file):
                    shutil.copy2(backup_file, file)
        
        return False

def main():
    """Hlavní funkce"""
    print("="*60)
    print("PRINTMASTER - KONTROLA AKTUALIZACÍ")
    print(f"https://github.com/{GITHUB_REPO}")
    print("="*60)
    
    # Načtení konfigurace
    config = load_config()
    
    if not config.has_section('Updates'):
        print("Sekce Updates v konfiguraci nenalezena.")
        print("Spouštím bez kontroly aktualizací...\n")
        repo = GITHUB_REPO
        check_updates = True
        auto_update = False
    else:
        check_updates = config.getboolean('Updates', 'check_updates', fallback=True)
        auto_update = config.getboolean('Updates', 'auto_update', fallback=False)
        repo = config.get('Updates', 'github_repo', fallback=GITHUB_REPO)
    
    if check_updates:
        print(f"Repozitář: https://github.com/{repo}")
        current = get_current_version()
        print(f"Aktuální verze: {current}")
        
        latest_info = check_github_version(repo)
        
        if latest_info:
            latest = latest_info['version']
            print(f"Nejnovější verze: {latest}")
            
            if compare_versions(current, latest):
                print("\n🎉 Dostupná nová verze!")
                print(f"\nPoznámky k vydání:\n{latest_info['notes']}\n")
                
                if auto_update:
                    print("Automatická aktualizace je povolena...")
                    if download_and_install_update(latest_info['url']):
                        save_version(latest)
                        print("\n✓ Aktualizace dokončena!")
                    else:
                        print("\n✗ Aktualizace selhala")
                else:
                    response = input("Chcete aktualizovat? (ano/ne): ").strip().lower()
                    if response in ['ano', 'a', 'yes', 'y']:
                        if download_and_install_update(latest_info['url']):
                            save_version(latest)
                            print("\n✓ Aktualizace dokončena!")
                        else:
                            print("\n✗ Aktualizace selhala")
            else:
                print("✓ Máte nejnovější verzi")
        else:
            print("Nelze zkontrolovat aktualizace")
    else:
        print("Kontrola aktualizací je vypnuta")
    
    print("\n" + "="*60)
    print("SPOUŠTĚNÍ RANNÍHO PŘEHLEDU")
    print("="*60 + "\n")
    
    # Spuštění hlavního programu
    try:
        subprocess.run([sys.executable, 'runme.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Chyba při spouštění: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("CHYBA: Soubor runme.py nebyl nalezen!")
        sys.exit(1)

if __name__ == "__main__":
    main()