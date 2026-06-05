



# improved upper




#!/usr/bin/env python3
# """
# LinkedIn Gmail Profile Scraper — Fixed Edition
# ===============================================
# FIXES APPLIED:
#   ✅ Login wall / redirect to signup page  → cookie validation + auto re-login
#   ✅ CAPTCHA / bot detection               → better stealth + human pacing
#   ✅ Email not extracted from About section → 5-layer extraction strategy
#   ✅ Contact info modal not opening        → multiple selector fallbacks
#   ✅ Profile redirect to signup            → session check before each profile

# HOW TO RUN:
#   pip install playwright fake-useragent
#   playwright install chromium
#   python linkedin_gmail_scraper.py
# """

# import csv
# import json
# import os
# import random
# import re
# import time
# import urllib.parse
# from datetime import datetime
# from pathlib import Path
# from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# # ── Config ────────────────────────────────────────────────────────────────────
# COOKIES_FILE = "linkedin_cookies.json"
# TIMESTAMP    = datetime.now().strftime("%Y%m%d_%H%M%S")
# MAX_RETRIES  = 2   # retries per profile on login-wall hit

# # ── Regex ─────────────────────────────────────────────────────────────────────
# GMAIL_RE  = re.compile(r"[a-zA-Z0-9._%+\-]+@gmail\.com", re.IGNORECASE)
# EMAIL_RE  = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
# LI_RE     = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+/?")

# JUNK_EMAILS = {"example", "test@", "noreply", "no-reply", "placeholder",
#                "sentry", "wix", "squarespace", "wordpress"}

# # ── User Agents ───────────────────────────────────────────────────────────────
# USER_AGENTS = [
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
# ]

# # ── Stealth Script ────────────────────────────────────────────────────────────
# STEALTH_JS = """() => {
#     Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
#     Object.defineProperty(navigator, 'plugins',   { get: () => [1,2,3,4,5] });
#     Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
#     const origQuery = window.navigator.permissions.query;
#     window.navigator.permissions.query = (p) =>
#         p.name === 'notifications'
#             ? Promise.resolve({ state: Notification.permission })
#             : origQuery(p);
#     window.chrome = { runtime:{}, loadTimes:()=>{}, csi:()=>{}, app:{} };
#     delete window.__playwright;
#     delete window.__pw_manual;
#     delete window.calledSelenium;
#     Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
#     Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
# }"""

# # ── Timing Helpers ────────────────────────────────────────────────────────────
# def human_delay(lo=2.0, hi=5.0):
#     time.sleep(random.uniform(lo, hi))

# def micro(lo=0.3, hi=1.0):
#     time.sleep(random.uniform(lo, hi))

# def long_pause(lo=10, hi=20):
#     t = random.uniform(lo, hi)
#     print(f"  ⏸  Resting {t:.0f}s to stay under the radar…")
#     time.sleep(t)

# def human_scroll(page, n=4):
#     for _ in range(n):
#         page.evaluate(f"window.scrollBy(0, {random.randint(250,600)})")
#         micro(0.3, 0.8)
#     if random.random() > 0.6:
#         page.evaluate(f"window.scrollBy(0, -{random.randint(80,250)})")
#         micro(0.2, 0.5)

# def random_mouse(page):
#     try:
#         page.mouse.move(random.randint(80,1200), random.randint(80,700))
#         micro(0.1,0.3)
#     except Exception:
#         pass

# def viewport():
#     return random.choice([
#         {"width":1920,"height":1080}, {"width":1440,"height":900},
#         {"width":1366,"height":768},  {"width":1280,"height":800},
#         {"width":1536,"height":864},
#     ])

# # ── Session / Cookie Helpers ──────────────────────────────────────────────────
# def save_cookies():
#     """Open a visible browser, let user log in, then save cookies."""
#     print("\n" + "="*60)
#     print("  SAVE LINKEDIN COOKIES")
#     print("="*60)
#     print("\n  A browser will open → log into LinkedIn normally.")
#     print("  After your feed loads, press ENTER here.\n")
#     with sync_playwright() as pw:
#         browser = pw.chromium.launch(headless=False, args=["--start-maximized"])
#         ctx  = browser.new_context(user_agent=random.choice(USER_AGENTS), viewport=viewport())
#         page = ctx.new_page()
#         ctx.add_init_script(STEALTH_JS)
#         page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
#         input("  ▶ Press ENTER once you are logged in and see your feed … ")
#         cookies = ctx.cookies()
#         with open(COOKIES_FILE, "w") as f:
#             json.dump(cookies, f, indent=2)
#         print(f"\n  ✅ {len(cookies)} cookies saved → {COOKIES_FILE}")
#         browser.close()

# def load_cookies():
#     if not Path(COOKIES_FILE).exists():
#         print(f"\n  ❌ {COOKIES_FILE} not found — run option 1 first.\n")
#         return None
#     with open(COOKIES_FILE) as f:
#         return json.load(f)

# def is_login_wall(page):
#     """Return True if LinkedIn has kicked us to the login / signup page."""
#     url  = page.url.lower()
#     text = ""
#     try:
#         text = page.evaluate("() => document.body.innerText").lower()
#     except Exception:
#         pass
#     return (
#         "linkedin.com/login"   in url or
#         "linkedin.com/signup"  in url or
#         "authwall"             in url or
#         "join linkedin"        in text or
#         "sign in"              in text and "feed" not in url
#     )

# def refresh_session(ctx, cookies_path=COOKIES_FILE):
#     """
#     Attempt to restore the session by re-adding cookies and navigating
#     to the feed.  Returns True if successful.
#     """
#     print("\n  ⚠  Session expired — attempting refresh …")
#     try:
#         with open(cookies_path) as f:
#             cookies = json.load(f)
#         ctx.add_cookies(cookies)
#         page = ctx.pages[0]
#         page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
#         human_delay(3, 6)
#         if not is_login_wall(page):
#             print("  ✅ Session restored.")
#             return True
#     except Exception as e:
#         print(f"  Session refresh error: {e}")
#     print("  ❌ Could not restore session. Re-save cookies (option 1) then rerun.")
#     return False

# # ── Email Extraction (5-layer) ────────────────────────────────────────────────
# def extract_emails_from_text(text):
#     """Find all non-junk emails in a text blob."""
#     found = set(EMAIL_RE.findall(text))
#     return {e for e in found if not any(j in e.lower() for j in JUNK_EMAILS)}

# def extract_gmails(text):
#     return {e for e in extract_emails_from_text(text) if "gmail.com" in e.lower()}

# def extract_all_emails(text):
#     """Return (gmails_set, all_emails_set)."""
#     all_e  = extract_emails_from_text(text)
#     gmails = {e for e in all_e if "gmail.com" in e.lower()}
#     return gmails, all_e

# def scrape_about_section(page):
#     """
#     Multi-selector About extraction.
#     Returns plain text of the About section or ''.
#     """
#     selectors = [
#         # 2024-2026 LinkedIn DOM
#         "div[data-generated-suggestion-target] span[aria-hidden='true']",
#         "#about ~ * span[aria-hidden='true']",
#         "#about + div span[aria-hidden='true']",
#         ".pv-shared-text-with-see-more span[aria-hidden='true']",
#         ".pv-about-section .pv-about__summary-text",
#         # Generic fallback
#         "section.pv-about-section",
#     ]
#     for sel in selectors:
#         try:
#             el = page.query_selector(sel)
#             if el:
#                 txt = el.inner_text().strip()
#                 if len(txt) > 20:
#                     return txt
#         except Exception:
#             pass

#     # Last resort: find "About" header in page text and grab next 30 lines
#     try:
#         lines = page.evaluate("() => document.body.innerText").split("\n")
#         for i, line in enumerate(lines):
#             if line.strip().lower() == "about":
#                 chunk = []
#                 for j in range(i+1, min(i+35, len(lines))):
#                     if lines[j].strip().lower() in {"experience","education","skills",
#                                                      "licenses","certifications","contact"}:
#                         break
#                     chunk.append(lines[j].strip())
#                 result = " ".join(x for x in chunk if x)
#                 if result:
#                     return result[:600]
#     except Exception:
#         pass
#     return ""

# # ── Contact Info Modal ────────────────────────────────────────────────────────
# def open_contact_modal(page):
#     """
#     Click the 'Contact info' link/button and return (modal_text, websites[]).
#     Returns ('', []) on failure.
#     """
#     selectors = [
#         'a[href*="contact-info"]',
#         'a#contact-info',
#         'span.link-without-visited-state:has-text("Contact info")',
#         'a:has-text("Contact info")',
#         'button:has-text("Contact info")',
#         '#contact-info',
#     ]
#     clicked = False
#     for sel in selectors:
#         try:
#             btn = page.query_selector(sel)
#             if btn:
#                 page.evaluate("el => el.scrollIntoView({block:'center'})", btn)
#                 micro(0.3, 0.7)
#                 btn.click()
#                 human_delay(2, 4)
#                 clicked = True
#                 break
#         except Exception:
#             pass

