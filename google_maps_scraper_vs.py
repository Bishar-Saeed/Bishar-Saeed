import time
import re
from datetime import datetime
from typing import List, Dict

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def create_driver() -> webdriver.Chrome:
    """Create and configure Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver


def search_on_maps(driver: webdriver.Chrome, query: str) -> bool:
    """Search for a query on Google Maps"""
    try:
        print(f"Loading Google Maps...")
        driver.get("https://www.google.com/maps")
        time.sleep(3)

        # Find and click the search box
        print(f"Finding search box...")
        search_box = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "searchboxinput"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)

        print(f"Searching for '{query}'...")
        time.sleep(5)

        # Wait for results to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@role='feed']//div[@role='article']"))
        )
        print("Results loaded successfully!")
        return True

    except Exception as e:
        print(f"Error during search: {e}")
        return False


def get_place_info_from_card(card) -> Dict[str, str]:
    """Extract information from a single place card"""
    try:
        info = {
            "Name": "",
            "Category": "",
            "Rating": "",
            "Reviews": "",
            "Address": "",
            "Phone": "",
            "Website": "",
            "Google Maps URL": "",
        }

        # Try to get the card text content
        card_text = card.text
        lines = [line.strip() for line in card_text.split("\n") if line.strip()]

        if not lines:
            return None

        # First line is usually the name
        info["Name"] = lines[0]

        # Parse the rest of the lines
        for i, line in enumerate(lines[1:], 1):
            # Rating pattern: "X.X★ (Y reviews)" or similar
            if "★" in line or "stars" in line.lower() or ("(" in line and ")" in line):
                info["Rating"] = line
            # Phone pattern
            elif re.match(r"[\d\s\-\+\(\)]{7,}", line):
                if not info["Phone"]:
                    info["Phone"] = line
            # Address pattern - contains numbers, commas
            elif ("st" in line.lower() or "ave" in line.lower() or "rd" in line.lower()
                  or "blvd" in line.lower() or "," in line):
                if not info["Address"]:
                    info["Address"] = line
            # Category or other info
            elif i == 1:
                info["Category"] = line

        # Try to get the Google Maps URL from the card link
        try:
            link_elem = card.find_element(By.XPATH, ".//a[@href]")
            info["Google Maps URL"] = link_elem.get_attribute("href")
        except NoSuchElementException:
            pass

        return info if info["Name"] else None

    except StaleElementReferenceException:
        return None
    except Exception as e:
        return None


def scrape_results(driver: webdriver.Chrome, max_results: int) -> List[Dict]:
    """Scroll through results and collect place information"""
    results = []
    seen_names = set()

    try:
        # Find the results container
        results_container = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='feed']"))
        )

        scroll_attempts = 0
        no_new_found_count = 0
        last_count = 0

        while len(results) < max_results and scroll_attempts < 100:
            # Get all currently visible place cards
            try:
                cards = driver.find_elements(By.XPATH, "//div[@role='feed']//div[@role='article']")
            except NoSuchElementException:
                cards = []

            if not cards:
                print("No cards found, waiting...")
                time.sleep(2)
                scroll_attempts += 1
                continue

            # Process each visible card
            for card in cards:
                if len(results) >= max_results:
                    break

                try:
                    place_info = get_place_info_from_card(card)
                    if place_info and place_info["Name"] not in seen_names:
                        seen_names.add(place_info["Name"])
                        results.append(place_info)
                        print(f"[{len(results)}] {place_info['Name']} - {place_info['Category']}")

                except StaleElementReferenceException:
                    continue

            # Check if we found new results
            if len(results) == last_count:
                no_new_found_count += 1
            else:
                no_new_found_count = 0
                last_count = len(results)

            # Stop if no new results found in multiple attempts
            if no_new_found_count >= 5:
                print("No new results found after multiple attempts. Stopping.")
                break

            # Scroll down in the results container
            print(f"Scrolling... (Current: {len(results)}/{max_results})")
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollTop + 500;",
                results_container
            )
            time.sleep(2)
            scroll_attempts += 1

    except Exception as e:
        print(f"Error during scraping: {e}")

    return results


def save_to_excel(results: List[Dict], query: str) -> str:
    """Save results to an Excel file"""
    if not results:
        print("No results to save")
        return None

    try:
        df = pd.DataFrame(results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = re.sub(r"[^a-zA-Z0-9_]", "_", query)[:40]
        filename = f"google_maps_{safe_query}_{timestamp}.xlsx"

        df.to_excel(filename, index=False, engine="openpyxl")
        print(f"\n✓ Saved {len(results)} results to: {filename}")
        return filename

    except Exception as e:
        print(f"Error saving file: {e}")
        return None


def main():
    """Main execution function"""
    print("=" * 60)
    print("Google Maps Scraper (Working Version)")
    print("=" * 60)

    query = input("\nEnter search query (e.g., 'restaurants in NYC'): ").strip()
    if not query:
        query = "restaurants"

    max_results_str = input("Maximum results to collect (default 1000): ").strip()
    try:
        max_results = int(max_results_str)
    except ValueError:
        max_results = 1000

    if max_results < 1:
        max_results = 1000

    print(f"\nConfiguration:")
    print(f"  Search Query: {query}")
    print(f"  Max Results: {max_results}")
    print(f"  Starting browser...\n")

    driver = None
    try:
        driver = create_driver()

        # Search on Google Maps
        if not search_on_maps(driver, query):
            print("Failed to search on Google Maps")
            return

        # Scrape results
        print("\nScraping results...")
        results = scrape_results(driver, max_results)

        # Save to Excel
        if results:
            print(f"\nCollected {len(results)} places total")
            save_to_excel(results, query)
        else:
            print("\nNo results were collected")

    except KeyboardInterrupt:
        print("\n\nScraping cancelled by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()
            print("Done!")


if __name__ == "__main__":
    main()
