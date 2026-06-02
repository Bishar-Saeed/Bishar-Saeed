"""
State-Specific Medical/Dental Designation Scraper
--------------------------------------------------
Sources:
  1. NPPES Bulk File  — taxonomy/designation codes (federal, free)
  2. Florida DBPR API — real state board license data (free JSON API)
  3. Texas TMB        — public license search (HTML scrape)

Install: pip install requests beautifulsoup4 pandas lxml
"""

import requests
import pandas as pd
import csv
import time
import zipfile
import os
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# SOURCE 1: NPPES Bulk File (Federal, Free)
# Downloads the full NPI + taxonomy/designation file
# ─────────────────────────────────────────────

NPPES_DOWNLOAD_PAGE = "https://download.cms.gov/nppes/NPI_Files.html"

# Taxonomy code → human-readable designation
TAXONOMY_MAP = {
    "207Q00000X": "MD - Family Medicine",
    "207R00000X": "MD - Internal Medicine",
    "208D00000X": "MD - General Practice",
    "207P00000X": "MD - Emergency Medicine",
    "208000000X": "MD - Pediatrics",
    "207X00000X": "MD - Orthopedic Surgery",
    "207N00000X": "MD - Dermatology",
    "207V00000X": "MD - Obstetrics & Gynecology",
    "2084P0800X": "MD - Psychiatry",
    "122300000X": "DDS/DMD - General Dentistry",
    "1223E0200X": "DDS/DMD - Orthodontics",
    "1223P0221X": "DDS/DMD - Pediatric Dentistry",
    "1223S0112X": "DDS/DMD - Oral Surgery",
    "1223P0300X": "DDS/DMD - Periodontics",
    "1223D0001X": "DDS/DMD - Dental Public Health",
    "363L00000X": "NP - Nurse Practitioner",
    "363A00000X": "PA - Physician Assistant",
}

def get_designation(taxonomy_code):
    return TAXONOMY_MAP.get(taxonomy_code, f"Other ({taxonomy_code})")


def query_npi_by_state(state_code, taxonomy_desc="Dentist", limit=200):
    """
    Query the NPI Registry API for providers in a specific state.
    Returns list of dicts with name, designation, license state, address.
    """
    url = "https://npiregistry.cms.hhs.gov/api/"
    results = []
    skip = 0

    while skip < limit:
        params = {
            "version":              "2.1",
            "taxonomy_description": taxonomy_desc,
            "state":                state_code,
            "enumeration_type":     "NPI-1",
            "limit":                min(200, limit - skip),
            "skip":                 skip,
        }

        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  API error: {e}")
            break

        batch = data.get("results", [])
        if not batch:
            break

        for p in batch:
            basic     = p.get("basic", {})
            addresses = p.get("addresses", [])
            taxonomies= p.get("taxonomies", [])
            identifiers = p.get("identifiers", [])

            addr = next((a for a in addresses if a.get("address_purpose") == "LOCATION"), addresses[0] if addresses else {})
            tax  = next((t for t in taxonomies if t.get("primary")), taxonomies[0] if taxonomies else {})

            # State license number from identifiers block
            state_license = next(
                (i.get("identifier", "") for i in identifiers
                 if i.get("state") == state_code and i.get("code") == "02"),
                ""
            )

            results.append({
                "npi":             p.get("number", ""),
                "first_name":      basic.get("first_name", ""),
                "last_name":       basic.get("last_name", ""),
                "credential":      basic.get("credential", ""),  # MD, DO, DDS, DMD etc.
                "designation":     get_designation(tax.get("code", "")),
                "taxonomy_code":   tax.get("code", ""),
                "license_state":   state_code,
                "state_license_no":state_license,
                "city":            addr.get("city", ""),
                "zip":             addr.get("postal_code", ""),
                "phone":           addr.get("telephone_number", ""),
                "address":         addr.get("address_1", ""),
                "enumeration_date":basic.get("enumeration_date", ""),
                "last_updated":    basic.get("last_updated", ""),
                "status":          basic.get("status", ""),
            })

        skip += len(batch)
        time.sleep(0.4)

    return results


# ─────────────────────────────────────────────
# SOURCE 2: Florida DBPR (Free JSON API)
# Florida Department of Business & Professional Regulation
# One of the best state APIs — returns license status, expiry, discipline
# ─────────────────────────────────────────────