#     if not clicked:
#         return "", []

#     # Grab modal content
#     modal_text = ""
#     websites   = []
#     try:
#         modal_text = page.evaluate("""
#             () => {
#                 const m = document.querySelector(
#                     '.artdeco-modal__content, [role="dialog"], .pv-contact-info__contact-type'
#                 );
#                 return m ? m.innerText : '';
#             }
#         """)
#         websites = page.evaluate("""
#             () => Array.from(
#                 document.querySelectorAll('.artdeco-modal a[href], [role="dialog"] a[href]')
#             )
#             .map(a => a.href)
#             .filter(h => h.startsWith('http')
#                       && !h.includes('linkedin.com')
#                       && !h.includes('google.com')
#                       && !h.includes('javascript'))
#         """)
#     except Exception:
#         pass

#     # Close modal
#     try:
#         close = page.query_selector('button[aria-label="Dismiss"], button[aria-label="Close"]')
#         if close:
#             close.click()
#             micro(0.5, 1)
#     except Exception:
#         pass

#     return modal_text, websites

# # ── Profile Scraper ───────────────────────────────────────────────────────────
# def scrape_profile(page, url, ctx, require_gmail=True):
#     """
#     Visit a LinkedIn profile and extract all data.
#     Returns dict or None.
#     """
#     for attempt in range(MAX_RETRIES + 1):
#         try:
#             page.goto(url, wait_until="domcontentloaded", timeout=35000)
#             human_delay(2.5, 5)
#             page.evaluate(STEALTH_JS)

#             # ── Detect login wall ─────────────────────────────────────────
#             if is_login_wall(page):
#                 if attempt < MAX_RETRIES:
#                     print(f"         🔒 Login wall hit — refreshing session (attempt {attempt+1})…")
#                     if not refresh_session(ctx):
#                         return None
#                     continue
#                 else:
#                     print("         🔒 Still hitting login wall after retries — skipping.")
#                     return None

#             # ── Detect CAPTCHA ────────────────────────────────────────────
#             body_text = page.evaluate("() => document.body.innerText")
#             if "captcha" in body_text.lower() or "security check" in body_text.lower():
#                 print("         🤖 CAPTCHA detected — pausing 60s, please solve it manually…")
#                 time.sleep(60)
#                 body_text = page.evaluate("() => document.body.innerText")

#             human_scroll(page, random.randint(3, 7))
#             random_mouse(page)

#             body_html = page.content()

#             # ── Layer 1: emails directly in page source ───────────────────
#             gmails_page, all_emails_page = extract_all_emails(body_text)
#             gmails_page |= extract_gmails(body_html)

#             # ── Layer 2: Name ─────────────────────────────────────────────
#             name = ""
#             try:
#                 h1 = page.query_selector("h1")
#                 if h1:
#                     name = h1.inner_text().strip()
#             except Exception:
#                 pass

#             # ── Layer 3: Headline ─────────────────────────────────────────
#             headline = ""
#             for sel in [
#                 ".text-body-medium.break-words",
#                 ".pv-text-details__left-panel .text-body-medium",
#                 "[data-generated-suggestion-target]",
#             ]:
#                 try:
#                     el = page.query_selector(sel)
#                     if el:
#                         t = el.inner_text().strip()
#                         if t:
#                             headline = t
#                             break
#                 except Exception:
#                     pass

#             # ── Layer 4: About section (enhanced) ─────────────────────────
#             about = scrape_about_section(page)
#             gmails_about, all_emails_about = extract_all_emails(about)

#             # ── Layer 5: Contact info modal ───────────────────────────────
#             modal_text, websites = open_contact_modal(page)
#             gmails_modal, all_emails_modal = extract_all_emails(modal_text)

#             # ── Merge all found emails ────────────────────────────────────
#             all_gmails  = gmails_page | gmails_about | gmails_modal
#             all_emails  = all_emails_page | all_emails_about | all_emails_modal

#             # ── Apply filter ──────────────────────────────────────────────
#             if require_gmail and not all_gmails:
#                 return None

#             website = websites[0] if websites else ""

#             return {
#                 "Full Name"   : name,
#                 "Headline"    : headline,
#                 "About"       : about[:400] if about else "",
#                 "Website"     : website,
#                 "Gmail"       : "; ".join(sorted(all_gmails)),
#                 "Other Email" : "; ".join(sorted(all_emails - all_gmails)),
#                 "LinkedIn URL": url,
#             }

#         except PlaywrightTimeout:
#             print(f"         ⏱ Timeout on {url} (attempt {attempt+1})")
#             if attempt < MAX_RETRIES:
#                 human_delay(5, 10)
#             continue
#         except Exception as e:
#             print(f"         [Error] {e}")
#             return None

#     return None

# # ── Google Search → LinkedIn URLs ─────────────────────────────────────────────
# def collect_urls(page, query, max_pages):
#     print(f"\n  Querying Google: {query}\n")
#     all_urls = []
#     seen     = set()

#     for p in range(max_pages):
#         start = p * 10
#         url   = (
#             f"https://www.google.com/search"
#             f"?q={urllib.parse.quote(query)}&num=10&start={start}"
#         )
#         print(f"  Google page {p+1}/{max_pages}…", end="", flush=True)
#         try:
#             page.goto(url, wait_until="domcontentloaded", timeout=30000)
#             human_delay(2, 5)
#             page.evaluate(STEALTH_JS)

#             # Accept cookie banner if present
#             for btn_text in ["Accept all", "Accept", "I agree", "Agree"]:
#                 try:
#                     b = page.query_selector(f'button:has-text("{btn_text}")')
#                     if b:
#                         b.click(); micro(); break
#                 except Exception:
#                     pass

#             human_scroll(page, random.randint(2, 4))
#             random_mouse(page)

#             links = page.evaluate("""
#                 () => Array.from(document.querySelectorAll('a[href]'))
#                     .map(a => a.href)
#                     .filter(h => h.includes('linkedin.com/in/'))
#             """)

#             new = 0
#             for lnk in links:
#                 m = LI_RE.search(lnk)
#                 if m:
#                     clean = m.group(0).rstrip("/").split("?")[0]
#                     if clean not in seen:
#                         seen.add(clean)
#                         all_urls.append(clean)
#                         new += 1

#             print(f" +{new} (total {len(all_urls)})")

#             if not page.query_selector('a#pnnext, a[aria-label="Next"]') and p < max_pages-1:
#                 print("  No more Google pages.")
#                 break

#             human_delay(4, 9)

#         except Exception as e:
#             print(f" Error: {e}")
#             human_delay(6, 12)

#     print(f"\n  ✅ {len(all_urls)} unique LinkedIn URLs found.")
#     return all_urls

# # ── Config Prompt ─────────────────────────────────────────────────────────────
# def prompt_config():
#     print("\n" + "="*60)
#     print("  SEARCH CONFIGURATION")
#     print("="*60)
#     print('\n  Examples:')
#     print('  site:linkedin.com/in "doctor" "California" "@gmail.com"')
#     print('  site:linkedin.com/in "physician" "Texas" "@gmail.com"')
#     print('  site:linkedin.com/in "dentist" "New York" "@gmail.com"')
#     print('  site:linkedin.com/in "surgeon" "Florida" "@gmail.com"')

#     q = input("\n  Enter Google query (ENTER = default California doctor): ").strip()
#     if not q:
#         q = 'site:linkedin.com/in "doctor" "California" "@gmail.com"'

#     pages = input("  Google pages to scrape (default 5): ").strip()
#     try:    pages = int(pages)
#     except: pages = 5

#     gmail_only = input("  Save ONLY gmail profiles? (Y/n): ").strip().lower()
#     require_gmail = gmail_only != "n"

#     out = f"linkedin_results_{TIMESTAMP}.csv"
#     return q, pages, out, require_gmail

# # ── Main ──────────────────────────────────────────────────────────────────────
# def main():
#     print("\n" + "="*60)
#     print("  LinkedIn Gmail Scraper — Fixed Anti-Block Edition")
#     print("="*60)
#     print("""
#   [1] Save LinkedIn cookies  (do ONCE — or when session expires)
#   [2] Run scraper
#   [3] Exit
# """)
#     choice = input("  Choice: ").strip()

