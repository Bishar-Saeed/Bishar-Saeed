# #!/usr/bin/env python3
# """
# LinkedIn Doctor Email Finder - Browser Session + HTTPX
# 1. Google search for LinkedIn profiles with @gmail.com
# 2. Extract profile URLs
# 3. Authenticate once with browser
# 4. Use HTTPX session for fast profile scraping
# 5. Save only profiles with emails to CSV
# """

# import asyncio
# import json
# import re
# import csv
# import time
# from urllib.parse import quote_plus
# import httpx
# from playwright.async_api import async_playwright
# from bs4 import BeautifulSoup

# # ============================================================================
# # CONFIGURATION
# # ============================================================================

# EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
# MAX_GOOGLE_PAGES = 5  # Number of Google search pages
# MAX_PROFILES_TO_SCRAPE = 50

# # ============================================================================
# # STEP 1: GOOGLE SEARCH FOR LINKEDIN PROFILES (USING HTTPX)
# # ============================================================================

# async def search_google_for_linkedin(profession, state, max_pages=5):
#     """
#     Search Google for LinkedIn profiles with @gmail.com
#     Uses HTTPX with proper headers (no browser needed for search)
#     """
#     query = f'site:linkedin.com/in "{profession}" "{state}" "@gmail.com"'
#     encoded_query = quote_plus(query)
    
#     profiles_urls = []
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
#         "Accept": "text/html,application/xhtml+xml",
#         "Accept-Language": "en-US,en;q=0.9"
#     }
    
#     print(f"\n🔍 Google Search: {query}")
#     print(f"{'=' * 60}\n")
    
#     async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
#         for page in range(max_pages):
#             start = page * 10
#             search_url = f"https://www.google.com/search?q={encoded_query}&start={start}"
            
#             print(f"  Page {page + 1}: {search_url[:80]}...")
            
#             try:
#                 response = await client.get(search_url)
                
#                 if response.status_code != 200:
#                     print(f"    ⚠️ Google blocked? Status: {response.status_code}")
#                     break
                
#                 # Extract LinkedIn URLs
#                 linkedin_links = re.findall(r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+/?', response.text)
                
#                 # Clean URLs
#                 for link in linkedin_links:
#                     clean_url = link.split('?')[0].rstrip('/')
#                     if clean_url not in profiles_urls:
#                         profiles_urls.append(clean_url)
                
#                 print(f"    ✅ Found {len(linkedin_links)} URLs (total: {len(profiles_urls)})")
                
#                 # Check if there's a next page
#                 if 'aria-label="Next"' not in response.text and 'pnnext' not in response.text:
#                     print("    📄 No more pages")
#                     break
                
#                 await asyncio.sleep(2)  # Polite delay
                
#             except Exception as e:
#                 print(f"    ❌ Error: {e}")
#                 break
    
#     print(f"\n✅ Total LinkedIn profiles found: {len(profiles_urls)}")
#     return profiles_urls

# # ============================================================================
# # STEP 2: GET AUTHENTICATED LINKEDIN SESSION (ONCE)
# # ============================================================================

# async def get_linkedin_session():
#     """
#     Launches a browser, logs in manually once, returns session cookies + CSRF token
#     """
#     print("\n" + "=" * 60)
#     print("  STEP 2: AUTHENTICATE WITH LINKEDIN")
#     print("=" * 60)
    
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False)
#         context = await browser.new_context()
#         page = await context.new_page()
#         await page.goto("https://www.linkedin.com/login")
        
#         input("\n📌 Log into LinkedIn in the opened browser, then press ENTER here...")
        
#         # Wait for feed to load
#         await page.wait_for_timeout(3000)
        
#         # Extract cookies
#         cookies = await context.cookies()
#         cookie_dict = {c['name']: c['value'] for c in cookies}
        
#         # Extract CSRF token
#         csrf_token = await page.evaluate("""() => {
#             const metas = document.querySelectorAll('meta[name="csrf-token"]');
#             return metas.length ? metas[0].getAttribute('content') : null;
#         }""")
        
