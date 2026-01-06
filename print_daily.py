#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrintMaster - Ranní přehled pro termotiskárnu
https://github.com/Quertz/printmaster

Vytiskne denní přehled s počasím, kalendářem, zprávami, horoskopem a doporučením oblečení.
"""

import datetime
import requests
import random
from icalendar import Calendar
import feedparser
from dateutil import tz
import configparser
import os
import sys

VERSION = "1.0.0"
GITHUB_REPO = "Quertz/printmaster"

# ====== NAČTENÍ KONFIGURACE ======
def load_config():
    """Načte konfiguraci ze souboru"""
    config = configparser.ConfigParser()
    
    if not os.path.exists('config.ini'):
        print("CHYBA: Nenalezen soubor config.ini!")
        print("Spusťte nejprve: python3 runme.py")
        sys.exit(1)
    
    config.read('config.ini', encoding='utf-8')
    return config

CONFIG = load_config()

# Načtení konfiguračních hodnot
DRY_RUN = CONFIG.getboolean('General', 'dry_run', fallback=True)
OPENWEATHER_API_KEY = CONFIG.get('Weather', 'api_key', fallback='')
CITY = CONFIG.get('Weather', 'city', fallback='Prague')
COUNTRY_CODE = CONFIG.get('Weather', 'country_code', fallback='CZ')
ZVEROKRUH = CONFIG.get('Personal', 'zodiac_sign', fallback='aries')

# Načtení kalendářů
KALENDARE = []
for key in CONFIG['Calendars']:
    if key.startswith('calendar_'):
        parts = CONFIG['Calendars'][key].split('|')
        if len(parts) == 3:
            KALENDARE.append({
                'nazev': parts[0],
                'ikona': parts[1],
                'url': parts[2]
            })

# Načtení RSS zdrojů
RSS_ZDROJE = []
for key in CONFIG['RSS']:
    if key.startswith('rss_'):
        parts = CONFIG['RSS'][key].split('|')
        if len(parts) == 2:
            RSS_ZDROJE.append({
                'nazev': parts[0],
                'url': parts[1]
            })

MAX_NEWS = CONFIG.getint('RSS', 'max_news', fallback=5)

# Načtení šatníku
SATNIK = {
    "vrchní": {
        "lehké": [x.strip() for x in CONFIG.get('Wardrobe', 'light_top', fallback='tričko').split(',')],
        "střední": [x.strip() for x in CONFIG.get('Wardrobe', 'medium_top', fallback='svetr').split(',')],
        "teplé": [x.strip() for x in CONFIG.get('Wardrobe', 'warm_top', fallback='fleece').split(',')],
        "velmi_teplé": [x.strip() for x in CONFIG.get('Wardrobe', 'very_warm_top', fallback='bunda').split(',')]
    },
    "spodní": {
        "lehké": [x.strip() for x in CONFIG.get('Wardrobe', 'light_bottom', fallback='kraťasy').split(',')],
        "teplé": [x.strip() for x in CONFIG.get('Wardrobe', 'warm_bottom', fallback='džíny').split(',')]
    },
    "doplňky": {
        "déšť": [x.strip() for x in CONFIG.get('Wardrobe', 'rain_accessories', fallback='deštník').split(',')],
        "zima": [x.strip() for x in CONFIG.get('Wardrobe', 'cold_accessories', fallback='čepice').split(',')],
        "slunce": [x.strip() for x in CONFIG.get('Wardrobe', 'sun_accessories', fallback='brýle').split(',')]
    }
}

# Tiskárna
if not DRY_RUN:
    PRINTER_VENDOR_ID = int(CONFIG.get('Printer', 'vendor_id', fallback='0x0416'), 16)
    PRINTER_PRODUCT_ID = int(CONFIG.get('Printer', 'product_id', fallback='0x5011'), 16)

# ====== ČESKÉ SVÁTKY 2025-2026 ======
SVATKY = {
    "01-01": "Nový rok, Den obnovy samostatného českého státu",
    "04-18": "Velký pátek",
    "04-21": "Velikonoční pondělí",
    "05-01": "Svátek práce",
    "05-08": "Den vítězství",
    "07-05": "Den slovanských věrozvěstů Cyrila a Metoděje",
    "07-06": "Den upálení mistra Jana Husa",
    "09-28": "Den české státnosti",
    "10-28": "Den vzniku samostatného československého státu",
    "11-17": "Den boje za svobodu a demokracii",
    "12-24": "Štědrý den",
    "12-25": "1. svátek vánoční",
    "12-26": "2. svátek vánoční",
}

# ====== JMENINY ======
JMENINY = {
    # Leden
    "01-01": "Nový rok", "01-02": "Karina", "01-03": "Radmila", "01-04": "Diana",
    "01-05": "Dalimil", "01-06": "Tři králové", "01-07": "Vilma", "01-08": "Čestmír",
    "01-09": "Vladan", "01-10": "Břetislav", "01-11": "Bohdana", "01-12": "Pravoslav",
    "01-13": "Edita", "01-14": "Radovan", "01-15": "Alice", "01-16": "Ctirad",
    "01-17": "Drahoslav", "01-18": "Vladislav", "01-19": "Doubravka", "01-20": "Ilona",
    "01-21": "Běla", "01-22": "Slavomír", "01-23": "Zdeněk", "01-24": "Milena",
    "01-25": "Miloš", "01-26": "Zora", "01-27": "Ingrid", "01-28": "Otýlie",
    "01-29": "Zdislava", "01-30": "Robin", "01-31": "Marika",
    
    # Únor
    "02-01": "Hynek", "02-02": "Nela", "02-03": "Blažej", "02-04": "Jarmila",
    "02-05": "Dobromila", "02-06": "Vanda", "02-07": "Veronika", "02-08": "Milada",
    "02-09": "Apolena", "02-10": "Mojmír", "02-11": "Božena", "02-12": "Slavěna",
    "02-13": "Věnceslav", "02-14": "Valentýn", "02-15": "Jiřina", "02-16": "Ljuba",
    "02-17": "Miloslava", "02-18": "Gizela", "02-19": "Patrik", "02-20": "Oldřich",
    "02-21": "Lenka", "02-22": "Petr", "02-23": "Svatopluk", "02-24": "Matěj",
    "02-25": "Liliana", "02-26": "Dorota", "02-27": "Alexandr", "02-28": "Lumír",
    "02-29": "Horymír",
    
    # Březen
    "03-01": "Bedřich", "03-02": "Anežka", "03-03": "Kamil", "03-04": "Stela",
    "03-05": "Kazimír", "03-06": "Miroslav", "03-07": "Tomáš", "03-08": "Gabriela",
    "03-09": "Františka", "03-10": "Viktorie", "03-11": "Anděla", "03-12": "Řehoř",
    "03-13": "Růžena", "03-14": "Rút/Matylda", "03-15": "Ida", "03-16": "Elena/Herbert",
    "03-17": "Vlastimil", "03-18": "Eduard", "03-19": "Josef", "03-20": "Světlana",
    "03-21": "Radek", "03-22": "Leona", "03-23": "Ivona", "03-24": "Gabriel",
    "03-25": "Marián", "03-26": "Emanuel", "03-27": "Dita", "03-28": "Soňa",
    "03-29": "Taťána", "03-30": "Arnošt", "03-31": "Kvido",
    
    # Duben
    "04-01": "Hugo", "04-02": "Erika", "04-03": "Richard", "04-04": "Ivana",
    "04-05": "Miroslava", "04-06": "Vendula", "04-07": "Heřman/Hermína", "04-08": "Ema",
    "04-09": "Dušan", "04-10": "Darja", "04-11": "Izabela", "04-12": "Julius",
    "04-13": "Aleš", "04-14": "Vincenc", "04-15": "Anastázie", "04-16": "Irena",
    "04-17": "Rudolf", "04-18": "Valérie", "04-19": "Rostislav", "04-20": "Marcela",
    "04-21": "Alexandra", "04-22": "Evženie", "04-23": "Vojtěch", "04-24": "Jiří",
    "04-25": "Marek", "04-26": "Oto", "04-27": "Jaroslav", "04-28": "Vlastislav",
    "04-29": "Robert", "04-30": "Blahoslav",
    
    # Květen
    "05-01": "Svátek práce", "05-02": "Zikmund", "05-03": "Alexej", "05-04": "Květoslav",
    "05-05": "Klaudie", "05-06": "Radoslav", "05-07": "Stanislav", "05-08": "Den vítězství",
    "05-09": "Ctibor", "05-10": "Blažena", "05-11": "Svatava", "05-12": "Pankrác",
    "05-13": "Servác", "05-14": "Bonifác", "05-15": "Žofie", "05-16": "Přemysl",
    "05-17": "Aneta", "05-18": "Nataša", "05-19": "Ivo", "05-20": "Zbyšek",
    "05-21": "Monika", "05-22": "Emil", "05-23": "Vladimír", "05-24": "Jana",
    "05-25": "Viola", "05-26": "Filip", "05-27": "Valdemar", "05-28": "Vilém",
    "05-29": "Maxmilián", "05-30": "Ferdinand", "05-31": "Kamila",
    
    # Červen
    "06-01": "Laura", "06-02": "Jarmil", "06-03": "Tamara", "06-04": "Dalibor",
    "06-05": "Dobroslav", "06-06": "Norbert", "06-07": "Iveta/Robert", "06-08": "Medard",
    "06-09": "Stanislava", "06-10": "Gita", "06-11": "Bruno", "06-12": "Antonie",
    "06-13": "Antonín", "06-14": "Roland", "06-15": "Vít", "06-16": "Zbyněk",
    "06-17": "Adolf", "06-18": "Milan", "06-19": "Leoš", "06-20": "Květa",
    "06-21": "Alois", "06-22": "Pavla", "06-23": "Zdeňka", "06-24": "Jan",
    "06-25": "Ivan", "06-26": "Adriana", "06-27": "Ladislav", "06-28": "Lubomír",
    "06-29": "Petr a Pavel", "06-30": "Šárka",
    
    # Červenec
    "07-01": "Jaroslava", "07-02": "Patricie", "07-03": "Radomír", "07-04": "Prokop",
    "07-05": "Cyril a Metoděj", "07-06": "Jan Hus", "07-07": "Bohuslava", "07-08": "Nora",
    "07-09": "Drahoslava", "07-10": "Libuše/Amálie", "07-11": "Olga", "07-12": "Bořek",
    "07-13": "Markéta", "07-14": "Karolína", "07-15": "Jindřich", "07-16": "Luboš",
    "07-17": "Martina", "07-18": "Drahomíra", "07-19": "Čeněk", "07-20": "Ilja",
    "07-21": "Vítězslav", "07-22": "Magdaléna", "07-23": "Libor", "07-24": "Kristýna",
    "07-25": "Jakub", "07-26": "Anna", "07-27": "Věroslav", "07-28": "Viktor",
    "07-29": "Marta", "07-30": "Bořivoj", "07-31": "Ignác",
    
    # Srpen
    "08-01": "Oskar", "08-02": "Gustav", "08-03": "Miluše", "08-04": "Dominik",
    "08-05": "Kristián", "08-06": "Oldřiška", "08-07": "Lada", "08-08": "Soběslav",
    "08-09": "Roman", "08-10": "Vavřinec", "08-11": "Zuzana", "08-12": "Klára",
    "08-13": "Alena", "08-14": "Alan", "08-15": "Hana", "08-16": "Jáchym",
    "08-17": "Petra", "08-18": "Helena", "08-19": "Ludvík", "08-20": "Bernard",
    "08-21": "Johana", "08-22": "Bohuslav", "08-23": "Sandra", "08-24": "Bartoloměj",
    "08-25": "Radim", "08-26": "Luděk", "08-27": "Otakar", "08-28": "Augustýn",
    "08-29": "Evelína", "08-30": "Vladěna", "08-31": "Pavlína",
    
    # Září
    "09-01": "Linda/Samuel", "09-02": "Adéla", "09-03": "Bronislav", "09-04": "Jindřiška",
    "09-05": "Boris", "09-06": "Boleslav", "09-07": "Regína", "09-08": "Mariana",
    "09-09": "Daniela", "09-10": "Irma", "09-11": "Denisa", "09-12": "Marie",
    "09-13": "Lubor", "09-14": "Radka", "09-15": "Jolana", "09-16": "Ludmila",
    "09-17": "Naděžda", "09-18": "Kryštof", "09-19": "Zita", "09-20": "Oleg",
    "09-21": "Matouš", "09-22": "Darina", "09-23": "Berta", "09-24": "Jaromír",
    "09-25": "Zlata", "09-26": "Andrea", "09-27": "Jonáš", "09-28": "Václav",
    "09-29": "Michal", "09-30": "Jeroným",
    
    # Říjen
    "10-01": "Igor", "10-02": "Olivie/Oliver", "10-03": "Bohumil", "10-04": "František",
    "10-05": "Eliška", "10-06": "Hanuš", "10-07": "Justýna", "10-08": "Věra",
    "10-09": "Štefan/Sára", "10-10": "Marina", "10-11": "Andrej", "10-12": "Marcel",
    "10-13": "Renáta", "10-14": "Agáta", "10-15": "Tereza", "10-16": "Havel",
    "10-17": "Hedvika", "10-18": "Lukáš", "10-19": "Michaela", "10-20": "Vendelín",
    "10-21": "Brigita", "10-22": "Sabina", "10-23": "Teodor", "10-24": "Nina",
    "10-25": "Beáta", "10-26": "Erik", "10-27": "Šarlota/Zoe", "10-28": "Den vzniku ČSR",
    "10-29": "Silvie", "10-30": "Tadeáš", "10-31": "Štěpánka",
    
    # Listopad
    "11-01": "Felix", "11-02": "Památka zesnulých", "11-03": "Hubert", "11-04": "Karel",
    "11-05": "Miriam", "11-06": "Liběna", "11-07": "Saskie", "11-08": "Bohdan",
    "11-09": "Bohdan", "11-10": "Evžen", "11-11": "Martin", "11-12": "Benedikt",
    "11-13": "Tibor", "11-14": "Sáva", "11-15": "Leopold", "11-16": "Otmar",
    "11-17": "Den boje za svobodu", "11-18": "Romana", "11-19": "Alžběta", "11-20": "Nikola",
    "11-21": "Albert", "11-22": "Cecílie", "11-23": "Klement", "11-24": "Emílie",
    "11-25": "Kateřina", "11-26": "Artur", "11-27": "Xénie", "11-28": "René",
    "11-29": "Zina", "11-30": "Ondřej",
    
    # Prosinec
    "12-01": "Iva", "12-02": "Blanka", "12-03": "Svatoslav", "12-04": "Barbora",
    "12-05": "Jitka", "12-06": "Mikuláš", "12-07": "Ambrož/Benjamín", "12-08": "Květoslava",
    "12-09": "Vratislav", "12-10": "Julie", "12-11": "Dana", "12-12": "Simona",
    "12-13": "Lucie", "12-14": "Lýdie", "12-15": "Radana/Radan", "12-16": "Albína",
    "12-17": "Daniel", "12-18": "Miloslav", "12-19": "Ester", "12-20": "Dagmar",
    "12-21": "Natálie", "12-22": "Šimon", "12-23": "Vlasta", "12-24": "Štědrý den",
    "12-25": "1. svátek vánoční", "12-26": "2. svátek vánoční", "12-27": "Žaneta", "12-28": "Bohumila",
    "12-29": "Judita", "12-30": "David", "12-31": "Silvestr",
}

# ====== MAPOVÁNÍ ZNAMENÍ ======
ZVEROKRUH_CZ = {
    "aries": "Beran", "taurus": "Býk", "gemini": "Blíženci",
    "cancer": "Rak", "leo": "Lev", "virgo": "Panna",
    "libra": "Váhy", "scorpio": "Štír", "sagittarius": "Střelec",
    "capricorn": "Kozoroh", "aquarius": "Vodnář", "pisces": "Ryby"
}

# ====== VTIPY ======
VTIPY = [
    "Proč programátoři preferují tmavý režim?\nProtože světlo přitahuje bugy!",
    "Jdu k doktorovi: 'Doktore, myslím, že jsem neviditelný.'\n'Kdo to tam mluví?'",
    "Proč nemůže nos měřit 30 cm?\nProtože pak by to byla noha!",
    "Co dělá medvěd v knihovně?\nČte medvědí příběhy!",
    "Jak se učí stromy?\nZ kořenů!",
    "Proč si počítač vzal svetr?\nProtože měl Windows!",
    "Co řekne chemik, když najde dva atomy hélia?\nHeHe!",
    "Proč tučňáci nepadají?\nProtože jsou dobrý tanečníci na ledě!",
    "Jsem na dietě už 2 týdny.\nZhubl jsem 14 dní!",
    "Jak zavoláš psa, který dělá kouzla?\nLabrakadabrador!",
    "Proč nemůžeš věřit atomům?\nProtože tvoří všechno!",
    "Co řekl Buddha kelnerovi?\n'Udělej mě jedním se vším.'",
    "Proč kráva skočila přes měsíc?\nProtože farmář měl studené ruce!",
    "Jak se jmenuje medvěd bez zubů?\nGumový medvídek!",
    "Co dělá včela když je zima?\nPuťka!",
]

# ====== TŘÍDA PRO TESTOVACÍ TISK ======
class DryRunPrinter:
    """Simuluje tiskárnu - vypisuje na konzoli"""
    
    def __init__(self):
        self.align = 'left'
        self.text_type = 'normal'
        self.width = 1
        self.height = 1
        print("\n" + "="*50)
        print("TESTOVACÍ REŽIM - SIMULACE TISKU")
        print("="*50 + "\n")
    
    def set(self, align=None, text_type=None, width=None, height=None):
        if align:
            self.align = align
        if text_type:
            self.text_type = text_type
        if width:
            self.width = width
        if height:
            self.height = height
    
    def text(self, text):
        if self.align == 'center':
            lines = text.split('\n')
            for line in lines:
                if line:
                    print(line.center(50))
                else:
                    print()
        else:
            if self.text_type == 'B':
                print(f"\033[1m{text}\033[0m", end='')
            else:
                print(text, end='')
    
    def cut(self):
        print("\n" + "="*50)
        print("KONEC TISKU")
        print("="*50 + "\n")

# ====== FUNKCE ======

def get_weather():
    """Získá aktuální počasí"""
    if not OPENWEATHER_API_KEY:
        print("Varování: OpenWeatherMap API klíč není nastaven")
        return None
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY},{COUNTRY_CODE}&appid={OPENWEATHER_API_KEY}&units=metric&lang=cz"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        return {
            "teplota": round(data["main"]["temp"]),
            "pocit": round(data["main"]["feels_like"]),
            "popis": data["weather"][0]["description"],
            "vlhkost": data["main"]["humidity"],
            "vitr": round(data["wind"]["speed"] * 3.6),
            "dest": "rain" in data or "drizzle" in data["weather"][0]["main"].lower(),
            "snih": "snow" in data["weather"][0]["main"].lower(),
            "oblacnost": data["clouds"]["all"]
        }
    except Exception as e:
        print(f"Chyba při získávání počasí: {e}")
        return None

def get_horoskop():
    """Získá horoskop z API"""
    try:
        url = f"https://aztro.sameerkumar.website/?sign={ZVEROKRUH}&day=today"
        response = requests.post(url, timeout=10)
        data = response.json()
        
        return {
            "popis": data.get("description", "Horoskop není dostupný."),
            "stesti": data.get("lucky_number", "?"),
            "barva": data.get("color", "?"),
            "nalada": data.get("mood", "?")
        }
    except Exception as e:
        print(f"Chyba při získávání horoskopu: {e}")
        offline_horoskopy = [
            "Dnes je skvělý den pro nové začátky.",
            "Buďte pozorní k detailům.",
            "Komunikace bude klíčem k úspěchu.",
            "Důvěřujte své intuici.",
            "Dobrý den pro kreativitu."
        ]
        return {
            "popis": random.choice(offline_horoskopy),
            "stesti": "?",
            "barva": "?",
            "nalada": "?"
        }

def get_ical_events():
    """Získá události ze všech iCal kalendářů"""
    vsechny_udalosti = []
    
    for kalendar in KALENDARE:
        if not kalendar["url"] or kalendar["url"].startswith("https://calendar.google.com/calendar/ical/xxxxx"):
            continue
        
        try:
            response = requests.get(kalendar["url"], timeout=10)
            cal = Calendar.from_ical(response.content)
            
            dnes = datetime.datetime.now(tz.tzlocal()).date()
            
            for component in cal.walk():
                if component.name == "VEVENT":
                    start = component.get('dtstart').dt
                    
                    # Převod na date pokud je datetime
                    if isinstance(start, datetime.datetime):
                        start_date = start.date()
                        start_time = start.time()
                    else:
                        start_date = start
                        start_time = None
                    
                    # Pouze dnešní události
                    if start_date == dnes:
                        vsechny_udalosti.append({
                            "cas": start_time if start_time else None,
                            "nazev": str(component.get('summary')),
                            "kalendar": kalendar["nazev"],
                            "ikona": kalendar["ikona"]
                        })
            
        except Exception as e:
            print(f"Chyba při načítání kalendáře {kalendar['nazev']}: {e}")
            continue
    
    # Seřadit podle času (celodenní nakonec)
    vsechny_udalosti.sort(key=lambda x: (x["cas"] is None, x["cas"] or datetime.time.max))
    return vsechny_udalosti

def get_rss_news(max_zprav=5):
    """Získá nejnovější zprávy z RSS"""
    zpravy = []
    
    for zdroj in RSS_ZDROJE:
        try:
            feed = feedparser.parse(zdroj["url"])
            
            for entry in feed.entries[:2]:
                titulek = entry.title
                if len(titulek) > 60:
                    titulek = titulek[:57] + "..."
                
                zpravy.append({
                    "titulek": titulek,
                    "zdroj": zdroj["nazev"]
                })
                
                if len(zpravy) >= max_zprav:
                    return zpravy
                    
        except Exception as e:
            print(f"Chyba při načítání RSS z {zdroj['nazev']}: {e}")
            continue
    
    return zpravy

def get_svatek_a_jmeniny():
    """Vrátí dnešní svátek a jmeniny"""
    dnes = datetime.datetime.now()
    klic = dnes.strftime("%m-%d")
    
    svatek = SVATKY.get(klic)
    jmeniny = JMENINY.get(klic)
    
    return svatek, jmeniny

def doporuc_obleceni(pocasi):
    """Doporučí oblečení podle počasí"""
    if not pocasi:
        return ["Nepodařilo se načíst počasí"]
    
    temp = pocasi["teplota"]
    pocit = pocasi["pocit"]
    dest = pocasi["dest"]
    vitr = pocasi["vitr"]
    
    obleceni = []
    
    if pocit < 5:
        obleceni.append(random.choice(SATNIK["vrchní"]["velmi_teplé"]))
        obleceni.append(random.choice(SATNIK["vrchní"]["teplé"]))
    elif pocit < 12:
        obleceni.append(random.choice(SATNIK["vrchní"]["teplé"]))
    elif pocit < 18:
        obleceni.append(random.choice(SATNIK["vrchní"]["střední"]))
    else:
        obleceni.append(random.choice(SATNIK["vrchní"]["lehké"]))
    
    if temp < 15:
        obleceni.append(random.choice(SATNIK["spodní"]["teplé"]))
    else:
        obleceni.append(random.choice(SATNIK["spodní"]["lehké"]))
    
    if dest:
        obleceni.append(random.choice(SATNIK["doplňky"]["déšť"]))
    if temp < 10 or vitr > 20:
        obleceni.extend(random.sample(SATNIK["doplňky"]["zima"], min(2, len(SATNIK["doplňky"]["zima"]))))
    if temp > 22 and pocasi["oblacnost"] < 50:
        obleceni.append(random.choice(SATNIK["doplňky"]["slunce"]))
    
    return obleceni

def wrap_text(text, width=32):
    """Zalomí text na řádky o dané šířce"""
    words = text.split()
    lines = []
    line = ""
    
    for word in words:
        if len(line + word) < width:
            line += word + " "
        else:
            if line:
                lines.append(line.strip())
            line = word + " "
    
    if line:
        lines.append(line.strip())
    
    return lines

def vytiskni_prehled():
    """Hlavní funkce - vytiskne denní přehled"""
    try:
        # Výběr tiskárny podle režimu
        if DRY_RUN:
            p = DryRunPrinter()
        else:
            from escpos.printer import Usb
            p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)
        
        # Hlavička
        p.set(align='center', text_type='B', width=2, height=2)
        p.text("DNESNI PREHLED\n")
        p.set(align='center', text_type='normal')
        
        datum = datetime.datetime.now()
        den_tyden = ["pondělí", "úterý", "středa", "čtvrtek", "pátek", "sobota", "neděle"]
        mesice = ["ledna", "února", "března", "dubna", "května", "června", 
                  "července", "srpna", "září", "října", "listopadu", "prosince"]
        
        den_text = f"{den_tyden[datum.weekday()]}, {datum.day}. {mesice[datum.month-1]} {datum.year}"
        p.text(f"{den_text}\n")
        
        # Svátky a jmeniny
        svatek, jmeniny = get_svatek_a_jmeniny()
        if svatek:
            p.set(text_type='B')
            p.text(f"SVATEK: {svatek}\n")
            p.set(text_type='normal')
        if jmeniny:
            p.text(f"Jmeniny: {jmeniny}\n")
        
        p.text("=" * 32 + "\n\n")
        
        # Počasí
        p.set(align='left', text_type='B')
        p.text("POCASI\n")
        p.set(text_type='normal')
        
        pocasi = get_weather()
        if pocasi:
            p.text(f"Teplota: {pocasi['teplota']}°C ")
            p.text(f"(pocit {pocasi['pocit']}°C)\n")
            p.text(f"{pocasi['popis'].capitalize()}\n")
            p.text(f"Vlhkost: {pocasi['vlhkost']}% | ")
            p.text(f"Vitr: {pocasi['vitr']} km/h\n")
        else:
            p.text("Nepodařilo se načíst počasí\n")
        
        p.text("\n")
        
        # Doporučené oblečení
        p.set(text_type='B')
        p.text("CO NA SEBE\n")
        p.set(text_type='normal')
        
        obleceni = doporuc_obleceni(pocasi)
        for item in obleceni:
            p.text(f"• {item}\n")
        
        p.text("\n")
        
        # Kalendář ze všech zdrojů
        udalosti = get_ical_events()
        if udalosti:
            p.set(text_type='B')
            p.text("KALENDAR\n")
            p.set(text_type='normal')
            
            for udalost in udalosti[:8]:
                if udalost["cas"]:
                    cas_str = udalost["cas"].strftime("%H:%M")
                else:
                    cas_str = "celodenni"
                
                # V dry run módu použijeme ikony, na tiskárně ASCII
                if DRY_RUN:
                    p.text(f"{udalost['ikona']} {cas_str:>10} ")
                else:
                    # ASCII alternativa pro tiskárnu
                    prefix = "[O]" if udalost["kalendar"] == "Osobní" else "[P]"
                    p.text(f"{prefix} {cas_str:>10} ")
                
                p.text(f"{udalost['nazev']}\n")
            
            p.text("\n")
        
        # RSS Zprávy
        zpravy = get_rss_news(max_zprav=MAX_NEWS)
        if zpravy:
            p.set(text_type='B')
            p.text("ZPRAVY\n")
            p.set(text_type='normal')
            
            for zprava in zpravy:
                lines = wrap_text(zprava['titulek'], 32)
                for line in lines:
                    p.text(f"{line}\n")
                p.text(f"  ({zprava['zdroj']})\n")
            
            p.text("\n")
        
        # Horoskop
        p.set(text_type='B')
        p.text(f"HOROSKOP ({ZVEROKRUH_CZ.get(ZVEROKRUH, ZVEROKRUH).upper()})\n")
        p.set(text_type='normal')
        
        horoskop = get_horoskop()
        lines = wrap_text(horoskop['popis'], 32)
        for line in lines:
            p.text(f"{line}\n")
        
        if horoskop['stesti'] != "?":
            p.text(f"Stestne cislo: {horoskop['stesti']}\n")
            p.text(f"Barva dne: {horoskop['barva']}\n")
        
        p.text("\n")
        
        # Vtip dne
        p.set(text_type='B')
        p.text("VTIP DNE\n")
        p.set(text_type='normal')
        
        vtip = random.choice(VTIPY)
        for radek in vtip.split('\n'):
            lines = wrap_text(radek, 32)
            for line in lines:
                p.text(f"{line}\n")
        
        # Patička
        p.text("\n" + "=" * 32 + "\n")
        p.set(align='center')
        p.text("Hezky den!\n\n\n")
        
        # Řez papíru
        p.cut()
        
        if not DRY_RUN:
            print("Tisk dokončen!")
        
    except Exception as e:
        print(f"Chyba při tisku: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Hlavní spouštěcí funkce"""
    print(f"PrintMaster v{VERSION}")
    print(f"https://github.com/{GITHUB_REPO}")
    print("")
    
    vytiskni_prehled()

if __name__ == "__main__":
    main()