#     if choice == "1":
#         save_cookies()
#         print("\n  Now run again and choose [2].\n")
#         return

#     if choice == "3":
#         print("\n  Bye!\n")
#         return

#     if choice != "2":
#         print("\n  Invalid choice.\n")
#         return main()

#     # ── Load cookies ──────────────────────────────────────────────────────────
#     cookies = load_cookies()
#     if not cookies:
#         return

#     query, max_pages, out_file, require_gmail = prompt_config()
#     url_file = f"linkedin_urls_{TIMESTAMP}.txt"

#     fieldnames = ["Full Name","Headline","About","Website","Gmail","Other Email","LinkedIn URL"]
#     csv_out    = open(out_file, "w", newline="", encoding="utf-8")
#     writer     = csv.DictWriter(csv_out, fieldnames=fieldnames)
#     writer.writeheader()

#     saved = 0
#     skipped = 0

#     with sync_playwright() as pw:
#         browser = pw.chromium.launch(
#             headless=False,
#             args=[
#                 "--no-sandbox",
#                 "--disable-blink-features=AutomationControlled",
#                 "--disable-dev-shm-usage",
#                 "--disable-infobars",
#                 "--start-maximized",
#                 "--disable-web-security",
#             ]
#         )
#         ctx = browser.new_context(
#             user_agent=random.choice(USER_AGENTS),
#             viewport=viewport(),
#             locale="en-US",
#             timezone_id="America/Los_Angeles",
#             extra_http_headers={
#                 "Accept-Language": "en-US,en;q=0.9",
#                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#             }
#         )
#         ctx.add_cookies(cookies)
#         ctx.add_init_script(STEALTH_JS)
#         page = ctx.new_page()

#         # Warm up — visit LinkedIn feed first to confirm session is alive
#         print("\n  Warming up session…")
#         page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
#         human_delay(3, 5)
#         if is_login_wall(page):
#             print("\n  ❌ Your cookies are expired. Please re-run option [1] to save fresh cookies.\n")
#             browser.close()
#             csv_out.close()
#             return
#         print("  ✅ Session confirmed — logged in.\n")

#         # ── Phase 1: Collect URLs from Google ────────────────────────────
#         print("  PHASE 1 — Collecting LinkedIn URLs from Google…")
#         urls = collect_urls(page, query, max_pages)

#         if not urls:
#             print("\n  No URLs found. Try a different query.")
#             browser.close()
#             csv_out.close()
#             return

#         with open(url_file, "w") as f:
#             f.write("\n".join(urls))
#         print(f"  ✅ URL list saved → {url_file}")

#         # ── Phase 2: Scrape each profile ─────────────────────────────────
#         print(f"\n  PHASE 2 — Scraping {len(urls)} profiles…")
#         label = "(Gmail only)" if require_gmail else "(all profiles)"
#         print(f"  Filter: {label}\n")

#         for i, url in enumerate(urls, 1):
#             print(f"  [{i:>4}/{len(urls)}] {url}")

#             # Rotate UA every 8 profiles
#             if i % 8 == 0:
#                 ctx.set_extra_http_headers({"User-Agent": random.choice(USER_AGENTS)})

#             result = scrape_profile(page, url, ctx, require_gmail=require_gmail)

#             if result:
#                 writer.writerow(result)
#                 csv_out.flush()
#                 saved += 1
#                 print(f"         ✉  Gmail   : {result['Gmail'] or '—'}")
#                 print(f"         📧 Other   : {result['Other Email'] or '—'}")
#                 print(f"         👤 Name    : {result['Full Name']}")
#                 print(f"         🏷  Headline: {result['Headline'][:70]}")
#             else:
#                 skipped += 1
#                 print(f"         ⚠  {'No Gmail — skipped' if require_gmail else 'No data extracted'}")

#             print()

#             # Pacing — long break every 5 profiles
#             if i % 5 == 0:
#                 long_pause(10, 20)
#             else:
#                 human_delay(3, 8)

#         browser.close()

#     csv_out.close()

#     print("\n" + "="*60)
#     print("  ✅  DONE")
#     print("="*60)
#     print(f"  URL list  → {url_file}")
#     print(f"  Results   → {out_file}")
#     print(f"  Saved     : {saved}")
#     print(f"  Skipped   : {skipped}")
#     print("="*60 + "\n")


# if __name__ == "__main__":
#     main()






# serpapi




# !/usr/bin/env python3
# """
# LinkedIn Gmail Profile Scraper — SerpAPI Edition
# =================================================
# FIXES APPLIED:
#   ✅ Google search block bypass → SerpAPI integration
#   ✅ Login wall / redirect to signup page → cookie validation + auto re-login
#   ✅ CAPTCHA / bot detection → better stealth + human pacing
#   ✅ Email not extracted from About section → 5-layer extraction strategy
#   ✅ Contact info modal not opening → multiple selector fallbacks
#   ✅ Profile redirect to signup → session check before each profile

# HOW TO RUN:
#   pip install playwright google-search-results
#   playwright install chromium
#   python linkedin_serpapi_scraper.py
# """

# # import csv
# # import json
# # import os
# # import random
# # import re
# # import time
# # import urllib.parse
# # from datetime import datetime
# # from pathlib import Path
# # from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# # # Try to import SerpAPI
# # try:
# #     from serpapi import GoogleSearch
# #     SERPAPI_AVAILABLE = True
# # except ImportError:
# #     SERPAPI_AVAILABLE = False
# #     print("⚠️ SerpAPI not installed. Run: pip install google-search-results")

# # # ── Config ────────────────────────────────────────────────────────────────────
# # COOKIES_FILE = "linkedin_cookies.json"
# # SERPAPI_KEY_FILE = "serpapi_key.json"
# # TIMESTAMP    = datetime.now().strftime("%Y%m%d_%H%M%S")
# # MAX_RETRIES  = 2   # retries per profile on login-wall hit

# # # ── Regex ─────────────────────────────────────────────────────────────────────
# # GMAIL_RE  = re.compile(r"[a-zA-Z0-9._%+\-]+@gmail\.com", re.IGNORECASE)
# # EMAIL_RE  = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
# # LI_RE     = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+/?")

# # JUNK_EMAILS = {"example", "test@", "noreply", "no-reply", "placeholder",
# #                "sentry", "wix", "squarespace", "wordpress"}

# # # ── User Agents ───────────────────────────────────────────────────────────────
# # USER_AGENTS = [
# #     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
# #     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
# #     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
# #     "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
# #     "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
# #     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
# # ]

# # # ── Stealth Script ────────────────────────────────────────────────────────────
# # STEALTH_JS = """() => {
# #     Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
# #     Object.defineProperty(navigator, 'plugins',   { get: () => [1,2,3,4,5] });
# #     Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
# #     const origQuery = window.navigator.permissions.query;
# #     window.navigator.permissions.query = (p) =>
# #         p.name === 'notifications'
# #             ? Promise.resolve({ state: Notification.permission })
# #             : origQuery(p);
# #     window.chrome = { runtime:{}, loadTimes:()=>{}, csi:()=>{}, app:{} };
# #     delete window.__playwright;
# #     delete window.__pw_manual;
# #     delete window.calledSelenium;
# #     Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
# #     Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
# # }"""

# # # ── Timing Helpers ────────────────────────────────────────────────────────────
# # def human_delay(lo=2.0, hi=5.0):
# #     time.sleep(random.uniform(lo, hi))

# # def micro(lo=0.3, hi=1.0):
# #     time.sleep(random.uniform(lo, hi))

# # def long_pause(lo=10, hi=20):
# #     t = random.uniform(lo, hi)
# #     print(f"  ⏸  Resting {t:.0f}s to stay under the radar…")
# #     time.sleep(t)

# # def human_scroll(page, n=4):
# #     for _ in range(n):
# #         page.evaluate(f"window.scrollBy(0, {random.randint(250,600)})")
# #         micro(0.3, 0.8)
# #     if random.random() > 0.6:
# #         page.evaluate(f"window.scrollBy(0, -{random.randint(80,250)})")
# #         micro(0.2, 0.5)

# # def random_mouse(page):
# #     try:
# #         page.mouse.move(random.randint(80,1200), random.randint(80,700))
# #         micro(0.1,0.3)
# #     except Exception:
# #         pass

# # def viewport():
# #     return random.choice([
# #         {"width":1920,"height":1080}, {"width":1440,"height":900},
# #         {"width":1366,"height":768},  {"width":1280,"height":800},
# #         {"width":1536,"height":864},
# #     ])