#         print(f"✅ Cookies extracted: {len(cookie_dict)} items")
#         print(f"✅ CSRF Token: {csrf_token[:50] if csrf_token else 'Not found'}...")
        
#         await browser.close()
#         return cookie_dict, csrf_token

# # ============================================================================
# # STEP 3: BUILD HTTPX CLIENT WITH SESSION
# # ============================================================================

# def build_httpx_client(cookies, csrf_token):
#     """Creates an authenticated HTTPX client"""
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
#         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
#         "Accept-Language": "en-US,en;q=0.9",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Referer": "https://www.linkedin.com/",
#         "Origin": "https://www.linkedin.com",
#         "Connection": "keep-alive",
#         "Upgrade-Insecure-Requests": "1",
#         "Sec-Fetch-Dest": "document",
#         "Sec-Fetch-Mode": "navigate",
#         "Sec-Fetch-Site": "same-origin",
#     }
    
#     if csrf_token:
#         headers["csrf-token"] = csrf_token
#         headers["x-restli-protocol-version"] = "2.0.0"
    
#     client = httpx.Client(http2=True, headers=headers, cookies=cookies)
#     return client

# # ============================================================================
# # STEP 4: SCRAPE PROFILE DATA USING HTTPX
# # ============================================================================

# def extract_profile_data(html, profile_url):
#     """Extract name, headline, about, and emails from profile HTML"""
#     soup = BeautifulSoup(html, 'html.parser')
    
#     # Extract name from title
#     title_tag = soup.find('title')
#     name = ""
#     if title_tag:
#         title_text = title_tag.text.strip()
#         name = title_text.split(' | ')[0] if ' | ' in title_text else title_text
    
#     # Extract headline
#     headline = ""
#     headline_selectors = [
#         '.text-body-medium',
#         '.pv-text-details__left-panel',
#         '[data-generated-suggestion-target]',
#         '.pv-entity__headline'
#     ]
#     for selector in headline_selectors:
#         elem = soup.select_one(selector)
#         if elem:
#             headline = elem.text.strip()
#             break
    
#     # Extract about section
#     about = ""
#     about_selectors = [
#         'section#about',
#         '.pv-about-section',
#         '.pv-shared-text-with-see-more'
#     ]
#     for selector in about_selectors:
#         elem = soup.select_one(selector)
#         if elem:
#             about = elem.text.strip()
#             break
    
#     # Extract ALL emails from the page
#     all_emails = set(EMAIL_REGEX.findall(html))
    
#     # Filter out junk emails
#     valid_emails = []
#     for email in all_emails:
#         email_lower = email.lower()
#         if not any(x in email_lower for x in ['example', 'test', 'linkedin.com', 'noreply']):
#             valid_emails.append(email)
    
#     # Separate Gmail from other emails
#     gmails = [e for e in valid_emails if 'gmail.com' in e.lower()]
#     other_emails = [e for e in valid_emails if 'gmail.com' not in e.lower()]
    
#     return {
#         "name": name[:100] if name else "",
#         "headline": headline[:200] if headline else "",
#         "about": about[:500] if about else "",
#         "gmails": "; ".join(gmails),
#         "other_emails": "; ".join(other_emails),
#         "all_emails": "; ".join(valid_emails),
#         "profile_url": profile_url
#     }

# async def scrape_profile_httpx(client, profile_url):
#     """Scrape a single profile using authenticated HTTPX session"""
#     try:
#         response = client.get(profile_url, timeout=20.0)
        
#         if response.status_code == 200:
#             data = extract_profile_data(response.text, profile_url)
#             return data
#         else:
#             print(f"    ⚠️ HTTP {response.status_code}")
#             return None
            
#     except Exception as e:
#         print(f"    ❌ Error: {e}")
#         return None

# # ============================================================================
# # STEP 5: MAIN PIPELINE
# # ============================================================================

# async def main():
#     print("\n" + "=" * 60)
#     print("  LINKEDIN DOCTOR EMAIL FINDER")
#     print("  Browser Auth + HTTPX Scraping")
#     print("=" * 60)
    
