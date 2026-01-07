#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test RSS čtečky - s vylepšenou podporou hlaviček a redirectů
"""

import requests
import feedparser

# Testovací RSS zdroje - výchozí zdroje v aplikaci
RSS_ZDROJE = [
    {'nazev': 'Novinky.cz', 'url': 'https://www.novinky.cz/rss'},
    {'nazev': 'ČT24', 'url': 'https://ct24.ceskatelevize.cz/rss/hlavni-zpravy'},
    {'nazev': 'Hospodářské noviny', 'url': 'https://ihned.cz/?p=000000_rss'},
    {'nazev': 'Seznam Zprávy', 'url': 'https://www.seznamzpravy.cz/rss'}
]

def test_rss_reader():
    """Otestuje RSS čtečku s použitím requests a hlaviček"""
    print("="*60)
    print("TEST RSS ČTEČKY - OPRAVENÁ VERZE")
    print("="*60)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for zdroj in RSS_ZDROJE:
        print(f"\nTestuji: {zdroj['nazev']}")
        print(f"URL: {zdroj['url']}")

        try:
            # Použití requests s hlavičkami
            response = requests.get(zdroj['url'], headers=headers, timeout=10, allow_redirects=True)

            print(f"  HTTP Status: {response.status_code}")

            if response.status_code != 200:
                print(f"  ❌ CHYBA: Neplatný HTTP status")
                continue

            # Parse feedu z obsahu
            feed = feedparser.parse(response.content)

            # Zkontrolovat počet zpráv
            print(f"  Počet zpráv: {len(feed.entries)}")

            if len(feed.entries) == 0:
                print(f"  ❌ CHYBA: Žádné zprávy nenalezeny!")
            else:
                print(f"  ✓ Úspěšně načteno")

                # Vypsat první 2 zprávy
                for i, entry in enumerate(feed.entries[:2], 1):
                    if hasattr(entry, 'title'):
                        titulek = entry.title
                        if len(titulek) > 60:
                            titulek = titulek[:57] + "..."
                        print(f"    {i}. {titulek}")
                    else:
                        print(f"    {i}. (zpráva bez titulku)")

        except Exception as e:
            print(f"  ❌ VÝJIMKA: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_rss_reader()