# # # ── SerpAPI Key Management ────────────────────────────────────────────────────
# # def save_serpapi_key(api_key):
# #     """Save SerpAPI key to file"""
# #     with open(SERPAPI_KEY_FILE, "w") as f:
# #         json.dump({"api_key": api_key}, f)
# #     print(f"✅ SerpAPI key saved to {SERPAPI_KEY_FILE}")

# # def load_serpapi_key():
# #     """Load SerpAPI key from file or prompt user"""
# #     if Path(SERPAPI_KEY_FILE).exists():
# #         with open(SERPAPI_KEY_FILE, "r") as f:
# #             data = json.load(f)
# #             return data.get("api_key", "")
    
# #     print("\n" + "="*60)
# #     print("  SERPAPI KEY REQUIRED")
# #     print("="*60)
# #     print("\n  SerpAPI bypasses Google blocking and finds LinkedIn profiles.")
# #     print("  Get a free key at: https://serpapi.com")
# #     print("  Free tier: 100 searches/month\n")
    
# #     api_key = input("  Enter your SerpAPI key: ").strip()
# #     if api_key:
# #         save_serpapi_key(api_key)
# #         return api_key
# #     return None

# # # ── SerpAPI Google Search (No browser needed!) ────────────────────────────────
# # def collect_urls_via_serpapi(query, max_pages=5):
# #     """
# #     Search Google using SerpAPI - NO BROWSER NEEDED!
# #     Returns list of LinkedIn profile URLs
# #     """
# #     api_key = load_serpapi_key()
# #     if not api_key:
# #         print("\n  ❌ No SerpAPI key provided. Cannot search Google.")
# #         return []
    
# #     if not SERPAPI_AVAILABLE:
# #         print("\n  ❌ SerpAPI not installed. Run: pip install google-search-results")
# #         return []
    
# #     print(f"\n  🔍 SerpAPI Search: {query}")
# #     print(f"  {'='*50}\n")
    
# #     all_urls = []
# #     seen = set()
# #     start = 0
    
# #     for page in range(max_pages):
# #         print(f"  Page {page+1}/{max_pages}...", end=" ", flush=True)
        
# #         try:
# #             # Create search parameters
# #             search_params = {
# #                 "q": query,
# #                 "api_key": api_key,
# #                 "start": start,
# #                 "num": 10
# #             }
            
# #             # Execute search
# #             search = GoogleSearch(search_params)
# #             results = search.get_dict()
            
# #             organic_results = results.get("organic_results", [])
            
# #             if not organic_results:
# #                 print("No more results")
# #                 break
            
# #             new_urls = 0
# #             for result in organic_results:
# #                 link = result.get("link", "")
# #                 if "linkedin.com/in/" in link:
# #                     clean_url = link.split("?")[0].rstrip("/")
# #                     if clean_url not in seen:
# #                         seen.add(clean_url)
# #                         all_urls.append(clean_url)
# #                         new_urls += 1
            
# #             print(f"✅ +{new_urls} (total: {len(all_urls)})")
            
# #             # Check for next page
# #             if not results.get("serpapi_pagination", {}).get("next"):
# #                 print("  📄 No more pages")
# #                 break
            
# #             start += 10
            
# #         except Exception as e:
# #             print(f"❌ Error: {e}")
# #             break
    
# #     print(f"\n  ✅ {len(all_urls)} unique LinkedIn URLs found via SerpAPI.")
# #     return all_urls

# # # ── Session / Cookie Helpers ──────────────────────────────────────────────────
# # def save_cookies():
# #     """Open a visible browser, let user log in, then save cookies."""
# #     print("\n" + "="*60)
# #     print("  SAVE LINKEDIN COOKIES")
# #     print("="*60)
# #     print("\n  A browser will open → log into LinkedIn normally.")
# #     print("  After your feed loads, press ENTER here.\n")
# #     with sync_playwright() as pw:
# #         browser = pw.chromium.launch(headless=False, args=["--start-maximized"])
# #         ctx  = browser.new_context(user_agent=random.choice(USER_AGENTS), viewport=viewport())
# #         page = ctx.new_page()
# #         ctx.add_init_script(STEALTH_JS)
# #         page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
# #         input("  ▶ Press ENTER once you are logged in and see your feed … ")
# #         cookies = ctx.cookies()
# #         with open(COOKIES_FILE, "w") as f:
# #             json.dump(cookies, f, indent=2)
# #         print(f"\n  ✅ {len(cookies)} cookies saved → {COOKIES_FILE}")
# #         browser.close()

# # def load_cookies():
# #     if not Path(COOKIES_FILE).exists():
# #         print(f"\n  ❌ {COOKIES_FILE} not found — run option 1 first.\n")
# #         return None
# #     with open(COOKIES_FILE) as f:
# #         return json.load(f)

# # def is_login_wall(page):
# #     """Return True if LinkedIn has kicked us to the login / signup page."""
# #     url  = page.url.lower()
# #     text = ""
# #     try:
# #         text = page.evaluate("() => document.body.innerText").lower()
# #     except Exception:
# #         pass
# #     return (
# #         "linkedin.com/login"   in url or
# #         "linkedin.com/signup"  in url or
# #         "authwall"             in url or
# #         "join linkedin"        in text or
# #         "sign in"              in text and "feed" not in url
# #     )

# # def refresh_session(ctx, cookies_path=COOKIES_FILE):
# #     """
# #     Attempt to restore the session by re-adding cookies and navigating
# #     to the feed.  Returns True if successful.
# #     """
# #     print("\n  ⚠  Session expired — attempting refresh …")
# #     try:
# #         with open(cookies_path) as f:
# #             cookies = json.load(f)
# #         ctx.add_cookies(cookies)
# #         page = ctx.pages[0]
# #         page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
# #         human_delay(3, 6)
# #         if not is_login_wall(page):
# #             print("  ✅ Session restored.")
# #             return True
# #     except Exception as e:
# #         print(f"  Session refresh error: {e}")
# #     print("  ❌ Could not restore session. Re-save cookies (option 1) then rerun.")
# #     return False

# # # ── Email Extraction (5-layer) ────────────────────────────────────────────────
# # def extract_emails_from_text(text):
# #     """Find all non-junk emails in a text blob."""
# #     found = set(EMAIL_RE.findall(text))
# #     return {e for e in found if not any(j in e.lower() for j in JUNK_EMAILS)}

# # def extract_gmails(text):
# #     return {e for e in extract_emails_from_text(text) if "gmail.com" in e.lower()}

# # def extract_all_emails(text):
# #     """Return (gmails_set, all_emails_set)."""
# #     all_e  = extract_emails_from_text(text)
# #     gmails = {e for e in all_e if "gmail.com" in e.lower()}
# #     return gmails, all_e

# # def scrape_about_section(page):
# #     """
# #     Multi-selector About extraction.
# #     Returns plain text of the About section or ''.
# #     """
# #     selectors = [
# #         "div[data-generated-suggestion-target] span[aria-hidden='true']",
# #         "#about ~ * span[aria-hidden='true']",
# #         "#about + div span[aria-hidden='true']",
# #         ".pv-shared-text-with-see-more span[aria-hidden='true']",
# #         ".pv-about-section .pv-about__summary-text",
# #         "section.pv-about-section",
# #     ]
# #     for sel in selectors:
# #         try:
# #             el = page.query_selector(sel)
# #             if el:
# #                 txt = el.inner_text().strip()
# #                 if len(txt) > 20:
# #                     return txt
# #         except Exception:
# #             pass

# #     try:
# #         lines = page.evaluate("() => document.body.innerText").split("\n")
# #         for i, line in enumerate(lines):
# #             if line.strip().lower() == "about":
# #                 chunk = []
# #                 for j in range(i+1, min(i+35, len(lines))):
# #                     if lines[j].strip().lower() in {"experience","education","skills",
# #                                                      "licenses","certifications","contact"}:
# #                         break
# #                     chunk.append(lines[j].strip())
# #                 result = " ".join(x for x in chunk if x)
# #                 if result:
# #                     return result[:600]
# #     except Exception:
# #         pass
# #     return ""

# # # ── Contact Info Modal ────────────────────────────────────────────────────────
# # def open_contact_modal(page):
# #     """
# #     Click the 'Contact info' link/button and return (modal_text, websites[]).
# #     Returns ('', []) on failure.
# #     """
# #     selectors = [
# #         'a[href*="contact-info"]',
# #         'a#contact-info',
# #         'span.link-without-visited-state:has-text("Contact info")',
# #         'a:has-text("Contact info")',
# #         'button:has-text("Contact info")',
# #         '#contact-info',
# #     ]
# #     clicked = False
# #     for sel in selectors:
# #         try:
# #             btn = page.query_selector(sel)
# #             if btn:
# #                 page.evaluate("el => el.scrollIntoView({block:'center'})", btn)
# #                 micro(0.3, 0.7)
# #                 btn.click()
# #                 human_delay(2, 4)
# #                 clicked = True
# #                 break
# #         except Exception:
# #             pass

