"""
================================================================================
  GOOGLE MAPS SCRAPER — Selenium + openpyxl
  Author  : (your name here)
  Version : 1.0
================================================================================

QUICK-START
-----------
1. Install dependencies:
       pip install selenium openpyxl webdriver-manager

2. Make sure Google Chrome is installed on your machine.

3. Run:
       python google_maps_scraper.py

4. Enter your search query when prompted (e.g. "restaurants in Lahore").

THINGS YOU MUST CHANGE  ←←←  read these before running
--------------------------------------------------------
  • SCROLL_PAUSE       : seconds to wait between result-panel scrolls (increase on slow internet)
  • PAGE_LOAD_WAIT     : seconds after opening a listing (increase on slow machines)
  • TARGET_RESULTS     : how many listings to scrape (set to 50000 for full run)
  • OUTPUT_FILE        : name / path of the Excel file to write
  • HEADLESS           : set True to run Chrome without a visible window (faster, no UI)

NOTE ON 50 000 RESULTS
-----------------------
Google Maps typically caps the results panel at ~120 listings per search, even
if more exist. To get 50 000 results you must either:
  a) Run many different, narrower queries (e.g. city-by-city, category-by-category)
     and append them all to the same Excel file — this script supports that via
     APPEND_MODE = True.
  b) Use Google Places API (paid, but reliable for bulk data).
The script handles the scrolling / pagination Google does allow automatically.
================================================================================
"""

# ──────────────────────────────────────────────────────────────
#  IMPORTS
# ──────────────────────────────────────────────────────────────
import time
import re
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WDM = True
except ImportError:
    USE_WDM = False


# ══════════════════════════════════════════════════════════════
#  ⚙  USER-CONFIGURABLE SETTINGS  — CHANGE THESE AS NEEDED
# ══════════════════════════════════════════════════════════════

SCROLL_PAUSE    = 2          # ← seconds to pause between result-list scrolls
PAGE_LOAD_WAIT  = 4          # ← seconds to wait after opening each listing
TARGET_RESULTS  = 120        # ← max listings to collect per query run
OUTPUT_FILE     = "google_maps_results.xlsx"   # ← output Excel filename
APPEND_MODE     = False      # ← True = add new results below existing rows
HEADLESS        = False      # ← True = no Chrome window (invisible mode)

# Chrome profile directory (optional).
# Set to a real path to reuse a logged-in profile (avoids CAPTCHAs better).
# Example on Windows: r"C:\Users\YourName\AppData\Local\Google\Chrome\User Data"
# Leave as "" to use a fresh temporary profile.
CHROME_PROFILE_DIR = ""

# ══════════════════════════════════════════════════════════════
#  XPATH / CSS SELECTORS  — update if Google changes its HTML
# ══════════════════════════════════════════════════════════════
#
#  Google Maps updates its DOM regularly. If something stops working,
#  open Chrome DevTools (F12) on maps.google.com, inspect the element,
#  and replace the XPath/selector below.

# The scrollable results panel on the left side
RESULTS_PANEL_XPATH  = '//div[@role="feed"]'

# Each individual result card in the panel
RESULT_CARD_XPATH    = '//div[@role="feed"]//a[@class and @href and contains(@href, "/maps/place/")]'

# ── Inside a listing page ──────────────────────────────────────

# Business name (h1 heading at the top)
NAME_XPATH           = '//h1[contains(@class,"DUwDvf")]'

# Star rating  e.g. "4.5"
RATING_XPATH         = '//div[@class="F7nice "]//span[@aria-hidden="true"]'

# Review count  e.g. "(1,234)"
REVIEW_COUNT_XPATH   = '//div[@class="F7nice "]//span[contains(@aria-label,"reviews")]'

# Address line
ADDRESS_XPATH        = '//button[@data-item-id="address"]//div[contains(@class,"Io6YTe")]'

# Phone number
PHONE_XPATH          = '//button[contains(@data-item-id,"phone")]//div[contains(@class,"Io6YTe")]'

# Website URL
WEBSITE_XPATH        = '//a[@data-item-id="authority"]//div[contains(@class,"Io6YTe")]'

# Category / type  e.g. "Italian restaurant"
CATEGORY_XPATH       = '//button[contains(@jsaction,"category")]'

# Business hours — the summary line shown on the listing
HOURS_XPATH          = '//div[@class="t39EBf GUrTXd"]//span'

# "Open now" / "Closed" status
OPEN_STATUS_XPATH    = '//span[contains(@class,"ZDu9vd")]//span'

# Latitude / longitude (extracted from the URL)
# Google embeds coords in the URL as  @lat,lng  — no separate XPath needed.

# Plus Code  e.g. "QXQR+49"
PLUS_CODE_XPATH      = '//button[@data-item-id="oloc"]//div[contains(@class,"Io6YTe")]'

# Description / "About" tab text (not always present)
DESCRIPTION_XPATH    = '//div[@class="PYvSYb"]'

# Price level  e.g. "$$"
PRICE_XPATH          = '//span[contains(@aria-label,"Price")]'