#     # Get user inputs
#     profession = input("\n📌 Profession (Doctor, Dentist, Cardiologist): ").strip()
#     state = input("📍 State (California, TX, New York): ").strip()
#     max_profiles = int(input("🎯 Max profiles to scrape (default 30): ") or "30")
#     max_google_pages = int(input("📄 Google pages to search (default 3): ") or "3")
    
#     # Step 1: Google search for LinkedIn URLs
#     print("\n" + "=" * 60)
#     print("  STEP 1: GOOGLE SEARCH FOR LINKEDIN PROFILES")
#     print("=" * 60)
    
#     profile_urls = await search_google_for_linkedin(profession, state, max_google_pages)
    
#     if not profile_urls:
#         print("\n❌ No LinkedIn profiles found. Try different search terms.")
#         return
    
#     # Limit URLs
#     profile_urls = profile_urls[:max_profiles]
#     print(f"\n📊 Will scrape {len(profile_urls)} profiles")
    
#     # Step 2: Get authenticated LinkedIn session
#     cookies, csrf_token = await get_linkedin_session()
    
#     if not cookies:
#         print("\n❌ Failed to get authentication. Cannot proceed.")
#         return
    
#     # Step 3: Build HTTPX client
#     print("\n" + "=" * 60)
#     print("  STEP 3: SCRAPING PROFILES WITH HTTPX")
#     print("=" * 60)
    
#     client = build_httpx_client(cookies, csrf_token)
    
#     results = []
#     for i, url in enumerate(profile_urls, 1):
#         print(f"\n[{i}/{len(profile_urls)}] {url}")
        
#         profile_data = await scrape_profile_httpx(client, url)
        
#         if profile_data and profile_data.get('all_emails'):
#             print(f"    ✅ Name: {profile_data['name'][:50]}")
#             print(f"    📧 Emails: {profile_data['all_emails'][:80]}")
#             results.append(profile_data)
#         elif profile_data:
#             print(f"    ⚠️ No emails found - skipping")
#         else:
#             print(f"    ❌ Failed to scrape")
        
#         # Polite delay between requests
#         await asyncio.sleep(random.uniform(2, 4))
    
#     client.close()
    
#     # Step 4: Save results to CSV
#     if results:
#         timestamp = time.strftime("%Y%m%d_%H%M%S")
#         filename = f"linkedin_doctors_{profession}_{state}_{timestamp}.csv"
        
#         with open(filename, 'w', newline='', encoding='utf-8') as f:
#             fieldnames = ['name', 'gmails', 'other_emails', 'all_emails', 'headline', 'about', 'profile_url']
#             writer = csv.DictWriter(f, fieldnames=fieldnames)
#             writer.writeheader()
#             writer.writerows(results)
        
#         print("\n" + "=" * 60)
#         print(f"  ✅ RESULTS SAVED")
#         print(f"  📁 File: {filename}")
#         print(f"  📊 Profiles with emails: {len(results)} / {len(profile_urls)}")
#         print("=" * 60)
        
#         # Preview
#         print("\n📋 SAMPLE RESULTS:")
#         for i, r in enumerate(results[:5], 1):
#             print(f"\n[{i}] {r['name'][:50]}")
#             print(f"    📧 {r['all_emails'][:80]}")
#             print(f"    🔗 {r['profile_url']}")
#     else:
#         print("\n❌ No profiles with emails found.")
#         print("   Note: LinkedIn rarely displays emails on public profiles.")

# # ============================================================================
# # RUN
# # ============================================================================

# if __name__ == "__main__":
#     import random
#     asyncio.run(main())





#!/usr/bin/env python3
"""
LinkedIn Doctor Email Finder - SerpAPI + Browser Session + HTTPX
1. SerpAPI search for LinkedIn profiles with @gmail.com (bypasses Google blocks)
2. Extract profile URLs
3. Authenticate once with browser
4. Use HTTPX session for fast profile scraping
5. Save only profiles with emails to CSV

REQUIRES: pip install google-search-results
Get SerpAPI key: https://serpapi.com (free tier: 100 searches/month)
"""