# #     if not clicked:
# #         return "", []

# #     modal_text = ""
# #     websites   = []
# #     try:
# #         modal_text = page.evaluate("""
# #             () => {
# #                 const m = document.querySelector(
# #                     '.artdeco-modal__content, [role="dialog"], .pv-contact-info__contact-type'
# #                 );
# #                 return m ? m.innerText : '';
# #             }
# #         """)
# #         websites = page.evaluate("""
# #             () => Array.from(
# #                 document.querySelectorAll('.artdeco-modal a[href], [role="dialog"] a[href]')
# #             )
# #             .map(a => a.href)
# #             .filter(h => h.startsWith('http')
# #                       && !h.includes('linkedin.com')
# #                       && !h.includes('google.com')
# #                       && !h.includes('javascript'))
# #         """)
# #     except Exception:
# #         pass

# #     try:
# #         close = page.query_selector('button[aria-label="Dismiss"], button[aria-label="Close"]')
# #         if close:
# #             close.click()
# #             micro(0.5, 1)
# #     except Exception:
# #         pass

# #     return modal_text, websites

# # # ── Profile Scraper ───────────────────────────────────────────────────────────
# # def scrape_profile(page, url, ctx, require_gmail=True):
# #     """
# #     Visit a LinkedIn profile and extract all data.
# #     Returns dict or None.
# #     """
# #     for attempt in range(MAX_RETRIES + 1):
# #         try:
# #             page.goto(url, wait_until="domcontentloaded", timeout=35000)
# #             human_delay(2.5, 5)
# #             page.evaluate(STEALTH_JS)

# #             if is_login_wall(page):
# #                 if attempt < MAX_RETRIES:
# #                     print(f"         🔒 Login wall hit — refreshing session (attempt {attempt+1})…")
# #                     if not refresh_session(ctx):
# #                         return None
# #                     continue
# #                 else:
# #                     print("         🔒 Still hitting login wall after retries — skipping.")
# #                     return None

# #             body_text = page.evaluate("() => document.body.innerText")
# #             if "captcha" in body_text.lower() or "security check" in body_text.lower():
# #                 print("         🤖 CAPTCHA detected — pausing 60s, please solve it manually…")
# #                 time.sleep(60)
# #                 body_text = page.evaluate("() => document.body.innerText")

# #             human_scroll(page, random.randint(3, 7))
# #             random_mouse(page)

# #             body_html = page.content()

# #             gmails_page, all_emails_page = extract_all_emails(body_text)
# #             gmails_page |= extract_gmails(body_html)

# #             name = ""
# #             try:
# #                 h1 = page.query_selector("h1")
# #                 if h1:
# #                     name = h1.inner_text().strip()
# #             except Exception:
# #                 pass

# #             headline = ""
# #             for sel in [
# #                 ".text-body-medium.break-words",
# #                 ".pv-text-details__left-panel .text-body-medium",
# #                 "[data-generated-suggestion-target]",
# #             ]:
# #                 try:
# #                     el = page.query_selector(sel)
# #                     if el:
# #                         t = el.inner_text().strip()
# #                         if t:
# #                             headline = t
# #                             break
# #                 except Exception:
# #                     pass

# #             about = scrape_about_section(page)
# #             gmails_about, all_emails_about = extract_all_emails(about)

# #             modal_text, websites = open_contact_modal(page)
# #             gmails_modal, all_emails_modal = extract_all_emails(modal_text)

# #             all_gmails  = gmails_page | gmails_about | gmails_modal
# #             all_emails  = all_emails_page | all_emails_about | all_emails_modal

# #             if require_gmail and not all_gmails:
# #                 return None

# #             website = websites[0] if websites else ""

# #             return {
# #                 "Full Name"   : name,
# #                 "Headline"    : headline,
# #                 "About"       : about[:400] if about else "",
# #                 "Website"     : website,
# #                 "Gmail"       : "; ".join(sorted(all_gmails)),
# #                 "Other Email" : "; ".join(sorted(all_emails - all_gmails)),
# #                 "LinkedIn URL": url,
# #             }

# #         except PlaywrightTimeout:
# #             print(f"         ⏱ Timeout on {url} (attempt {attempt+1})")
# #             if attempt < MAX_RETRIES:
# #                 human_delay(5, 10)
# #             continue
# #         except Exception as e:
# #             print(f"         [Error] {e}")
# #             return None

# #     return None

# # # ── Config Prompt ─────────────────────────────────────────────────────────────
# # def prompt_config():
# #     print("\n" + "="*60)
# #     print("  SEARCH CONFIGURATION")
# #     print("="*60)
# #     print('\n  Examples:')
# #     print('  site:linkedin.com/in "doctor" "California" "@gmail.com"')
# #     print('  site:linkedin.com/in "physician" "Texas" "@gmail.com"')
# #     print('  site:linkedin.com/in "dentist" "New York" "@gmail.com"')

# #     q = input("\n  Enter Google query (ENTER = default California doctor): ").strip()
# #     if not q:
# #         q = 'site:linkedin.com/in "doctor" "California" "@gmail.com"'

# #     pages = input("  Google pages to scrape (default 5): ").strip()
# #     try:    pages = int(pages)
# #     except: pages = 5

# #     gmail_only = input("  Save ONLY gmail profiles? (Y/n): ").strip().lower()
# #     require_gmail = gmail_only != "n"

# #     out = f"linkedin_results_{TIMESTAMP}.csv"
# #     return q, pages, out, require_gmail

# # # ── Main ──────────────────────────────────────────────────────────────────────
# # def main():
# #     print("\n" + "="*60)
# #     print("  LinkedIn Gmail Scraper — SerpAPI Edition")
# #     print("="*60)
# #     print("""
# #   [1] Save LinkedIn cookies  (do ONCE — or when session expires)
# #   [2] Run scraper
# #   [3] Exit
# # """)
# #     choice = input("  Choice: ").strip()

# #     if choice == "1":
# #         save_cookies()
# #         print("\n  Now run again and choose [2].\n")
# #         return

# #     if choice == "3":
# #         print("\n  Bye!\n")
# #         return

# #     if choice != "2":
# #         print("\n  Invalid choice.\n")
# #         return main()

# #     # ── Load cookies ──────────────────────────────────────────────────────────
# #     cookies = load_cookies()
# #     if not cookies:
# #         return

# #     query, max_pages, out_file, require_gmail = prompt_config()
# #     url_file = f"linkedin_urls_{TIMESTAMP}.txt"

# #     fieldnames = ["Full Name","Headline","About","Website","Gmail","Other Email","LinkedIn URL"]
# #     csv_out    = open(out_file, "w", newline="", encoding="utf-8")
# #     writer     = csv.DictWriter(csv_out, fieldnames=fieldnames)
# #     writer.writeheader()

# #     saved = 0
# #     skipped = 0

# #     # ── Phase 1: Collect URLs via SerpAPI (NO BROWSER NEEDED!) ────────────────
# #     print("\n" + "="*60)
# #     print("  PHASE 1 — Collecting LinkedIn URLs via SerpAPI")
# #     print("  (No browser needed, bypasses Google blocking)")
# #     print("="*60)
    
# #     urls = collect_urls_via_serpapi(query, max_pages)

# #     if not urls:
# #         print("\n  No URLs found. Try a different query or check your SerpAPI key.")
# #         csv_out.close()
# #         return

# #     with open(url_file, "w") as f:
# #         f.write("\n".join(urls))
# #     print(f"  ✅ URL list saved → {url_file}")

# #     # ── Phase 2: Scrape profiles with Playwright (browser needed for auth) ───
# #     print(f"\n" + "="*60)
# #     print(f"  PHASE 2 — Scraping {len(urls)} profiles with Playwright")
# #     print("="*60)

# #     with sync_playwright() as pw:
# #         browser = pw.chromium.launch(
# #             headless=False,
# #             args=[
# #                 "--no-sandbox",
# #                 "--disable-blink-features=AutomationControlled",
# #                 "--disable-dev-shm-usage",
# #                 "--disable-infobars",
# #                 "--start-maximized",
# #                 "--disable-web-security",
# #             ]
# #         )
# #         ctx = browser.new_context(
# #             user_agent=random.choice(USER_AGENTS),
# #             viewport=viewport(),
# #             locale="en-US",
# #             timezone_id="America/Los_Angeles",
# #             extra_http_headers={
# #                 "Accept-Language": "en-US,en;q=0.9",
# #                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
# #             }
# #         )
# #         ctx.add_cookies(cookies)
# #         ctx.add_init_script(STEALTH_JS)
# #         page = ctx.new_page()