# ══════════════════════════════════════════════════════════════
#  EXCEL COLUMN DEFINITIONS
# ══════════════════════════════════════════════════════════════

COLUMNS = [
    "No.",
    "Name",
    "Category",
    "Rating",
    "Reviews",
    "Address",
    "Phone",
    "Website",
    "Hours",
    "Open Status",
    "Price Level",
    "Latitude",
    "Longitude",
    "Plus Code",
    "Description",
    "Google Maps URL",
    "Search Query",
]

# ──────────────────────────────────────────────────────────────
#  HELPER: safe element text getter
# ──────────────────────────────────────────────────────────────

def get_text(driver, xpath, default=""):
    """Return stripped text from the first matching element, or default."""
    try:
        el = driver.find_element(By.XPATH, xpath)
        return el.text.strip()
    except NoSuchElementException:
        return default


def get_attr(driver, xpath, attr, default=""):
    """Return an attribute value from the first matching element, or default."""
    try:
        el = driver.find_element(By.XPATH, xpath)
        return (el.get_attribute(attr) or "").strip()
    except NoSuchElementException:
        return default


# ──────────────────────────────────────────────────────────────
#  HELPER: extract lat/lng from the current URL
# ──────────────────────────────────────────────────────────────

def extract_coords(url):
    """
    Google Maps URLs contain coordinates like:  @25.1234,67.4321,17z
    Returns (lat_str, lng_str) or ("", "").
    """
    match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if match:
        return match.group(1), match.group(2)
    return "", ""


# ──────────────────────────────────────────────────────────────
#  CHROME DRIVER SETUP
# ──────────────────────────────────────────────────────────────

def build_driver():
    opts = Options()

    if HEADLESS:
        opts.add_argument("--headless=new")  # Chrome ≥ 112 headless flag
        opts.add_argument("--window-size=1920,1080")

    # Reduce bot-detection fingerprint
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--lang=en-US,en;q=0.9")

    # ← Optional: use an existing Chrome profile to avoid CAPTCHAs
    if CHROME_PROFILE_DIR:
        opts.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")

    if USE_WDM:
        service = Service(ChromeDriverManager().install())
    else:
        # ← If webdriver-manager is not installed, put the chromedriver path here:
        service = Service("/usr/local/bin/chromedriver")  # CHANGE THIS PATH

    driver = webdriver.Chrome(service=service, options=opts)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
    )
    return driver


# ──────────────────────────────────────────────────────────────
#  EXCEL WORKBOOK SETUP
# ──────────────────────────────────────────────────────────────

