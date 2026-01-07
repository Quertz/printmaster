#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hlavní spouštěč - kontroluje konfiguraci a spouští tisk
PrintMaster - https://github.com/Quertz/printmaster
"""

import os
import sys
import configparser

GITHUB_REPO = "Quertz/printmaster"
VERSION = "1.0.0"

def check_config_exists():
    """Kontroluje, zda existuje konfigurační soubor"""
    return os.path.exists('config.ini')

def create_initial_config():
    """Interaktivní vytvoření konfiguračního souboru"""
    print("="*60)
    print("PRINTMASTER - NASTAVENÍ RANNÍHO PŘEHLEDU")
    print("https://github.com/Quertz/printmaster")
    print("="*60)
    print("\nKonfigurace nebyla nalezena. Pojďme ji vytvořit!\n")
    
    config = configparser.ConfigParser()
    
    # General
    config['General'] = {}
    print("--- OBECNÉ NASTAVENÍ ---")
    dry_run = input("Testovací režim? (ano/ne) [ano]: ").strip().lower()
    config['General']['dry_run'] = 'true' if dry_run in ['', 'ano', 'a', 'yes', 'y'] else 'false'
    config['General']['timezone'] = 'Europe/Prague'
    
    # Weather
    config['Weather'] = {}
    print("\n--- POČASÍ ---")
    print("Zaregistrujte se na https://openweathermap.org/api (zdarma)")
    api_key = input("OpenWeatherMap API klíč: ").strip()
    config['Weather']['api_key'] = api_key
    
    city = input("Město [Prague]: ").strip() or "Prague"
    config['Weather']['city'] = city
    
    country = input("Kód země [CZ]: ").strip() or "CZ"
    config['Weather']['country_code'] = country
    
    # Personal
    config['Personal'] = {}
    print("\n--- OSOBNÍ ÚDAJE ---")
    print("Znamení zvěrokruhu:")
    print("aries (Beran), taurus (Býk), gemini (Blíženci), cancer (Rak)")
    print("leo (Lev), virgo (Panna), libra (Váhy), scorpio (Štír)")
    print("sagittarius (Střelec), capricorn (Kozoroh), aquarius (Vodnář), pisces (Ryby)")
    zodiac = input("Vaše znamení [aries]: ").strip().lower() or "aries"
    config['Personal']['zodiac_sign'] = zodiac
    
    # Calendars
    config['Calendars'] = {}
    print("\n--- KALENDÁŘE ---")
    print("Můžete přidat více kalendářů (iCal URL)")
    print("Pro Google Calendar: Nastavení → Integrovat → Tajná adresa ve formátu iCal")
    
    cal_count = 1
    while True:
        if cal_count > 1:
            add_more = input(f"\nPřidat další kalendář? (ano/ne) [ne]: ").strip().lower()
            if add_more not in ['ano', 'a', 'yes', 'y']:
                break
        
        print(f"\nKalendář #{cal_count}:")
        cal_name = input(f"  Název kalendáře [Kalendář {cal_count}]: ").strip() or f"Kalendář {cal_count}"
        
        icons = ['🏠', '💼', '📅', '🎓', '🏋️', '🎨', '👨‍👩‍👧‍👦']
        print(f"  Ikona (emoji): {', '.join(icons)}")
        cal_icon = input(f"  Ikona [{icons[min(cal_count-1, len(icons)-1)]}]: ").strip() or icons[min(cal_count-1, len(icons)-1)]
        
        cal_url = input("  iCal URL (nebo Enter pro přeskočení): ").strip()
        
        if cal_url:
            config['Calendars'][f'calendar_{cal_count}'] = f"{cal_name}|{cal_icon}|{cal_url}"
            cal_count += 1
        else:
            break
    
    # RSS
    config['RSS'] = {}
    print("\n--- RSS ZPRÁVY ---")
    use_default = input("Použít výchozí české zdroje zpráv? (ano/ne) [ano]: ").strip().lower()
    
    if use_default in ['', 'ano', 'a', 'yes', 'y']:
        config['RSS']['rss_1'] = 'Novinky.cz|https://www.novinky.cz/rss'
        config['RSS']['rss_2'] = 'ČT24|https://ct24.ceskatelevize.cz/rss/hlavni-zpravy'
        config['RSS']['rss_3'] = 'Hospodářské noviny|https://ihned.cz/?p=000000_rss'
        config['RSS']['rss_4'] = 'Seznam Zprávy|https://www.seznamzpravy.cz/rss'
    
    max_news = input("Maximální počet zpráv [5]: ").strip() or "5"
    config['RSS']['max_news'] = max_news
    
    # Printer
    config['Printer'] = {}
    print("\n--- TISKÁRNA ---")
    if config['General']['dry_run'] == 'false':
        print("Pro zjištění USB ID spusťte: lsusb")
        vendor = input("Vendor ID (hex, např. 0x0416): ").strip()
        product = input("Product ID (hex, např. 0x5011): ").strip()
        config['Printer']['vendor_id'] = vendor
        config['Printer']['product_id'] = product
    else:
        print("Testovací režim - ID tiskárny není potřeba")
        config['Printer']['vendor_id'] = '0x0416'
        config['Printer']['product_id'] = '0x5011'
    
    # Wardrobe
    config['Wardrobe'] = {}
    print("\n--- ŠATNÍK ---")
    customize = input("Přizpůsobit šatník? (ano/ne) [ne]: ").strip().lower()
    
    if customize in ['ano', 'a', 'yes', 'y']:
        print("\nZadejte položky oddělené čárkami:")
        config['Wardrobe']['light_top'] = input("Lehký vrch: ").strip() or "tričko, košile"
        config['Wardrobe']['medium_top'] = input("Střední vrch: ").strip() or "svetr, mikina"
        config['Wardrobe']['warm_top'] = input("Teplý vrch: ").strip() or "fleece, vlněný svetr"
        config['Wardrobe']['very_warm_top'] = input("Velmi teplý vrch: ").strip() or "zimní bunda, kabát"
        config['Wardrobe']['light_bottom'] = input("Lehký spodek: ").strip() or "kraťasy, lehké kalhoty"
        config['Wardrobe']['warm_bottom'] = input("Teplý spodek: ").strip() or "džíny, teplé kalhoty"
        config['Wardrobe']['rain_accessories'] = input("Doplňky na déšť: ").strip() or "deštník, pláštěnka"
        config['Wardrobe']['cold_accessories'] = input("Doplňky na zimu: ").strip() or "čepice, rukavice, šála"
        config['Wardrobe']['sun_accessories'] = input("Doplňky na slunce: ").strip() or "brýle, kšiltovka"
    else:
        # Výchozí šatník
        config['Wardrobe']['light_top'] = 'bílé tričko, černé tričko, modré polo, lněná košile'
        config['Wardrobe']['medium_top'] = 'svetr, mikina, lehká košile, cardigan'
        config['Wardrobe']['warm_top'] = 'fleecová mikina, silný svetr, vlněný svetr'
        config['Wardrobe']['very_warm_top'] = 'zimní bunda, kabát, péřová vesta'
        config['Wardrobe']['light_bottom'] = 'kraťasy, lehké kalhoty, džíny'
        config['Wardrobe']['warm_bottom'] = 'teplé džíny, vlněné kalhoty, zateplené kalhoty'
        config['Wardrobe']['rain_accessories'] = 'deštník, nepromokavá bunda, gumové boty'
        config['Wardrobe']['cold_accessories'] = 'čepice, rukavice, šála, teplé ponožky'
        config['Wardrobe']['sun_accessories'] = 'sluneční brýle, kšiltovka, krém na opalování'
    
    # Updates
    config['Updates'] = {}
    print("\n--- AKTUALIZACE ---")
    check_updates = input("Kontrolovat aktualizace? (ano/ne) [ano]: ").strip().lower()
    config['Updates']['check_updates'] = 'true' if check_updates in ['', 'ano', 'a', 'yes', 'y'] else 'false'
    
    auto_update = input("Automaticky instalovat aktualizace? (ano/ne) [ne]: ").strip().lower()
    config['Updates']['auto_update'] = 'true' if auto_update in ['ano', 'a', 'yes', 'y'] else 'false'
    
    config['Updates']['github_repo'] = GITHUB_REPO
    
    # Uložení konfigurace
    print("\n" + "="*60)
    print("Ukládám konfiguraci do config.ini...")
    with open('config.ini', 'w', encoding='utf-8') as f:
        config.write(f)
    
    print("✓ Konfigurace úspěšně vytvořena!")
    print("="*60)
    print("\nMůžete upravit config.ini ručně pro pokročilé nastavení.")
    print("Pro spuštění tisku nyní stiskněte Enter...")
    input()

def main():
    """Hlavní funkce"""
    print(f"PrintMaster v{VERSION}")
    print(f"https://github.com/{GITHUB_REPO}\n")
    
    # Kontrola konfigurace
    if not check_config_exists():
        create_initial_config()
    
    # Spuštění tisku
    print("\nSpouštím tisk ranního přehledu...\n")
    
    try:
        import print_daily
        print_daily.main()
    except Exception as e:
        print(f"Chyba při tisku: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()