# #         # Warm up — visit LinkedIn feed first to confirm session is alive
# #         print("\n  Warming up session…")
# #         page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
# #         human_delay(3, 5)
# #         if is_login_wall(page):
# #             print("\n  ❌ Your cookies are expired. Please re-run option [1] to save fresh cookies.\n")
# #             browser.close()
# #             csv_out.close()
# #             return
# #         print("  ✅ Session confirmed — logged in.\n")

# #         print(f"  Scraping {len(urls)} profiles…")
# #         label = "(Gmail only)" if require_gmail else "(all profiles)"
# #         print(f"  Filter: {label}\n")

# #         for i, url in enumerate(urls, 1):
# #             print(f"  [{i:>4}/{len(urls)}] {url}")

# #             if i % 8 == 0:
# #                 ctx.set_extra_http_headers({"User-Agent": random.choice(USER_AGENTS)})

# #             result = scrape_profile(page, url, ctx, require_gmail=require_gmail)

# #             if result:
# #                 writer.writerow(result)
# #                 csv_out.flush()
# #                 saved += 1
# #                 print(f"         ✉  Gmail   : {result['Gmail'] or '—'}")
# #                 print(f"         📧 Other   : {result['Other Email'] or '—'}")
# #                 print(f"         👤 Name    : {result['Full Name']}")
# #                 print(f"         🏷  Headline: {result['Headline'][:70]}")
# #             else:
# #                 skipped += 1
# #                 print(f"         ⚠  {'No Gmail — skipped' if require_gmail else 'No data extracted'}")

# #             print()

# #             if i % 5 == 0:
# #                 long_pause(10, 20)
# #             else:
# #                 human_delay(3, 8)

# #         browser.close()

# #     csv_out.close()

# #     print("\n" + "="*60)
# #     print("  ✅  DONE")
# #     print("="*60)
# #     print(f"  URL list  → {url_file}")
# #     print(f"  Results   → {out_file}")
# #     print(f"  Saved     : {saved}")
# #     print(f"  Skipped   : {skipped}")
# #     print("="*60 + "\n")


# # if __name__ == "__main__":
# #     main()









# #!/usr/bin/env python3
# """
# LinkedIn People Search Scraper — Direct API Access (FIXED)
# ==================================================
# - Uses LinkedIn's internal search API (no Google)
# - Browser used ONLY once to save session
# - Fixed timeout issues with better wait strategies
# """

# import csv
# import json
# import random
# import re
# import time
# from datetime import datetime
# from pathlib import Path
# from typing import List, Dict, Optional
# import httpx
# from bs4 import BeautifulSoup

# # Try to import Playwright only for initial setup
# try:
#     from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
#     PLAYWRIGHT_AVAILABLE = True
# except ImportError:
#     PLAYWRIGHT_AVAILABLE = False
#     print("⚠️ Playwright not installed. Run: pip install playwright && playwright install chromium")

# # ============================================================================
# # CONFIGURATION
# # ============================================================================

# SESSION_FILE = "linkedin_session.json"
# TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# # Anti-detection headers
# USER_AGENTS = [
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
# ]

# # Email regex
# EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# # ============================================================================
# # SESSION MANAGEMENT (Fixed timeout issues)
# # ============================================================================

# def save_linkedin_session():
#     """
#     ONE-TIME: Use browser to get authenticated session
#     Fixed: No timeout on networkidle, uses domcontentloaded instead
#     """
#     if not PLAYWRIGHT_AVAILABLE:
#         print("❌ Playwright not available. Install with: pip install playwright && playwright install chromium")
#         return False
    
#     print("\n" + "="*60)
#     print("  SAVE LINKEDIN SESSION (One Time Only)")
#     print("="*60)
#     print("\n  This will open a browser ONCE to get your session.")
#     print("  After this, NO browser will be used.\n")
    
#     with sync_playwright() as pw:
#         browser = pw.chromium.launch(headless=False)
#         context = browser.new_context()
#         page = context.new_page()
        
#         print("  📌 Please log into LinkedIn when the browser opens...")
        
#         # Go to login page - wait for domcontentloaded instead of networkidle
#         page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        
#         input("\n  ✅ Press ENTER after you have logged in successfully...")
        
#         # Wait for feed to load - use domcontentloaded to avoid timeout
#         try:
#             page.wait_for_load_state("domcontentloaded", timeout=10000)
#         except:
#             pass
        
#         # Additional wait for any dynamic content
#         time.sleep(3)
        
#         # Extract cookies
#         cookies = context.cookies()
        
#         # Extract CSRF token from page
#         csrf_token = None
#         try:
#             csrf_token = page.evaluate("""
#                 () => {
#                     const metas = document.querySelectorAll('meta[name="csrf-token"]');
#                     return metas.length ? metas[0].getAttribute('content') : null;
#                 }
#             """)
#         except:
#             pass
        
#         # Extract JSESSIONID from cookies
#         jsessionid = None
#         for cookie in cookies:
#             if cookie['name'] == 'JSESSIONID':
#                 jsessionid = cookie['value']
#                 break
        
#         session_data = {
#             "cookies": cookies,
#             "csrf_token": csrf_token,
#             "jsessionid": jsessionid,
#             "timestamp": datetime.now().isoformat(),
#             "user_agent": page.evaluate("() => navigator.userAgent")
#         }
        
#         with open(SESSION_FILE, "w") as f:
#             json.dump(session_data, f, indent=2)
        
#         print(f"\n  ✅ Session saved to {SESSION_FILE}")
#         print(f"  ✅ Cookies saved: {len(cookies)} items")
        
#         browser.close()
#         return True

# def load_linkedin_session() -> Optional[Dict]:
#     """Load saved session data"""
#     if not Path(SESSION_FILE).exists():
#         print("\n  ❌ Session not found. Run session save first.\n")
#         return None
#     with open(SESSION_FILE, "r") as f:
#         return json.load(f)

# # ============================================================================
# # HTTPX CLIENT WITH SESSION
# # ============================================================================

# def create_authenticated_client(session_data: Dict) -> httpx.Client:
#     """Create HTTPX client with LinkedIn session"""
    
#     cookies = {c['name']: c['value'] for c in session_data['cookies']}
    
#     headers = {
#         "Accept": "application/json, text/plain, */*",
#         "Accept-Language": "en-US,en;q=0.9",
#         "Accept-Encoding": "gzip, deflate, br",
#         "User-Agent": session_data.get('user_agent', USER_AGENTS[0]),
#         "referer": "https://www.linkedin.com/",
#         "origin": "https://www.linkedin.com",
#     }
    
#     if session_data.get('csrf_token'):
#         headers["csrf-token"] = session_data['csrf_token']
#         headers["x-restli-protocol-version"] = "2.0.0"
    
#     return httpx.Client(headers=headers, cookies=cookies, timeout=30.0, follow_redirects=True)

# # ============================================================================
# # LINKEDIN PEOPLE SEARCH (Direct API)
# # ============================================================================

# def search_linkedin_people(client: httpx.Client, keywords: str, location: str, start: int = 0, count: int = 10) -> List[Dict]:
#     """
#     Search LinkedIn people using their internal API
#     """
    
#     params = {
#         "keywords": keywords,
#         "location": location,
#         "start": start,
#         "count": count,
#     }
    
#     search_url = "https://www.linkedin.com/voyager/api/search/dash/people"
    
#     try:
#         response = client.get(search_url, params=params)
        
#         if response.status_code != 200:
#             print(f"    ⚠️ API Error: {response.status_code}")
#             return []
        
#         data = response.json()
        
#         profiles = []
#         elements = data.get('data', {}).get('elements', [])
        
#         for element in elements:
#             profile = element.get('member', {})
            
#             profile_id = profile.get('publicIdentifier', '')
#             profile_url = f"https://www.linkedin.com/in/{profile_id}" if profile_id else ""
            
#             name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
#             headline = profile.get('headline', '')
            
#             profiles.append({
#                 'name': name,
#                 'headline': headline,
#                 'profile_url': profile_url,
#                 'location': profile.get('locationName', ''),
#                 'source': 'LinkedIn Search'
#             })
        
#         return profiles
        
#     except Exception as e:
#         print(f"    ❌ Search error: {e}")
#         return []