def setup_workbook():
    """Create (or load existing) workbook and return (wb, ws, start_row)."""
    import os

    if APPEND_MODE and os.path.exists(OUTPUT_FILE):
        wb = openpyxl.load_workbook(OUTPUT_FILE)
        ws = wb.active
        start_row = ws.max_row + 1
        print(f"[Excel] Appending from row {start_row}")
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Maps Data"

        # ── Header row styling ──
        header_fill = PatternFill("solid", start_color="1F4E79", end_color="1F4E79")
        header_font = Font(bold=True, color="FFFFFF", name="Arial", size=11)

        for col_idx, col_name in enumerate(COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.fill   = header_fill
            cell.font   = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Freeze the header row
        ws.freeze_panes = "A2"

        # ── Column widths (tweak to taste) ──
        widths = [6, 30, 20, 8, 10, 40, 18, 35, 25, 12, 10, 12, 12, 14, 40, 50, 25]
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w

        start_row = 2

    return wb, ws, start_row


# ──────────────────────────────────────────────────────────────
#  SCRAPE A SINGLE LISTING
# ──────────────────────────────────────────────────────────────

def scrape_listing(driver, query, row_no):
    """
    Scrapes all data fields from the currently-open listing page.
    Returns a list matching COLUMNS order.
    """
    time.sleep(PAGE_LOAD_WAIT)          # wait for the page to fully load

    url     = driver.current_url
    lat, lng = extract_coords(url)

    name        = get_text(driver, NAME_XPATH)
    rating      = get_text(driver, RATING_XPATH)
    reviews_raw = get_text(driver, REVIEW_COUNT_XPATH)
    reviews     = re.sub(r"[^\d]", "", reviews_raw)   # keep digits only
    address     = get_text(driver, ADDRESS_XPATH)
    phone       = get_text(driver, PHONE_XPATH)
    website     = get_text(driver, WEBSITE_XPATH)
    category    = get_text(driver, CATEGORY_XPATH)
    hours       = get_text(driver, HOURS_XPATH)
    open_status = get_text(driver, OPEN_STATUS_XPATH)
    plus_code   = get_text(driver, PLUS_CODE_XPATH)
    description = get_text(driver, DESCRIPTION_XPATH)
    price       = get_text(driver, PRICE_XPATH)

    return [
        row_no,
        name,
        category,
        rating,
        reviews,
        address,
        phone,
        website,
        hours,
        open_status,
        price,
        lat,
        lng,
        plus_code,
        description,
        url,
        query,
    ]


# ──────────────────────────────────────────────────────────────
#  SCROLL THE RESULTS PANEL
# ──────────────────────────────────────────────────────────────

def scroll_results_panel(driver, target):
    """
    Scrolls the left-side results feed until `target` cards are visible
    or no more results load.  Returns a list of href URLs.
    """
    wait = WebDriverWait(driver, 15)

    try:
        panel = wait.until(EC.presence_of_element_located((By.XPATH, RESULTS_PANEL_XPATH)))
    except TimeoutException:
        print("[!] Results panel not found — check RESULTS_PANEL_XPATH")
        return []

    seen_urls = []
    prev_count = 0
    stall_count = 0

    while len(seen_urls) < target:
        # Collect all result card hrefs currently in the DOM
        cards = driver.find_elements(By.XPATH, RESULT_CARD_XPATH)
        urls  = list(dict.fromkeys(c.get_attribute("href") for c in cards if c.get_attribute("href")))
        seen_urls = urls

        print(f"  [scroll] {len(seen_urls)} results visible …", end="\r")

        if len(seen_urls) >= target:
            break

        # Scroll the panel to the bottom
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", panel)
        time.sleep(SCROLL_PAUSE)

        # Detect "You've reached the end" message
        end_texts = driver.find_elements(By.XPATH, '//span[contains(text(),"end of results") or contains(text(),"reached the end")]')
        if end_texts:
            print("\n  [scroll] End of results reached.")
            break

        # Stall detection — stop if count hasn't grown for 5 cycles
        if len(seen_urls) == prev_count:
            stall_count += 1
            if stall_count >= 5:
                print("\n  [scroll] No new results loading — stopping scroll.")
                break
        else:
            stall_count = 0

        prev_count = len(seen_urls)

    print()
    return seen_urls[:target]


# ──────────────────────────────────────────────────────────────
#  MAIN SCRAPER FUNCTION
# ──────────────────────────────────────────────────────────────

def run_scraper():
    # ── Ask user for the search query ──
    print("=" * 60)
    print("  GOOGLE MAPS SCRAPER")
    print("=" * 60)
    query = input("\nEnter your Google Maps search query:\n> ").strip()
    if not query:
        print("No query entered. Exiting.")
        sys.exit(1)

    print(f"\n[*] Target: {TARGET_RESULTS} results")
    print(f"[*] Output : {OUTPUT_FILE}")
    print(f"[*] Query  : {query}\n")

    # ── Build driver and workbook ──
    driver = build_driver()
    wb, ws, start_row = setup_workbook()

    try:
        # ── Open Google Maps ──
        print("[1] Opening Google Maps …")
        driver.get("https://www.google.com/maps")
        time.sleep(3)

        # ── Accept cookies if the consent banner appears (EU regions) ──
        try:
            accept_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//span[text()="Accept all"]]'))
            )
            accept_btn.click()
            time.sleep(1)
        except TimeoutException:
            pass   # no consent banner — fine

        # ── Type query in the search box ──
        print("[2] Searching …")
        # ← CHANGE THIS XPATH if the search box moves
        search_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//input[@id="ucc-1"]'))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)
        time.sleep(4)

        # ── Scroll to collect listing URLs ──
        print("[3] Collecting listing URLs from results panel …")
        listing_urls = scroll_results_panel(driver, TARGET_RESULTS)

        if not listing_urls:
            print("[!] No listings found. The XPaths may need updating.")
            return

        print(f"[*] Found {len(listing_urls)} listing URLs. Starting detail scrape …\n")

        # ── Visit each listing and scrape ──
        row_no    = start_row - 1   # will be incremented before first use
        saved     = 0

        for idx, url in enumerate(listing_urls, start=1):
            print(f"[{idx}/{len(listing_urls)}] Scraping: {url[:80]} …")

            try:
                driver.get(url)
            except Exception as e:
                print(f"  [!] Failed to open listing: {e}")
                continue

            row_no += 1
            try:
                row_data = scrape_listing(driver, query, row_no)
            except Exception as e:
                print(f"  [!] Error scraping listing: {e}")
                row_data = [row_no] + [""] * (len(COLUMNS) - 1)

            # ── Write row to Excel ──
            ws.append(row_data)

            # Alternate row colour for readability
            fill_color = "D6E4F0" if row_no % 2 == 0 else "FFFFFF"
            row_fill   = PatternFill("solid", start_color=fill_color, end_color=fill_color)
            for cell in ws[ws.max_row]:
                cell.fill      = row_fill
                cell.font      = Font(name="Arial", size=10)
                cell.alignment = Alignment(vertical="center", wrap_text=True)

            # Save every 10 rows so you don't lose progress on a crash
            saved += 1
            if saved % 10 == 0:
                wb.save(OUTPUT_FILE)
                print(f"  [✓] Auto-saved at row {ws.max_row}")

        # ── Final save ──
        wb.save(OUTPUT_FILE)
        print(f"\n[✓] Done! {saved} listings saved to '{OUTPUT_FILE}'")

    finally:
        driver.quit()


# ──────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_scraper()
