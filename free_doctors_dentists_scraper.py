import argparse
import csv
import json
import re
import time
from datetime import datetime
from urllib.parse import quote_plus

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        TimeoutException,
                                        WebDriverException)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


US_STATE_MAP = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
    'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
    'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
    'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
    'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
    'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
    'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
    'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
    'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
    'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
    'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
}

PROFESSION_TO_TAXONOMY = {
    'doctor': 'Allopathic & Osteopathic Physicians',
    'physician': 'Allopathic & Osteopathic Physicians',
    'dentist': 'Dentist',
    'dental': 'Dentist',
    'pediatrician': 'Pediatrics',
    'cardiologist': 'Cardiovascular Disease',
    'psychiatrist': 'Psychiatry',
    'dermatologist': 'Dermatology',
    'ophthalmologist': 'Ophthalmology',
    'optometrist': 'Optometry',
    'chiropractor': 'Chiropractic',
}

NPI_API_URL = 'https://npiregistry.cms.hhs.gov/api/'
PHONE_REGEX = re.compile(r'\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}')
WEBSITE_REGEX = re.compile(r'https?://[^\s"\']+')


def normalize_state(city_or_state_or_location: str) -> str | None:
    if not city_or_state_or_location:
        return None
    value = city_or_state_or_location.strip().lower()
    if len(value) == 2 and value.isalpha():
        return value.upper()
    return US_STATE_MAP.get(value)


def parse_location(location: str) -> tuple[str | None, str | None]:
    if not location:
        return None, None

    parts = [part.strip() for part in location.split(',') if part.strip()]
    if len(parts) == 1:
        state_code = normalize_state(parts[0])
        return (None, state_code) if state_code else (parts[0], None)
    if len(parts) >= 2:
        state_code = normalize_state(parts[-1])
        city = parts[0]
        return city, state_code
    return None, None


def profession_to_taxonomy(profession: str) -> str:
    profession_key = profession.strip().lower()
    return PROFESSION_TO_TAXONOMY.get(profession_key, profession_key.title())


def safe_text(value):
    if value is None:
        return 'N/A'
    value = str(value).strip()
    return value if value else 'N/A'


def make_csv_filename(profession: str, location: str) -> str:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_location = re.sub(r'[^A-Za-z0-9]+', '_', location).strip('_')
    safe_profession = re.sub(r'[^A-Za-z0-9]+', '_', profession).strip('_')
    return f'{safe_profession}_{safe_location}_{timestamp}.csv'


def save_records(records: list[dict], profession: str, location: str) -> str:
    if not records:
        raise ValueError('No records to save.')
    filename = make_csv_filename(profession, location)
    df = pd.DataFrame(records)
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f'✅ Saved {len(records)} records to {filename}')
    return filename


def npi_query(profession: str, location: str, max_results: int = 200) -> list[dict]:
    city, state = parse_location(location)
    if not state and not city:
        print('ℹ️  Skipping NPI registry lookup because location could not be parsed as US city/state.')
        return []

    taxonomy_description = profession_to_taxonomy(profession)
    if not state:
        print('ℹ️  State not detected; NPI registry results may be limited to city search only.')

    records = []
    page = 0
    page_size = min(200, max_results)

    while len(records) < max_results:
        params = {
            'version': '2.1',
            'enumeration_type': 'NPI-1',
            'taxonomy_description': taxonomy_description,
            'limit': page_size,
            'skip': page * page_size,
        }
        if city:
            params['city'] = city
        if state:
            params['state'] = state

        response = requests.get(NPI_API_URL, params=params, timeout=25)
        if response.status_code != 200:
            print('❌ NPI API request failed with status:', response.status_code)
            break

        payload = response.json()
        page_results = payload.get('results', [])
        if not page_results:
            break

        for item in page_results:
            if len(records) >= max_results:
                break
            records.append(convert_npi_item(item, profession, location))

        if len(page_results) < page_size:
            break
        page += 1
        time.sleep(0.5)

    print(f'✅ NPI registry returned {len(records)} records for {profession} in {location}')
    return records


def convert_npi_item(item: dict, profession: str, location: str) -> dict:
    basic = item.get('basic', {})
    addresses = item.get('addresses', [])
    location_address = next((addr for addr in addresses if addr.get('address_purpose') == 'LOCATION'), addresses[:1] or [])

    practice_address = location_address if location_address else {}
    phone = practice_address.get('telephone_number') or practice_address.get('fax_number') or 'N/A'
    website = basic.get('enumeration_type')

    return {
        'Name': safe_text(basic.get('name') or basic.get('authorized_official_telephone_number') or 'N/A'),
        'Profession': safe_text(profession),
        'Location': safe_text(location),
        'Address': safe_text(', '.join(filter(None, [practice_address.get('address_1'), practice_address.get('address_2'), practice_address.get('city'), practice_address.get('state'), practice_address.get('postal_code')]))),
        'City': safe_text(practice_address.get('city')),
        'State': safe_text(practice_address.get('state')),
        'Postal_Code': safe_text(practice_address.get('postal_code')),
        'Phone': safe_text(phone),
        'Website': 'N/A',
        'Email': 'N/A',
        'NPI': safe_text(item.get('number')),
        'Source': 'NPI Registry',
    }