# def search_by_state_and_profession(client: httpx.Client, profession: str, state: str, max_results: int = 50) -> List[Dict]:
#     """
#     Search for professionals by profession and state
#     """
#     all_profiles = []
#     start = 0
#     count = 25
    
#     print(f"\n  🔍 Searching LinkedIn for: {profession} in {state}")
#     print(f"  {'='*50}")
    
#     while len(all_profiles) < max_results:
#         print(f"    Fetching results {start}...", end=" ", flush=True)
        
#         profiles = search_linkedin_people(client, profession, state, start, count)
        
#         if not profiles:
#             print("No more results")
#             break
        
#         all_profiles.extend(profiles)
#         print(f"✅ +{len(profiles)} (total: {len(all_profiles)})")
        
#         start += count
#         time.sleep(random.uniform(1, 2))
    
#     return all_profiles[:max_results]

# # ============================================================================
# # PROFILE DETAIL SCRAPING
# # ============================================================================

# def get_profile_details(client: httpx.Client, profile_url: str) -> Dict:
#     """Get detailed profile information including emails"""
    
#     try:
#         response = client.get(profile_url)
        
#         if response.status_code != 200:
#             return {}
        
#         html = response.text
#         soup = BeautifulSoup(html, 'html.parser')
        
#         # Check if we hit login wall
#         if "sign in" in html.lower() or "join linkedin" in html.lower():
#             print("    🔒 Session expired")
#             return {}
        
#         # Extract about section
#         about = ""
#         about_section = soup.select_one('section#about, .pv-about-section')
#         if about_section:
#             about = about_section.get_text(separator=' ', strip=True)
        
#         # Extract emails
#         emails = set(EMAIL_RE.findall(html))
#         valid_emails = [e for e in emails if '@' in e and not any(x in e for x in ['example', 'test'])]
        
#         # Extract website
#         website = ""
#         contact_section = soup.select_one('section#contact-info')
#         if contact_section:
#             for a in contact_section.find_all('a', href=True):
#                 href = a.get('href', '')
#                 if href.startswith('http') and 'linkedin.com' not in href:
#                     website = href
#                     break
        
#         return {
#             'about': about[:1000],
#             'emails': '; '.join(valid_emails),
#             'website': website
#         }
        
#     except Exception as e:
#         return {}

# # ============================================================================
# # MAIN PIPELINE
# # ============================================================================

# def main():
#     print("\n" + "="*60)
#     print("  LINKEDIN PEOPLE SEARCH SCRAPER")
#     print("  Direct LinkedIn API access")
#     print("="*60)
#     print("""
#   [1] Save LinkedIn session (ONE TIME - uses browser)
#   [2] Run scraper
#   [3] Exit
# """)
#     choice = input("  Choice: ").strip()
    
#     if choice == "1":
#         save_linkedin_session()
#         print("\n  ✅ Session saved. Now run option [2].\n")
#         return
    
#     if choice == "3":
#         print("\n  Bye!\n")
#         return
    
#     if choice != "2":
#         print("\n  Invalid choice.\n")
#         return main()
    
#     # Load session
#     session_data = load_linkedin_session()
#     if not session_data:
#         return
    
#     # Get search parameters
#     print("\n" + "="*60)
#     print("  SEARCH PARAMETERS")
#     print("="*60)
    
#     profession = input("\n📌 Profession (doctor, dentist, cardiologist): ").strip()
#     state = input("📍 State (California, Texas, New York): ").strip()
#     max_results = int(input("🎯 Max results (default 50): ") or "50")
#     require_email = input("📧 Save ONLY profiles with emails? (Y/n): ").strip().lower() != "n"
    
#     # Create authenticated client
#     client = create_authenticated_client(session_data)
    
#     # Search for people
#     print("\n" + "="*60)
#     print("  PHASE 1: Searching LinkedIn for profiles")
#     print("="*60)
    
#     profiles = search_by_state_and_profession(client, profession, state, max_results)
    
#     if not profiles:
#         print("\n  ❌ No profiles found. Try different search terms.")
#         client.close()
#         return
    
#     # Get detailed profiles
#     print("\n" + "="*60)
#     print(f"  PHASE 2: Getting details for {len(profiles)} profiles")
#     print("="*60 + "\n")
    
#     results = []
#     for i, profile in enumerate(profiles, 1):
#         print(f"  [{i}/{len(profiles)}] {profile['name'][:50]}")
        
#         details = get_profile_details(client, profile['profile_url'])
        
#         profile['about'] = details.get('about', '')
#         profile['emails'] = details.get('emails', '')
#         profile['website'] = details.get('website', '')
        
#         has_email = bool(profile['emails'])
        
#         if require_email and not has_email:
#             print(f"    ⚠️ No email — skipping")
#         else:
#             print(f"    ✅ Email: {profile['emails'][:50] or 'None'}")
#             print(f"    🌐 Website: {profile['website'][:50] or 'None'}")
#             results.append(profile)
        
#         time.sleep(random.uniform(1, 2))
    
#     client.close()
    
#     # Save results
#     if results:
#         filename = f"linkedin_doctors_{profession}_{state}_{TIMESTAMP}.csv"
#         with open(filename, 'w', newline='', encoding='utf-8') as f:
#             fieldnames = ['name', 'headline', 'location', 'emails', 'website', 'about', 'profile_url', 'source']
#             writer = csv.DictWriter(f, fieldnames=fieldnames)
#             writer.writeheader()
#             writer.writerows(results)
        
#         print("\n" + "="*60)
#         print(f"  ✅ RESULTS SAVED")
#         print(f"  📁 {filename}")
#         print(f"  📊 Profiles with data: {len(results)}/{len(profiles)}")
#         print("="*60)
#     else:
#         print("\n  ❌ No profiles with emails found.")

# if __name__ == "__main__":
#     main()





#!/usr/bin/env python3
"""
LinkedIn People Search - PURE HTTP (No Browser)
================================================
- Uses HTTP requests only (httpx)
- No browser automation, no Playwright
- Uses saved cookies for authentication
- Direct access to LinkedIn search results
"""

import csv
import json
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup

# ============================================================================
# CONFIGURATION
# ============================================================================

SESSION_FILE = "linkedin_session.json"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Rotating User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

# Email regex
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# ============================================================================
# SESSION MANAGEMENT (One-time cookie extraction - NO BROWSER AFTER)
# ============================================================================

def manual_cookie_instructions():
    """Instructions for manual cookie extraction (one time only)"""
    print("\n" + "="*60)
    print("  MANUAL COOKIE EXTRACTION (One Time Only)")
    print("="*60)
    print("""
  📋 STEPS to get cookies (NO automation, just once):
  
  1. Log into linkedin.com in your browser
  2. Open Developer Tools (F12) → Application/Storage → Cookies
  3. Find https://www.linkedin.com
  4. Copy these cookies as JSON:
     
     - li_at (most important)
     - JSESSIONID
     - lidc
     - bcookie
     
  5. Also get CSRF token from page source:
     - View page source, search for "csrf-token"
     
  Example JSON format:
  {
    "cookies": [
      {"name": "li_at", "value": "AQED...", "domain": ".linkedin.com"},
      {"name": "JSESSIONID", "value": "ajax:...", "domain": ".linkedin.com"}
    ],
    "csrf_token": "ajax:1234567890"
  }
  """)
    
    print("  📋 Paste the JSON here (then press Enter twice):")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    
    try:
        cookies_text = "".join(lines)
        session_data = json.loads(cookies_text)
        with open(SESSION_FILE, "w") as f:
            json.dump(session_data, f, indent=2)
        print(f"\n  ✅ Session saved to {SESSION_FILE}")
        return session_data
    except json.JSONDecodeError as e:
        print(f"\n  ❌ Invalid JSON: {e}")
        return None

def load_session() -> Optional[Dict]:
    """Load saved session data"""
    if not Path(SESSION_FILE).exists():
        return None
    with open(SESSION_FILE, "r") as f:
        return json.load(f)

# ============================================================================
# HTTPX CLIENT
# ============================================================================

def create_authenticated_client(session_data: Dict) -> httpx.Client:
    """Create HTTPX client with LinkedIn session"""
    
    cookies = {c['name']: c['value'] for c in session_data.get('cookies', [])}
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://www.linkedin.com/",
        "Origin": "https://www.linkedin.com",
    }
    
    if session_data.get('csrf_token'):
        headers["csrf-token"] = session_data['csrf_token']
    
    return httpx.Client(headers=headers, cookies=cookies, timeout=30.0, follow_redirects=True)

# ============================================================================
# DIRECT LINKEDIN SEARCH (HTTP Only)
# ============================================================================

