"""
================================================================================
  GOOGLE MAPS SCRAPER — Selenium + openpyxl
  Version : 2.1  (no blank rows · GPU error suppressed · PermissionError fixed)
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
  • SCROLL_PAUSE      : seconds to wait between result-panel scrolls
                        (increase on slow internet, e.g. 3–5)
  • PAGE_LOAD_WAIT    : seconds to wait after opening each listing
                        (increase on a slow machine, e.g. 5–6)
  • TARGET_RESULTS    : how many listings to scrape per run
                        (set to 50000 for a bulk run)
  • OUTPUT_FILE       : name / path of the Excel file to write
  • HEADLESS          : True = no visible Chrome window (faster)
  • CHROME_PROFILE_DIR: path to your Chrome profile (avoids CAPTCHAs)
  • RETRY_ATTEMPTS    : how many times to retry a listing before skipping

NOTE ON 50 000 RESULTS
-----------------------
Google Maps caps the results panel at ~120 listings per single search.
To collect 50 000 records run many narrower queries (city-by-city or
category-by-category) and set APPEND_MODE = True so every run adds rows
to the same Excel file without overwriting the header.
================================================================================
"""

# ──────────────────────────────────────────────────────────────
#  IMPORTS
# ──────────────────────────────────────────────────────────────
import time
import re
import sys
import os
import shutil
from datetime import datetime

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
)

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WDM = True
except ImportError:
    USE_WDM = False


# ══════════════════════════════════════════════════════════════
#  ⚙  USER-CONFIGURABLE SETTINGS  — CHANGE THESE AS NEEDED
# ══════════════════════════════════════════════════════════════

SCROLL_PAUSE     = 2        # ← seconds between result-panel scrolls
PAGE_LOAD_WAIT   = 4        # ← seconds to wait after opening each listing
TARGET_RESULTS   = 120      # ← max listings per run  (set 50000 for bulk)

# ── Output file location ───────────────────────────────────────
# Saved to your Desktop by default so there is no permission conflict
# even if you accidentally leave the file open in Excel.
# Change to any folder you like, e.g. r"D:\MyData\results.xlsx"
OUTPUT_FILE      = os.path.join(os.path.expanduser("~"), "Desktop", "google_maps_results.xlsx")

APPEND_MODE      = False    # ← True = keep adding rows to existing file
HEADLESS         = False    # ← True = hide Chrome window
RETRY_ATTEMPTS   = 2        # ← retries before skipping a failed listing
NAME_WAIT_SECS   = 10       # ← max seconds to wait for the name to appear

# Optional: paste your Chrome User Data path here to reuse a logged-in
# profile (fewer CAPTCHAs).
# Windows example: r"C:\Users\YourName\AppData\Local\Google\Chrome\User Data"
CHROME_PROFILE_DIR = ""


# ══════════════════════════════════════════════════════════════
#  XPATH / CSS SELECTORS  — update if Google changes its HTML
# ══════════════════════════════════════════════════════════════
#
#  Open Chrome DevTools (F12) on maps.google.com, inspect the element
#  you need, and replace the XPath constant below.

# Scrollable results panel on the left
RESULTS_PANEL_XPATH  = '//div[@role="feed"]'

# Each result card link in the panel
RESULT_CARD_XPATH    = '//div[@role="feed"]//a[@href and contains(@href, "/maps/place/")]'

# ── Inside a listing page ──────────────────────────────────────

# Business name  (h1 at the top of the detail panel)
NAME_XPATH           = '//h1[contains(@class,"DUwDvf")]'

# Star rating  e.g. "4.5"
RATING_XPATH         = '//div[@class="F7nice "]//span[@aria-hidden="true"]'

# Review count  e.g. "1,234 reviews"
REVIEW_COUNT_XPATH   = '//div[@class="F7nice "]//span[contains(@aria-label,"reviews")]'

# Street address
ADDRESS_XPATH        = '//button[@data-item-id="address"]//div[contains(@class,"Io6YTe")]'

# Phone number
PHONE_XPATH          = '//button[contains(@data-item-id,"phone")]//div[contains(@class,"Io6YTe")]'

# Website URL text shown on the page
WEBSITE_XPATH        = '//a[@data-item-id="authority"]//div[contains(@class,"Io6YTe")]'

# Category / business type  e.g. "Italian restaurant"
CATEGORY_XPATH       = '//button[contains(@jsaction,"category")]'

# Business hours summary line  e.g. "Open ⋅ Closes 11 PM"
HOURS_XPATH          = '//div[@class="t39EBf GUrTXd"]//span'