def scrape_google_maps(profession: str, location: str, max_results: int = 50) -> list[dict]:
    query = quote_plus(f'{profession} in {location}')
    url = f'https://www.google.com/maps/search/{query}'

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')

    records = []
    driver = None

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@role="article"]'))
        )

        try:
            feed = driver.find_element(By.XPATH, '//*[@role="feed"]')
            for _ in range(12):
                driver.execute_script('arguments[0].scrollBy(0, 1200);', feed)
                time.sleep(1.0)
        except Exception:
            for _ in range(12):
                driver.execute_script('window.scrollBy(0, 1200);')
                time.sleep(1.0)

        cards = driver.find_elements(By.XPATH, '//*[@role="article"]')
        print(f'ℹ️  Found {len(cards)} Google Maps place cards, scraping up to {max_results}')

        for card in cards[:max_results]:
            try:
                card.click()
                time.sleep(2.0)
            except Exception:
                pass

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            record = parse_google_maps_detail(soup, profession, location)
            if record:
                records.append(record)

            if len(records) >= max_results:
                break

        print(f'✅ Google Maps fallback returned {len(records)} records')
        return records

    except WebDriverException as exc:
        print('❌ Google Maps scraping failed:', exc)
        return []

    finally:
        if driver:
            driver.quit()


def parse_google_maps_detail(soup: BeautifulSoup, profession: str, location: str) -> dict | None:
    title_el = soup.select_one('h1')
    name = safe_text(title_el.get_text()) if title_el else 'N/A'

    address = 'N/A'
    phone = 'N/A'
    website = 'N/A'
    email = 'N/A'

    address_candidate = soup.select_one('button[data-item-id="address"]')
    if address_candidate:
        address = safe_text(address_candidate.get_text())

    content_text = soup.get_text(separator=' ', strip=True)
    phone_match = PHONE_REGEX.search(content_text)
    if phone_match:
        phone = phone_match.group(0)

    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('http') and 'google.com/maps' not in href and 'googleusercontent.com' not in href:
            website = safe_text(href)
            break

    if name == 'N/A':
        return None

    return {
        'Name': name,
        'Profession': safe_text(profession),
        'Location': safe_text(location),
        'Address': address,
        'City': 'N/A',
        'State': 'N/A',
        'Postal_Code': 'N/A',
        'Phone': phone,
        'Website': website,
        'Email': email,
        'NPI': 'N/A',
        'Source': 'Google Maps',
    }


def scrape_google_search(profession: str, location: str, max_results: int = 50) -> list[dict]:
    query = quote_plus(f'{profession} in {location}')
    url = f'https://www.google.com/search?q={query}&gl=us'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    }

    response = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(response.text, 'html.parser')
    blocks = soup.select('div.g')
    records = []

    for block in blocks[:max_results]:
        title_el = block.select_one('h3')
        link_el = block.find('a', href=True)
        snippet = block.select_one('.IsZvec') or block.select_one('.VwiC3b')
        if not title_el or not link_el:
            continue

        name = safe_text(title_el.get_text())
        link = safe_text(link_el['href'])
        snippet_text = safe_text(snippet.get_text()) if snippet else 'N/A'
        phone_match = PHONE_REGEX.search(snippet_text)
        phone = phone_match.group(0) if phone_match else 'N/A'

        records.append({
            'Name': name,
            'Profession': safe_text(profession),
            'Location': safe_text(location),
            'Address': snippet_text,
            'City': 'N/A',
            'State': 'N/A',
            'Postal_Code': 'N/A',
            'Phone': phone,
            'Website': link,
            'Email': 'N/A',
            'NPI': 'N/A',
            'Source': 'Google Search',
        })

    print(f'✅ Google Search fallback returned {len(records)} records')
    return records


def prompt_for_value(prompt_text: str, default: str | None = None) -> str:
    while True:
        if default:
            value = input(f"{prompt_text} [{default}]: ").strip()
            if not value:
                return default
        else:
            value = input(f"{prompt_text}: ").strip()
        if value:
            return value
        print('Please enter a value.')


def main() -> None:
    parser = argparse.ArgumentParser(description='Free doctors/dentists finder and CSV exporter')
    parser.add_argument('-p', '--profession', help='Doctor, dentist or other provider type')
    parser.add_argument('-l', '--location', help='City, region, or state, e.g. "Los Angeles, CA" or "California"')
    parser.add_argument('-m', '--max-results', type=int, default=200, help='Maximum number of records to retrieve')
    parser.add_argument('--no-browser', action='store_true', help='Do not use Google Maps fallback browser scraping')
    args = parser.parse_args()

    profession = args.profession.strip() if args.profession else prompt_for_value(
        'Enter profession (doctor, dentist, physician, etc)'
    )
    location = args.location.strip() if args.location else prompt_for_value(
        'Enter location (city, region, or state)'
    )
    max_results = args.max_results if args.max_results and args.max_results > 0 else 200

    if not args.profession:
        print(f'Using profession: {profession}')
    if not args.location:
        print(f'Using location: {location}')

    max_results = max(10, min(max_results, 500))
    print(f'\nSearching for "{profession}" in "{location}" (max {max_results})...\n')

    records = npi_query(profession, location, max_results)
    if len(records) >= min(max_results, 20):
        print('ℹ️  Using NPI results as primary output.')
    else:
        if not args.no_browser:
            records = scrape_google_maps(profession, location, max_results)

        if not records:
            records = scrape_google_search(profession, location, max_results)

    if not records:
        print('⚠️  No records were found by the free sources.')
        return

    save_records(records[:max_results], profession, location)


if __name__ == '__main__':
    main()