def scrape_florida_dbpr(license_type="ME", max_records=100):
    """
    Florida DBPR open data API.
    license_type:
      'ME'  = Medical Doctor
      'DN'  = Dentist
      'OS'  = Osteopathic Physician
      'NUR' = Nurse
    """
    url = "https://www.myfloridalicense.com/wl11.asp"

    params = {
        "mode":         "0",
        "SID":          "",
        "brd":          "0",
        "typ":          license_type,
        "num":          "",
        "namefirst":    "",
        "namelast":     "",
        "namemid":      "",
        "county":       "0",
        "LicLoc":       "fl",
        "lnum":         "",
        "lang":         "EN",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)",
    }

    print(f"Scraping Florida DBPR for license type: {license_type}")

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"  Error: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    rows = soup.select("table tr")[1:]  # skip header

    results = []
    for row in rows[:max_records]:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cols) >= 5:
            results.append({
                "license_number": cols[0] if len(cols) > 0 else "",
                "name":           cols[1] if len(cols) > 1 else "",
                "license_type":   license_type,
                "status":         cols[2] if len(cols) > 2 else "",
                "expiry_date":    cols[3] if len(cols) > 3 else "",
                "county":         cols[4] if len(cols) > 4 else "",
                "state":          "FL",
            })

    print(f"  Found {len(results)} Florida records")
    return results


# ─────────────────────────────────────────────
# SOURCE 3: Texas Medical Board (HTML scrape)
# ─────────────────────────────────────────────

def scrape_texas_tmb(last_name_starts_with="A", license_type="MD"):
    """
    Scrape Texas Medical Board public license search.
    https://www.tmb.state.tx.us/page/public-info
    """
    url = "https://www.tmb.state.tx.us/idl/D2399F6C-8EA1-4A07-B8D0-0E4D5F9E5C62"

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    payload = {
        "LastName":    last_name_starts_with,
        "FirstName":   "",
        "LicenseType": license_type,
        "LicenseNo":   "",
        "City":        "",
        "ZipCode":     "",
    }

    print(f"Scraping Texas TMB: last name starts '{last_name_starts_with}', type={license_type}")

    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"  Error: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    table = soup.find("table", {"id": "tblResults"}) or soup.find("table")

    results = []
    if not table:
        print("  No table found — TMB may have updated their HTML.")
        return results

    headers_row = [th.get_text(strip=True) for th in table.find_all("th")]
    for row in table.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if cols:
            record = dict(zip(headers_row, cols))
            record["state"] = "TX"
            results.append(record)

    print(f"  Found {len(results)} Texas records")
    return results


# ─────────────────────────────────────────────
# MAIN: Run all sources and save to CSV
# ─────────────────────────────────────────────

def save_csv(data, filename):
    if not data:
        print(f"  No data for {filename}")
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ Saved {len(data)} records → {filename}")


if __name__ == "__main__":

    # 1. NPI API — Dentists and Doctors by State
    print("\n=== 1. NPI Registry by State ===")
    states_to_scrape = ["NY", "CA", "TX", "FL", "IL"]

    all_npi = []
    for state in states_to_scrape:
        for category in ["Dentist", "Physician"]:
            print(f"\nFetching {category}s in {state}...")
            records = query_npi_by_state(state, taxonomy_desc=category, limit=200)
            all_npi.extend(records)

    save_csv(all_npi, "npi_state_designations.csv")

    # 2. Florida DBPR
    print("\n=== 2. Florida DBPR Licenses ===")
    fl_doctors  = scrape_florida_dbpr(license_type="ME", max_records=200)
    fl_dentists = scrape_florida_dbpr(license_type="DN", max_records=200)
    save_csv(fl_doctors + fl_dentists, "florida_licenses.csv")

    # 3. Texas Medical Board
    print("\n=== 3. Texas Medical Board ===")
    tx_md = scrape_texas_tmb(last_name_starts_with="Smith", license_type="MD")
    save_csv(tx_md, "texas_licenses.csv")

    # Summary
    print("\n=== Summary ===")
    print(f"Total NPI records:     {len(all_npi)}")
    print(f"Total Florida records: {len(fl_doctors + fl_dentists)}")
    print(f"Total Texas records:   {len(tx_md)}")