import asyncio
import json
import re
import csv
import time
import os
import random
from urllib.parse import quote_plus
import httpx
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Try to import SerpAPI
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    print("⚠️ SerpAPI not installed. Install with: pip install google-search-results")

# ============================================================================
# CONFIGURATION
# ============================================================================

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
MAX_PROFILES_TO_SCRAPE = 50

# Get SerpAPI key from environment variable or input
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

# ============================================================================
# STEP 1: SERPAPI SEARCH FOR LINKEDIN PROFILES (RELIABLE, NO BLOCKS)
# ============================================================================

async def search_google_serpapi(profession, state, max_results=50):
    """
    Search Google using SerpAPI - reliably gets results without blocking
    Requires API key from https://serpapi.com
    """
    if not SERPAPI_AVAILABLE:
        print("\n❌ SerpAPI not installed. Run: pip install google-search-results")
        return []
    
    if not SERPAPI_KEY:
        print("\n❌ SerpAPI key not configured!")
        print("   Get a free key at: https://serpapi.com")
        print("   Free tier: 100 searches/month")
        print("\n   Set it as environment variable: export SERPAPI_KEY='your_key'")
        print("   Or enter it now:")
        key_input = input("   Enter SerpAPI key: ").strip()
        if not key_input:
            return []
        globals()['SERPAPI_KEY'] = key_input
    
    query = f'site:linkedin.com/in "{profession}" "{state}" "@gmail.com"'
    
    print(f"\n🔍 SerpAPI Search: {query}")
    print(f"{'=' * 60}\n")
    
    profiles_urls = []
    start = 0
    
    while len(profiles_urls) < max_results:
        print(f"  Fetching results {start}...", end=" ", flush=True)
        
        try:
            # Use SerpAPI in a non-blocking way
            search = GoogleSearch({
                "q": query,
                "api_key": SERPAPI_KEY,
                "start": start,
                "num": 10
            })
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, search.get_dict)
            
            organic_results = results.get("organic_results", [])
            
            if not organic_results:
                print("No more results")
                break
            
            new_urls = 0
            for result in organic_results:
                link = result.get("link", "")
                if "linkedin.com/in/" in link:
                    clean_url = link.split("?")[0].rstrip("/")
                    if clean_url not in profiles_urls:
                        profiles_urls.append(clean_url)
                        new_urls += 1
            
            print(f"✅ +{new_urls} (total: {len(profiles_urls)})")
            
            # Check if we've reached the end
            if not results.get("serpapi_pagination", {}).get("next"):
                print("  📄 No more pages")
                break
            
            start += 10
            await asyncio.sleep(1)  # Polite delay
            
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    
    print(f"\n✅ Total LinkedIn profiles found: {len(profiles_urls)}")
    return profiles_urls[:max_results]

# ============================================================================
# FALLBACK: MANUAL URL INPUT (IF SERPAPI FAILS)
# ============================================================================

async def get_urls_manually():
    """Fallback method: let user paste URLs manually"""
    print("\n" + "=" * 60)
    print("  MANUAL URL INPUT MODE")
    print("=" * 60)
    print("\n📋 Paste LinkedIn profile URLs (one per line, empty line to finish):")
    
    urls = []
    while True:
        url = input().strip()
        if not url:
            break
        if "linkedin.com/in/" in url:
            clean_url = url.split("?")[0].rstrip("/")
            urls.append(clean_url)
    
    print(f"\n✅ Collected {len(urls)} LinkedIn URLs")
    return urls

# ============================================================================
# STEP 2: GET AUTHENTICATED LINKEDIN SESSION (ONCE)
# ============================================================================