def search_linkedin_people_http(client: httpx.Client, profession: str, state: str, start: int = 0, count: int = 10) -> Dict:
    """
    Search LinkedIn people using direct HTTP request to search endpoint
    """
    
    # Build the search URL
    keywords = f"{profession} {state}"
    
    # LinkedIn's search endpoint (this works with proper cookies)
    search_url = "https://www.linkedin.com/search/results/people/"
    
    params = {
        "keywords": keywords,
        "origin": "GLOBAL_SEARCH_HEADER",
        "pageNum": start // count + 1 if start > 0 else 1,
    }
    
    # Add headers to look like a real browser
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Referer": "https://www.linkedin.com/feed/",
    }
    
    try:
        response = client.get(search_url, params=params, headers=headers)
        
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}", "profiles": []}
        
        html = response.text
        
        # Check for login wall
        if "sign in" in html.lower() or "join linkedin" in html.lower():
            return {"error": "session_expired", "profiles": []}
        
        # Parse HTML to extract profiles
        soup = BeautifulSoup(html, 'html.parser')
        profiles = []
        
        # Find search result containers
        result_selectors = [
            '.reusable-search__result-container',
            '.entity-result',
            'li.search-result',
            'div[data-urn]'
        ]
        
        results = []
        for selector in result_selectors:
            results = soup.select(selector)
            if results:
                break
        
        for result in results:
            # Extract profile URL
            profile_link = result.select_one('a[href*="/in/"]')
            if not profile_link:
                continue
            
            profile_url = profile_link.get('href', '')
            if profile_url and not profile_url.startswith('http'):
                profile_url = f"https://www.linkedin.com{profile_url}"
            profile_url = profile_url.split('?')[0]
            
            # Extract name
            name_elem = result.select_one('.entity-result__title-text a, .actor-name, .name')
            name = name_elem.get_text(strip=True) if name_elem else ""
            
            # Extract headline
            headline_elem = result.select_one('.entity-result__primary-subtitle, .subline')
            headline = headline_elem.get_text(strip=True) if headline_elem else ""
            
            # Extract location
            location_elem = result.select_one('.entity-result__secondary-subtitle, .location')
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            profiles.append({
                'name': name,
                'headline': headline,
                'location': location,
                'profile_url': profile_url
            })
        
        return {"error": None, "profiles": profiles, "html_length": len(html)}
        
    except Exception as e:
        return {"error": str(e), "profiles": []}

def search_all_pages(client: httpx.Client, profession: str, state: str, max_results: int = 50) -> List[Dict]:
    """
    Search multiple pages to get more results
    """
    all_profiles = []
    page = 1
    
    print(f"\n  🔍 Searching LinkedIn (HTTP) for: {profession} in {state}")
    print(f"  {'='*50}")
    
    while len(all_profiles) < max_results and page <= 5:
        print(f"    Page {page}...", end=" ", flush=True)
        
        result = search_linkedin_people_http(client, profession, state, (page-1) * 10, 10)
        
        if result.get("error"):
            print(f"❌ {result['error']}")
            break
        
        profiles = result.get("profiles", [])
        if not profiles:
            print("No more results")
            break
        
        # Add new profiles
        new_count = 0
        for profile in profiles:
            if profile['profile_url'] not in [p['profile_url'] for p in all_profiles]:
                all_profiles.append(profile)
                new_count += 1
        
        print(f"✅ +{new_count} (total: {len(all_profiles)})")
        
        page += 1
        time.sleep(random.uniform(1, 2))
    
    return all_profiles[:max_results]

# ============================================================================
# PROFILE DETAIL SCRAPING (HTTP Only)
# ============================================================================

def get_profile_details_http(client: httpx.Client, profile_url: str) -> Dict:
    """
    Get detailed profile information using HTTP request
    """
    try:
        response = client.get(profile_url)
        
        if response.status_code != 200:
            return {}
        
        html = response.text
        
        # Check for login wall
        if "sign in" in html.lower() or "join linkedin" in html.lower():
            return {'error': 'session_expired'}
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract about section
        about = ""
        about_selectors = [
            'section#about',
            '.pv-about-section',
            '.pv-shared-text-with-see-more'
        ]
        for selector in about_selectors:
            about_elem = soup.select_one(selector)
            if about_elem:
                about = about_elem.get_text(separator=' ', strip=True)
                break
        
        # Extract emails from about section
        emails = []
        if about:
            found_emails = EMAIL_RE.findall(about)
            for email in found_emails:
                if 'gmail.com' in email.lower():
                    emails.append(email)
        
        # Extract website
        website = ""
        contact_section = soup.select_one('section#contact-info')
        if contact_section:
            for a in contact_section.find_all('a', href=True):
                href = a.get('href', '')
                if href.startswith('http') and 'linkedin.com' not in href:
                    website = href
                    break
        
        return {
            'about': about[:1000] if about else "",
            'emails': '; '.join(emails),
            'website': website,
            'has_gmail': len(emails) > 0
        }
        
    except Exception as e:
        return {'error': str(e)}

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    print("\n" + "="*60)
    print("  LINKEDIN PEOPLE SEARCH - PURE HTTP")
    print("  No browser, no automation - just HTTP requests")
    print("="*60)
    print("""
  [1] Set up cookies (ONE TIME - manual extraction)
  [2] Run scraper
  [3] Exit
""")
    choice = input("  Choice: ").strip()
    
    if choice == "1":
        manual_cookie_instructions()
        print("\n  ✅ Setup complete. Run option [2] to scrape.\n")
        return
    
    if choice == "3":
        print("\n  Bye!\n")
        return
    
    if choice != "2":
        print("\n  Invalid choice.\n")
        return main()
    
    # Load session
    session_data = load_session()
    if not session_data:
        print("\n  ❌ No session found. Run option [1] first.\n")
        return
    
    # Get search parameters
    print("\n" + "="*60)
    print("  SEARCH PARAMETERS")
    print("="*60)
    
    profession = input("\n📌 Profession (doctor, dentist, cardiologist): ").strip()
    state = input("📍 State (California, Texas, New York): ").strip()
    max_results = int(input("🎯 Max results (default 50): ") or "50")
    require_gmail = input("📧 Save ONLY profiles with Gmail? (Y/n): ").strip().lower() != "n"
    
    # Create HTTP client
    client = create_authenticated_client(session_data)
    
    # Search for profiles
    print("\n" + "="*60)
    print("  PHASE 1: Searching LinkedIn (HTTP)")
    print("="*60)
    
    profiles = search_all_pages(client, profession, state, max_results)
    
    if not profiles:
        print("\n  ❌ No profiles found.")
        client.close()
        return
    
    # Get profile details
    print("\n" + "="*60)
    print(f"  PHASE 2: Getting details for {len(profiles)} profiles")
    print("  Looking for Gmail addresses...")
    print("="*60 + "\n")
    
    results = []
    for i, profile in enumerate(profiles, 1):
        print(f"  [{i}/{len(profiles)}] {profile['name'][:50]}")
        
        details = get_profile_details_http(client, profile['profile_url'])
        
        if details.get('error') == 'session_expired':
            print("      ❌ Session expired - stopping")
            break
        
        has_gmail = details.get('has_gmail', False)
        
        if require_gmail and not has_gmail:
            print(f"      ⚠️ No Gmail - skipping")
        else:
            print(f"      ✅ Gmail: {details.get('emails', 'None')}")
            print(f"      🌐 Website: {details.get('website', 'None')[:50]}")
            
            results.append({
                'name': profile['name'],
                'headline': profile['headline'],
                'location': profile['location'],
                'email': details.get('emails', ''),
                'website': details.get('website', ''),
                'about': details.get('about', '')[:500],
                'profile_url': profile['profile_url']
            })
        
        time.sleep(random.uniform(0.5, 1.5))
    
    client.close()
    
    # Save results
    if results:
        filename = f"linkedin_doctors_{profession}_{state}_{TIMESTAMP}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['name', 'headline', 'location', 'email', 'website', 'about', 'profile_url']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print("\n" + "="*60)
        print(f"  ✅ RESULTS SAVED")
        print(f"  📁 {filename}")
        print(f"  📊 Profiles with Gmail: {len(results)}/{len(profiles)}")
        print("="*60)
        
        # Preview
        print("\n📋 PREVIEW:")
        for i, r in enumerate(results[:5], 1):
            print(f"\n[{i}] {r['name']}")
            print(f"    📧 {r['email'] or 'No email'}")
            print(f"    🌐 {r['website'] or 'No website'}")
            print(f"    🔗 {r['profile_url']}")
    else:
        print("\n  ❌ No profiles with Gmail found.")

if __name__ == "__main__":
    main()