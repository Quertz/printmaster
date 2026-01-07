#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pro ověření funkcí weather API a kalendáře
"""

def test_location_detection():
    """Test detekce různých typů lokací"""
    print("="*60)
    print("TEST DETEKCE LOKACÍ PRO WEATHER API")
    print("="*60)

    test_cases = [
        ("Prague", "město"),
        ("11000", "PSČ"),
        ("50.0755,14.4378", "souřadnice"),
        ("New York", "město"),
        ("10001", "PSČ"),
        ("40.7128,-74.0060", "souřadnice"),
    ]

    for location, expected_type in test_cases:
        location = location.strip()

        if ',' in location:
            parts = location.split(',')
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                detected_type = "souřadnice"
            except ValueError:
                detected_type = "město"
        elif location.replace(' ', '').isdigit() or (len(location) <= 10 and any(c.isdigit() for c in location)):
            detected_type = "PSČ"
        else:
            detected_type = "město"

        status = "✓" if detected_type == expected_type else "✗"
        print(f"{status} '{location}' → {detected_type} (očekáváno: {expected_type})")

def test_webcal_conversion():
    """Test převodu webcal:// protokolu"""
    print("\n" + "="*60)
    print("TEST PŘEVODU WEBCAL:// PROTOKOLU")
    print("="*60)

    test_urls = [
        ("webcal://p27-caldav.icloud.com/published/2/test", "https://p27-caldav.icloud.com/published/2/test"),
        ("webcals://example.com/calendar.ics", "https://example.com/calendar.ics"),
        ("https://calendar.google.com/calendar/ical/test", "https://calendar.google.com/calendar/ical/test"),
        ("http://example.com/cal.ics", "http://example.com/cal.ics"),
    ]

    for original_url, expected_url in test_urls:
        url = original_url
        if url.startswith("webcal://"):
            url = url.replace("webcal://", "https://", 1)
        elif url.startswith("webcals://"):
            url = url.replace("webcals://", "https://", 1)

        status = "✓" if url == expected_url else "✗"
        print(f"{status} {original_url}")
        print(f"   → {url}")
        if url != expected_url:
            print(f"   Očekáváno: {expected_url}")

def main():
    """Hlavní test funkce"""
    test_location_detection()
    test_webcal_conversion()

    print("\n" + "="*60)
    print("TEST DOKONČEN")
    print("="*60)

if __name__ == "__main__":
    main()