# Open / Closed status text
OPEN_STATUS_XPATH    = '//span[contains(@class,"ZDu9vd")]//span'

# Plus Code  e.g. "QXQR+49 Lahore"
PLUS_CODE_XPATH      = '//button[@data-item-id="oloc"]//div[contains(@class,"Io6YTe")]'

# Short description from the "About" section (not always present)
DESCRIPTION_XPATH    = '//div[@class="PYvSYb"]'

# Price level  e.g. "$$"
PRICE_XPATH          = '//span[contains(@aria-label,"Price")]'

# Latitude / longitude are parsed from the URL — no XPath needed.


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

# Fields considered "required" — if ALL are empty the row is skipped
REQUIRED_FIELDS = {"Name"}   # ← add "Address", "Phone" etc. to be stricter


# ──────────────────────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────────────────────

def get_text(driver, xpath, default=""):
    """Return stripped inner text of the first matching element."""
    try:
        return driver.find_element(By.XPATH, xpath).text.strip()
    except NoSuchElementException:
        return default


def extract_coords(url):
    """
    Parse lat/lng from a Google Maps URL fragment like @31.5204,74.3587,17z.
    Returns (lat_str, lng_str) or ("", "").
    """
    m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    return (m.group(1), m.group(2)) if m else ("", "")


def is_complete(row_data):
    """
    Return True only when all REQUIRED_FIELDS have non-empty values.
    row_data is a list aligned with COLUMNS.
    """
    col_index = {name: idx for idx, name in enumerate(COLUMNS)}
    for field in REQUIRED_FIELDS:
        value = row_data[col_index[field]]
        if not value or str(value).strip() == "":
            return False
    return True


# ──────────────────────────────────────────────────────────────
#  CHROME DRIVER SETUP
# ──────────────────────────────────────────────────────────────

def build_driver():
    opts = Options()

    if HEADLESS:
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")

    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--lang=en-US,en;q=0.9")

    # ── Suppress GPU / CommandBuffer errors (Windows-specific noise) ──
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--disable-gpu-compositing")
    opts.add_argument("--log-level=3")                 # silence Chrome console noise
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])  # hide DevTools logs

    if CHROME_PROFILE_DIR:
        opts.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")

    if USE_WDM:
        service = Service(ChromeDriverManager().install())
    else:
        # ← CHANGE THIS to your local chromedriver path if webdriver-manager
        #   is not installed.
        service = Service("/usr/local/bin/chromedriver")

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
    """Create or load the workbook. Returns (wb, ws, next_row_number)."""
    import os

    if APPEND_MODE and os.path.exists(OUTPUT_FILE):
        wb = openpyxl.load_workbook(OUTPUT_FILE)
        ws = wb.active
        next_row = ws.max_row + 1
        print(f"[Excel] Appending — next data row: {next_row}")
        return wb, ws, next_row

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Maps Data"

    # ── Header styling ──────────────────────────────────────────
    hdr_fill = PatternFill("solid", start_color="1F4E79", end_color="1F4E79")
    hdr_font = Font(bold=True, color="FFFFFF", name="Arial", size=11)
    thin_side = Side(style="thin", color="AAAAAA")
    thin_border = Border(left=thin_side, right=thin_side,
                         top=thin_side, bottom=thin_side)

    for col_idx, col_name in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill      = hdr_fill
        cell.font      = hdr_font
        cell.border    = thin_border
        cell.alignment = Alignment(horizontal="center", vertical="center",
                                   wrap_text=True)

    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"   # header stays visible while scrolling

    # ── Column widths ──────────────────────────────────────────
    # Adjust these numbers (character widths) to taste
    widths = [5, 30, 22, 8, 10, 40, 18, 35, 30, 12, 10, 12, 12, 14, 40, 50, 25]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    return wb, ws, 2   # data starts at row 2


# ──────────────────────────────────────────────────────────────
#  WRITE ONE ROW TO EXCEL (only if data is complete)
# ──────────────────────────────────────────────────────────────