async def get_linkedin_session():
    """
    Launches a browser, logs in manually once, returns browser, context, page, session cookies, and CSRF token.
    """
    print("\n" + "=" * 60)
    print("  STEP 2: AUTHENTICATE WITH LINKEDIN")
    print("=" * 60)
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://www.linkedin.com/login")
    
    input("\n📌 Log into LinkedIn in the opened browser, then press ENTER here...")
    
    # Wait for login to complete and open the feed
    await page.wait_for_timeout(3000)
    await page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(3000)
    
    # Extract cookies
    cookies = await context.cookies()
    cookie_dict = {c['name']: c['value'] for c in cookies}
    
    # Extract CSRF token
    csrf_token = await page.evaluate("""() => {
        const metas = document.querySelectorAll('meta[name="csrf-token"]');
        return metas.length ? metas[0].getAttribute('content') : null;
    }""")
    
    print(f"✅ Cookies extracted: {len(cookie_dict)} items")
    print(f"✅ CSRF Token: {csrf_token[:50] if csrf_token else 'Not found'}")

    return p, browser, context, page, cookie_dict, csrf_token

# ============================================================================
# STEP 3: BUILD HTTPX CLIENT WITH SESSION
# ============================================================================

def build_httpx_client(cookies, csrf_token):
    """Creates an authenticated HTTPX client"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.linkedin.com/",
        "Origin": "https://www.linkedin.com",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
    }
    
    if csrf_token:
        headers["csrf-token"] = csrf_token
        headers["x-restli-protocol-version"] = "2.0.0"
    
    client = httpx.Client(http2=True, headers=headers, cookies=cookies)
    return client

# ============================================================================
# STEP 4: SCRAPE PROFILE DATA USING HTTPX
# ============================================================================

def extract_profile_data(html, profile_url):
    """Extract name, headline, about, website, and emails from profile HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract name from explicit profile heading
    name = ""
    name_selectors = [
        'h1.text-heading-xlarge',
        'h1.text-heading-large',
        'h1',
        '.pv-top-card--list li.inline.t-24'
    ]
    for selector in name_selectors:
        elem = soup.select_one(selector)
        if elem and elem.text.strip():
            name = elem.text.strip()
            break

    if not name:
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.strip()
            name = title_text.split(' | ')[0] if ' | ' in title_text else title_text

    # Extract headline
    headline = ""
    headline_selectors = [
        '.text-body-medium.break-words',
        '.pv-text-details__left-panel .text-body-medium',
        '.pv-text-details__left-panel .text-body-small',
        '[data-generated-suggestion-target]',
        '.pv-top-card--list .text-body-medium'
    ]
    for selector in headline_selectors:
        elem = soup.select_one(selector)
        if elem and elem.text.strip():
            headline = elem.text.strip()
            break

    # Extract about section
    about = ""
    about_selectors = [
        'section#about',
        'section.pv-about-section',
        '.pv-about-section',
        '.pv-shared-text-with-see-more',
        '.ember-view .pv-about-section',
        'div[data-test-about], div[data-section]'
    ]
    for selector in about_selectors:
        elems = soup.select(selector)
        if elems:
            text_parts = []
            for elem in elems:
                text = elem.get_text(separator=' ', strip=True)
                if text:
                    text_parts.append(text)
            about = ' '.join(text_parts).strip()
            if about:
                break

    # Extract website / external links
    website = ""
    link_selectors = [
        'a[href^="http"]',
        'section.pv-contact-info__contact-type a[href^="http"]',
        '.pv-contact-info__contact-type a[href^="http"]',
    ]
    seen_websites = set()
    for selector in link_selectors:
        for elem in soup.select(selector):
            href = elem.get('href', '').strip()
            if href and 'linkedin.com' not in href and 'mailto:' not in href and href not in seen_websites:
                seen_websites.add(href)
                if not website:
                    website = href
    
    # Extract contact info block if available
    contact_info = ""
    contact_selectors = [
        '.pv-contact-info__contact-type',
        '.ci-phone',
        '.ci-email',
        '.pv-contact-info .pv-contact-info__ci-container',
        '.pv-contact-info__contact-type'
    ]
    text_parts = []
    for selector in contact_selectors:
        for elem in soup.select(selector):
            txt = elem.get_text(separator=' ', strip=True)
            if txt:
                text_parts.append(txt)
    contact_info = ' '.join(text_parts).strip()

    # Extract ALL emails from the page
    all_emails = set(EMAIL_REGEX.findall(html))
    
    # Filter out junk emails
    valid_emails = []
    for email in all_emails:
        email_lower = email.lower()
        if not any(x in email_lower for x in ['example', 'test', 'linkedin.com', 'noreply', 'no-reply', 'placeholder']):
            valid_emails.append(email)
    
    # Separate Gmail from other emails
    gmails = [e for e in valid_emails if 'gmail.com' in e.lower()]
    other_emails = [e for e in valid_emails if 'gmail.com' not in e.lower()]
    
    return {
        "name": name[:120] if name else "",
        "headline": headline[:250] if headline else "",
        "about": about[:1000] if about else "",
        "website": website,
        "contact_info": contact_info,
        "gmails": "; ".join(sorted(set(gmails))),
        "other_emails": "; ".join(sorted(set(other_emails))),
        "all_emails": "; ".join(sorted(set(valid_emails))),
        "profile_url": profile_url,
        "linkedin_url": profile_url
    }