def write_row(ws, row_number, row_data):
    """
    Appends row_data to ws.
    row_number is the sequential display number (1, 2, 3 …) used for
    alternating row colours — it is NOT the Excel row index.
    Returns True so the caller can count written rows.
    """
    thin_side   = Side(style="thin", color="DDDDDD")
    thin_border = Border(left=thin_side, right=thin_side,
                         top=thin_side, bottom=thin_side)

    # Alternate white / light-blue rows
    fill_hex  = "EAF2FB" if row_number % 2 == 0 else "FFFFFF"
    row_fill  = PatternFill("solid", start_color=fill_hex, end_color=fill_hex)
    data_font = Font(name="Arial", size=10)
    data_align = Alignment(vertical="center", wrap_text=True)

    ws.append(row_data)
    excel_row = ws.max_row

    for cell in ws[excel_row]:
        cell.fill      = row_fill
        cell.font      = data_font
        cell.alignment = data_align
        cell.border    = thin_border

    ws.row_dimensions[excel_row].height = 18
    return True


# ──────────────────────────────────────────────────────────────
#  SAFE EXCEL SAVE  (handles PermissionError when file is open)
# ──────────────────────────────────────────────────────────────

def safe_save(wb, filepath):
    """
    Save the workbook to `filepath`.
    If the file is locked (open in Excel), automatically saves to a
    timestamped fallback name so no data is ever lost.
    Prints a clear message telling you what happened.
    """
    try:
        wb.save(filepath)
    except PermissionError:
        # File is open in Excel — save to a dated fallback instead
        base, ext = os.path.splitext(filepath)
        stamp     = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback  = f"{base}_BACKUP_{stamp}{ext}"
        wb.save(fallback)
        print(
            f"\n  ⚠  PermissionError: '{os.path.basename(filepath)}' is open in Excel.\n"
            f"     Data saved to fallback: {fallback}\n"
            f"     Close Excel and rename the backup if needed.\n"
        )


# ──────────────────────────────────────────────────────────────
#  WAIT FOR THE LISTING PAGE TO LOAD (name must appear)
# ──────────────────────────────────────────────────────────────

def wait_for_listing(driver):
    """
    Blocks until the business name h1 is present in the DOM.
    Returns True on success, False on timeout.
    """
    try:
        WebDriverWait(driver, NAME_WAIT_SECS).until(
            EC.presence_of_element_located((By.XPATH, NAME_XPATH))
        )
        return True
    except TimeoutException:
        return False


# ──────────────────────────────────────────────────────────────
#  SCRAPE ONE LISTING PAGE
# ──────────────────────────────────────────────────────────────

def scrape_listing(driver, query, display_no):
    """
    Waits for the page to load, then reads all fields.
    Returns a filled row list, or None if the page didn't load properly.
    """
    # Wait for the name element — if it never appears the page failed
    if not wait_for_listing(driver):
        return None

    # Give JS-rendered sections a moment to settle
    time.sleep(PAGE_LOAD_WAIT)

    url      = driver.current_url
    lat, lng = extract_coords(url)

    name        = get_text(driver, NAME_XPATH)
    rating      = get_text(driver, RATING_XPATH)
    reviews_raw = get_text(driver, REVIEW_COUNT_XPATH)
    reviews     = re.sub(r"[^\d,]", "", reviews_raw)   # keep digits and commas
    address     = get_text(driver, ADDRESS_XPATH)
    phone       = get_text(driver, PHONE_XPATH)
    website     = get_text(driver, WEBSITE_XPATH)
    category    = get_text(driver, CATEGORY_XPATH)
    hours       = get_text(driver, HOURS_XPATH)
    open_status = get_text(driver, OPEN_STATUS_XPATH)
    plus_code   = get_text(driver, PLUS_CODE_XPATH)
    description = get_text(driver, DESCRIPTION_XPATH)
    price       = get_text(driver, PRICE_XPATH)

    row = [
        display_no,   # "No." column — only assigned when row is kept
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

    # ── Guard: skip if required fields are missing ──────────────
    if not is_complete(row):
        return None

    return row


# ──────────────────────────────────────────────────────────────
#  SCROLL THE RESULTS PANEL TO COLLECT URLS
# ──────────────────────────────────────────────────────────────

def scroll_results_panel(driver, target):
    """
    Scrolls the left-side feed until `target` unique listing URLs are
    collected or no more results appear.
    Returns a deduplicated list of URLs.
    """
    try:
        panel = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, RESULTS_PANEL_XPATH))
        )
    except TimeoutException:
        print("[!] Results panel not found — check RESULTS_PANEL_XPATH")
        return []

    collected  = {}   # url → True  (ordered dict for deduplication)
    prev_count = 0
    stall_ticks = 0

    while len(collected) < target:
        cards = driver.find_elements(By.XPATH, RESULT_CARD_XPATH)
        for card in cards:
            href = card.get_attribute("href")
            if href and "/maps/place/" in href:
                # Strip tracking params after the coords for a clean key
                clean = href.split("?")[0]
                collected[clean] = href   # store original href as value

        count = len(collected)
        print(f"  [scroll] {count} listings found …", end="\r")

        if count >= target:
            break

        # Scroll panel down
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight", panel
        )
        time.sleep(SCROLL_PAUSE)

        # Check for Google's "end of results" notice
        end_els = driver.find_elements(
            By.XPATH,
            '//span[contains(text(),"end of results") or '
            'contains(text(),"reached the end") or '
            'contains(text(),"You\'ve reached the end")]'
        )
        if end_els:
            print("\n  [scroll] End of results reached.")
            break

        # Stall detection
        if count == prev_count:
            stall_ticks += 1
            if stall_ticks >= 5:
                print("\n  [scroll] No new results loading — stopping.")
                break
        else:
            stall_ticks = 0
        prev_count = count

    print()
    urls = list(collected.values())[:target]
    return urls


# ──────────────────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────────────────

def run_scraper():
    print("=" * 62)
    print("  GOOGLE MAPS SCRAPER  v2.0")
    print("=" * 62)
    query = input("\nEnter your search query :\n> ").strip()
    if not query:
        print("No query entered. Exiting.")
        sys.exit(1)

    print(f"\n  Target : {TARGET_RESULTS} results")
    print(f"  Output : {OUTPUT_FILE}")
    print(f"  Query  : {query}\n")

    driver      = build_driver()
    wb, ws, _   = setup_workbook()

    # display_no counts only rows that were actually written
    display_no  = ws.max_row - 1 if APPEND_MODE else 0
    written     = 0
    skipped     = 0

    try:
        # ── Open Google Maps ─────────────────────────────────────
        print("[1] Opening Google Maps …")
        driver.get("https://www.google.com/maps")
        time.sleep(3)

        # Accept cookie consent if it appears (common in EU / Pakistan)
        for btn_text in ["Accept all", "Reject all", "I agree"]:
            try:
                btn = WebDriverWait(driver, 4).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f'//button[.//span[text()="{btn_text}"]]')
                    )
                )
                btn.click()
                time.sleep(1)
                break
            except TimeoutException:
                pass

        # ── Search ───────────────────────────────────────────────
        print("[2] Typing search query …")
        search_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, '//input[@id="ucc-14"]')
                # ← CHANGE THIS XPATH if the search box id changes
            )
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)
        time.sleep(4)

        # ── Collect listing URLs ──────────────────────────────────
        print("[3] Scrolling results panel to collect URLs …")
        listing_urls = scroll_results_panel(driver, TARGET_RESULTS)

        if not listing_urls:
            print("[!] No listings found. The page XPaths may need updating.")
            return

        total = len(listing_urls)
        print(f"[*] {total} listing URLs collected. Scraping details …\n")

        # ── Visit each listing ────────────────────────────────────
        for idx, url in enumerate(listing_urls, start=1):
            short_url = url[:75] + "…" if len(url) > 75 else url
            print(f"  [{idx}/{total}] {short_url}")

            row_data = None

            for attempt in range(1, RETRY_ATTEMPTS + 1):
                try:
                    driver.get(url)
                except Exception as e:
                    print(f"    [!] Navigation error (attempt {attempt}): {e}")
                    time.sleep(2)
                    continue

                row_data = scrape_listing(driver, query, display_no + 1)

                if row_data is not None:
                    break   # success — stop retrying

                print(f"    [~] Incomplete data (attempt {attempt}) — retrying …")
                time.sleep(2)

            # ── Decide whether to write the row ──────────────────
            if row_data is None:
                skipped += 1
                print(f"    [✗] Skipped (missing required data)\n")
                continue

            display_no += 1
            write_row(ws, display_no, row_data)
            written += 1
            print(f"    [✓] Saved as row #{display_no}\n")

            # Auto-save every 10 successfully written rows
            if written % 10 == 0:
                safe_save(wb, OUTPUT_FILE)
                print(f"  ── Auto-saved ({written} rows written so far) ──\n")

        # ── Final save ────────────────────────────────────────────
        safe_save(wb, OUTPUT_FILE)
        print("=" * 62)
        print(f"  Done!")
        print(f"  Written  : {written} rows")
        print(f"  Skipped  : {skipped} listings (incomplete / failed to load)")
        print(f"  File     : {OUTPUT_FILE}")
        print("=" * 62)

    finally:
        driver.quit()


# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_scraper()