async def scrape_profile_playwright(page, profile_url):
    """Scrape a single profile using an authenticated Playwright page."""
    try:
        await page.goto(profile_url, wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(random.uniform(2500, 4500))

        # Expand About / See more if present
        about_selectors = [
            'button:has-text("See more")',
            'button:has-text("see more")',
            'button:has-text("See more on LinkedIn")',
            'button[aria-label*="See more"]'
        ]
        for selector in about_selectors:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    await btn.click()
                    await page.wait_for_timeout(random.uniform(1200, 2200))
                    break
            except Exception:
                pass

        # Open contact info modal if available
        contact_text = ""
        websites = []
        try:
            contact_button = await page.query_selector('button:has-text("Contact info"), a:has-text("Contact info")')
            if contact_button:
                await contact_button.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                await contact_button.click()
                await page.wait_for_timeout(random.uniform(1500, 2800))
                contact_text = await page.evaluate("""() => {
                    const modal = document.querySelector('.artdeco-modal__content, [role="dialog"]');
                    return modal ? modal.innerText : '';
                }""")
                websites = await page.evaluate("""() => Array.from(
                    document.querySelectorAll('.artdeco-modal a[href], [role="dialog"] a[href]')
                )
                .map(a => a.href)
                .filter(h => h.startsWith('http') && !h.includes('linkedin.com') && !h.includes('mailto:') && !h.includes('javascript'))
                """)
                close_button = await page.query_selector('button[aria-label="Dismiss"], button[aria-label="Close"], button:has-text("Close")')
                if close_button:
                    await close_button.click()
                    await page.wait_for_timeout(500)
        except Exception:
            pass

        # Extract page text and HTML
        page_text = await page.evaluate("() => document.body.innerText")
        html = await page.content()

        # Extract base profile data from HTML and page text
        data = extract_profile_data(html, profile_url)
        if not data.get('website') and websites:
            data['website'] = websites[0]
        if contact_text:
            data['contact_info'] = contact_text[:1000]

        # If email not found in HTML, search contact text too
        if not data['all_emails'] and contact_text:
            extras = set(EMAIL_REGEX.findall(contact_text))
            extras = {e for e in extras if not any(x in e.lower() for x in ['example', 'test', 'linkedin.com', 'noreply', 'no-reply', 'placeholder'])}
            if extras:
                gmails = [e for e in extras if 'gmail.com' in e.lower()]
                other = [e for e in extras if 'gmail.com' not in e.lower()]
                data['gmails'] = '; '.join(sorted(set(gmails)))
                data['other_emails'] = '; '.join(sorted(set(other)))
                data['all_emails'] = '; '.join(sorted(set(extras)))

        # Ensure the profile URL is always present
        data['linkedin_url'] = profile_url
        data['profile_url'] = profile_url
        return data
    except Exception as e:
        print(f"    ❌ Playwright scrape error: {e}")
        return None

async def scrape_profile_httpx(client, profile_url):
    """Scrape a single profile using authenticated HTTPX session"""
    try:
        response = client.get(profile_url, timeout=20.0)
        
        if response.status_code == 200:
            data = extract_profile_data(response.text, profile_url)
            return data
        else:
            print(f"    ⚠️ HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return None

# ============================================================================
# STEP 5: MAIN PIPELINE
# ============================================================================

async def main():
    print("\n" + "=" * 60)
    print("  LINKEDIN DOCTOR EMAIL FINDER - SerpAPI Edition")
    print("  Uses SerpAPI to bypass Google blocking")
    print("=" * 60)
    
    # Get user inputs
    profession = input("\n📌 Profession (Doctor, Dentist, Cardiologist): ").strip()
    state = input("📍 State (California, TX, New York): ").strip()
    max_profiles = int(input("🎯 Max profiles to scrape (default 30): ") or "30")
    
    # Step 1: Search for LinkedIn URLs using SerpAPI
    print("\n" + "=" * 60)
    print("  STEP 1: SEARCHING LINKEDIN PROFILES (SerpAPI)")
    print("=" * 60)
    
    profile_urls = await search_google_serpapi(profession, state, max_profiles)
    
    # Fallback to manual input if SerpAPI fails
    if not profile_urls:
        print("\n⚠️ SerpAPI search returned no results.")
        use_manual = input("\nWould you like to enter URLs manually? (y/n): ").strip().lower()
        if use_manual == 'y':
            profile_urls = await get_urls_manually()
        else:
            print("\n❌ No URLs to process. Exiting.")
            return
    
    if not profile_urls:
        print("\n❌ No LinkedIn profiles found. Exiting.")
        return
    
    print(f"\n📊 Will scrape {len(profile_urls)} profiles")
    
    # Step 2: Get authenticated LinkedIn session
    session = await get_linkedin_session()
    if not session:
        print("\n❌ Failed to get authentication. Cannot proceed.")
        return
    p, browser, context, page, cookies, csrf_token = session
    
    # Step 3: Scrape profiles using Playwright page navigation
    print("\n" + "=" * 60)
    print("  STEP 3: SCRAPING PROFILES WITH PLAYWRIGHT")
    print("=" * 60)
    
    results = []
    for i, url in enumerate(profile_urls, 1):
        print(f"\n[{i}/{len(profile_urls)}] {url}")
        
        profile_data = await scrape_profile_playwright(page, url)
        
        if profile_data:
            print(f"    ✅ Name: {profile_data['name'][:50] or 'Unknown'}")
            print(f"    🔗 URL: {profile_data['linkedin_url']}")
            print(f"    🌐 Website: {profile_data['website'] or 'None'}")
            print(f"    📨 Emails: {profile_data['all_emails'] or 'None'}")
            results.append(profile_data)
        else:
            print(f"    ❌ Failed to scrape")
        
        await asyncio.sleep(random.uniform(2.5, 5.0))
    
    await browser.close()
    await p.stop()
    
    # Step 4: Save results to CSV
    if results:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_doctors_{profession}_{state}_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'name', 'headline', 'about', 'website', 'contact_info',
                'gmails', 'other_emails', 'all_emails', 'profile_url', 'linkedin_url'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print("\n" + "=" * 60)
        print(f"  ✅ RESULTS SAVED")
        print(f"  📁 File: {filename}")
        print(f"  📊 Profiles with emails: {len(results)} / {len(profile_urls)}")
        print("=" * 60)
        
        # Preview
        print("\n📋 SAMPLE RESULTS:")
        for i, r in enumerate(results[:5], 1):
            print(f"\n[{i}] {r['name'][:50]}")
            print(f"    📧 {r['all_emails'][:80]}")
            print(f"    🔗 {r['profile_url']}")
    else:
        print("\n❌ No profiles were successfully scraped.")
        print("   Note: LinkedIn may require a logged-in session and some profile fields are gated.")

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    asyncio.run(main())