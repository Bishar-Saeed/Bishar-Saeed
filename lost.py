



# improved upper




#!/usr/bin/env python3
"""
LinkedIn Gmail Profile Scraper — Fixed Edition
===============================================
FIXES APPLIED:
  ✅ Login wall / redirect to signup page  → cookie validation + auto re-login
  ✅ CAPTCHA / bot detection               → better stealth + human pacing
  ✅ Email not extracted from About section → 5-layer extraction strategy
  ✅ Contact info modal not opening        → multiple selector fallbacks
  ✅ Profile redirect to signup            → session check before each profile

HOW TO RUN:
  pip install playwright fake-useragent
  playwright install chromium
  python linkedin_gmail_scraper.py
"""

import csv
import json
import os
import random
import re
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── Config ────────────────────────────────────────────────────────────────────
COOKIES_FILE = "linkedin_cookies.json"
TIMESTAMP    = datetime.now().strftime("%Y%m%d_%H%M%S")
MAX_RETRIES  = 2   # retries per profile on login-wall hit

# ── Regex ─────────────────────────────────────────────────────────────────────
GMAIL_RE  = re.compile(r"[a-zA-Z0-9._%+\-]+@gmail\.com", re.IGNORECASE)
EMAIL_RE  = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
LI_RE     = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+/?")

JUNK_EMAILS = {"example", "test@", "noreply", "no-reply", "placeholder",
               "sentry", "wix", "squarespace", "wordpress"}

# ── User Agents ───────────────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
]

# ── Stealth Script ────────────────────────────────────────────────────────────
STEALTH_JS = """() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins',   { get: () => [1,2,3,4,5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
    const origQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (p) =>
        p.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : origQuery(p);
    window.chrome = { runtime:{}, loadTimes:()=>{}, csi:()=>{}, app:{} };
    delete window.__playwright;
    delete window.__pw_manual;
    delete window.calledSelenium;
    Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
    Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
}"""

# ── Timing Helpers ────────────────────────────────────────────────────────────
def human_delay(lo=2.0, hi=5.0):
    time.sleep(random.uniform(lo, hi))

def micro(lo=0.3, hi=1.0):
    time.sleep(random.uniform(lo, hi))

def long_pause(lo=10, hi=20):
    t = random.uniform(lo, hi)
    print(f"  ⏸  Resting {t:.0f}s to stay under the radar…")
    time.sleep(t)

def human_scroll(page, n=4):
    for _ in range(n):
        page.evaluate(f"window.scrollBy(0, {random.randint(250,600)})")
        micro(0.3, 0.8)
    if random.random() > 0.6:
        page.evaluate(f"window.scrollBy(0, -{random.randint(80,250)})")
        micro(0.2, 0.5)

def random_mouse(page):
    try:
        page.mouse.move(random.randint(80,1200), random.randint(80,700))
        micro(0.1,0.3)
    except Exception:
        pass

def viewport():
    return random.choice([
        {"width":1920,"height":1080}, {"width":1440,"height":900},
        {"width":1366,"height":768},  {"width":1280,"height":800},
        {"width":1536,"height":864},
    ])

# ── Session / Cookie Helpers ──────────────────────────────────────────────────
def save_cookies():
    """Open a visible browser, let user log in, then save cookies."""
    print("\n" + "="*60)
    print("  SAVE LINKEDIN COOKIES")
    print("="*60)
    print("\n  A browser will open → log into LinkedIn normally.")
    print("  After your feed loads, press ENTER here.\n")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, args=["--start-maximized"])
        ctx  = browser.new_context(user_agent=random.choice(USER_AGENTS), viewport=viewport())
        page = ctx.new_page()
        ctx.add_init_script(STEALTH_JS)
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        input("  ▶ Press ENTER once you are logged in and see your feed … ")
        cookies = ctx.cookies()
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f, indent=2)
        print(f"\n  ✅ {len(cookies)} cookies saved → {COOKIES_FILE}")
        browser.close()

def load_cookies():
    if not Path(COOKIES_FILE).exists():
        print(f"\n  ❌ {COOKIES_FILE} not found — run option 1 first.\n")
        return None
    with open(COOKIES_FILE) as f:
        return json.load(f)

def is_login_wall(page):
    """Return True if LinkedIn has kicked us to the login / signup page."""
    url  = page.url.lower()
    text = ""
    try:
        text = page.evaluate("() => document.body.innerText").lower()
    except Exception:
        pass
    return (
        "linkedin.com/login"   in url or
        "linkedin.com/signup"  in url or
        "authwall"             in url or
        "join linkedin"        in text or
        "sign in"              in text and "feed" not in url
    )

def refresh_session(ctx, cookies_path=COOKIES_FILE):
    """
    Attempt to restore the session by re-adding cookies and navigating
    to the feed.  Returns True if successful.
    """
    print("\n  ⚠  Session expired — attempting refresh …")
    try:
        with open(cookies_path) as f:
            cookies = json.load(f)
        ctx.add_cookies(cookies)
        page = ctx.pages[0]
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        human_delay(3, 6)
        if not is_login_wall(page):
            print("  ✅ Session restored.")
            return True
    except Exception as e:
        print(f"  Session refresh error: {e}")
    print("  ❌ Could not restore session. Re-save cookies (option 1) then rerun.")
    return False


def parse_cookies_from_text(text, default_domain='.linkedin.com'):
    """Parse cookies from pasted text (JSON array or header string).

    Returns list of cookie dicts suitable for Playwright's `add_cookies`.
    """
    text = (text or '').strip()
    if not text:
        return []

    # Try JSON first (DevTools export)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            cookies = []
            for c in parsed:
                name = c.get('name') or c.get('Name')
                value = c.get('value') or c.get('Value')
                domain = c.get('domain') or c.get('Domain') or default_domain
                path = c.get('path', '/')
                if name and value:
                    cookies.append({'name': name, 'value': value, 'domain': domain, 'path': path})
            return cookies
    except Exception:
        pass

    # Header-style string: 'li_at=xxx; JSESSIONID=...'
    parts = [p.strip() for p in text.split(';') if '=' in p]
    cookies = []
    for p in parts:
        try:
            name, val = p.split('=', 1)
            cookies.append({'name': name.strip(), 'value': val.strip(), 'domain': default_domain, 'path': '/'})
        except Exception:
            continue
    return cookies


def paste_cookies_prompt(save_to_file=True):
    """Prompt the user to paste cookies and save them to COOKIES_FILE.

    Returns True if cookies were parsed and saved.
    """
    print("\nPaste cookies (JSON array from devtools or 'name=value; ...'). End with an empty line:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line:
            break
        lines.append(line)
    text = "\n".join(lines)
    cookies = parse_cookies_from_text(text)
    if not cookies:
        print('  ❌ No valid cookies parsed from input.')
        return False
    if save_to_file:
        try:
            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            print(f'  ✅ Saved {len(cookies)} cookies → {COOKIES_FILE}')
            return True
        except Exception as e:
            print(f'  ❌ Failed to save cookies: {e}')
            return False
    return True


def is_search_challenge(page):
    """Detect common search engine CAPTCHA / challenge pages."""
    try:
        txt = page.evaluate("() => document.body.innerText").lower()
    except Exception:
        txt = ''
    tokens = [
        'unusual traffic', 'our systems have detected', 'please show you are not a robot',
        'sorry', 'detected unusual', 'recaptcha', 'verify you are human', 'unusual requests',
        'access denied', 'security check', 'solve the captcha', 'prepare to browse safely',
        'one more step', 'sorry, but we can\'t process your request right now'
    ]
    return any(t in txt for t in tokens)


def wait_for_manual_challenge(page, prompt=None, attempts=3):
    """Wait for the user to solve a manual search engine challenge."""
    if prompt is None:
        prompt = 'Solve the challenge in the browser, then press ENTER to continue...'
    for attempt in range(1, attempts + 1):
        input(f'  {prompt} (attempt {attempt}/{attempts})')
        try:
            page.wait_for_load_state('networkidle', timeout=15000)
        except Exception:
            pass
        human_delay(3, 6)
        try:
            if not is_search_challenge(page):
                return True
        except Exception:
            pass
        print('  Still blocked after manual solve. Please try again or switch IP/proxy.')
    return False

# ── Email Extraction (5-layer) ────────────────────────────────────────────────
def extract_emails_from_text(text):
    """Find all non-junk emails in a text blob."""
    found = set(EMAIL_RE.findall(text))
    return {e for e in found if not any(j in e.lower() for j in JUNK_EMAILS)}

def extract_gmails(text):
    return {e for e in extract_emails_from_text(text) if "gmail.com" in e.lower()}

def extract_all_emails(text):
    """Return (gmails_set, all_emails_set)."""
    all_e  = extract_emails_from_text(text)
    gmails = {e for e in all_e if "gmail.com" in e.lower()}
    return gmails, all_e

def scrape_about_section(page):
    """
    Multi-selector About extraction.
    Returns plain text of the About section or ''.
    """
    selectors = [
        # 2024-2026 LinkedIn DOM
        "div[data-generated-suggestion-target] span[aria-hidden='true']",
        "#about ~ * span[aria-hidden='true']",
        "#about + div span[aria-hidden='true']",
        ".pv-shared-text-with-see-more span[aria-hidden='true']",
        ".pv-about-section .pv-about__summary-text",
        # Generic fallback
        "section.pv-about-section",
    ]
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                txt = el.inner_text().strip()
                if len(txt) > 20:
                    return txt
        except Exception:
            pass

    # Last resort: find "About" header in page text and grab next 30 lines
    try:
        lines = page.evaluate("() => document.body.innerText").split("\n")
        for i, line in enumerate(lines):
            if line.strip().lower() == "about":
                chunk = []
                for j in range(i+1, min(i+35, len(lines))):
                    if lines[j].strip().lower() in {"experience","education","skills",
                                                     "licenses","certifications","contact"}:
                        break
                    chunk.append(lines[j].strip())
                result = " ".join(x for x in chunk if x)
                if result:
                    return result[:600]
    except Exception:
        pass
    return ""

# ── Contact Info Modal ────────────────────────────────────────────────────────
def open_contact_modal(page):
    """
    Click the 'Contact info' link/button and return (modal_text, websites[]).
    Returns ('', []) on failure.
    """
    selectors = [
        'a[href*="contact-info"]',
        'a#contact-info',
        'span.link-without-visited-state:has-text("Contact info")',
        'a:has-text("Contact info")',
        'button:has-text("Contact info")',
        '#contact-info',
    ]
    clicked = False
    for sel in selectors:
        try:
            btn = page.query_selector(sel)
            if btn:
                page.evaluate("el => el.scrollIntoView({block:'center'})", btn)
                micro(0.3, 0.7)
                btn.click()
                human_delay(2, 4)
                clicked = True
                break
        except Exception:
            pass

    if not clicked:
        return "", []

    # Grab modal content
    modal_text = ""
    websites   = []
    try:
        modal_text = page.evaluate("""
            () => {
                const m = document.querySelector(
                    '.artdeco-modal__content, [role="dialog"], .pv-contact-info__contact-type'
                );
                return m ? m.innerText : '';
            }
        """)
        websites = page.evaluate("""
            () => Array.from(
                document.querySelectorAll('.artdeco-modal a[href], [role="dialog"] a[href]')
            )
            .map(a => a.href)
            .filter(h => h.startsWith('http')
                      && !h.includes('linkedin.com')
                      && !h.includes('google.com')
                      && !h.includes('javascript'))
        """)
    except Exception:
        pass

    # Close modal
    try:
        close = page.query_selector('button[aria-label="Dismiss"], button[aria-label="Close"]')
        if close:
            close.click()
            micro(0.5, 1)
    except Exception:
        pass

    return modal_text, websites

# ── Profile Scraper ───────────────────────────────────────────────────────────
def scrape_profile(page, url, ctx, require_gmail=True):
    """
    Visit a LinkedIn profile and extract all data.
    Returns dict or None.
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=35000)
            human_delay(2.5, 5)
            page.evaluate(STEALTH_JS)

            # ── Detect login wall ─────────────────────────────────────────
            if is_login_wall(page):
                if attempt < MAX_RETRIES:
                    print(f"         🔒 Login wall hit — refreshing session (attempt {attempt+1})…")
                    if not refresh_session(ctx):
                        return None
                    continue
                else:
                    print("         🔒 Still hitting login wall after retries — skipping.")
                    return None

            # ── Detect CAPTCHA ────────────────────────────────────────────
            body_text = page.evaluate("() => document.body.innerText")
            if "captcha" in body_text.lower() or "security check" in body_text.lower():
                print("         🤖 CAPTCHA detected — pausing 60s, please solve it manually…")
                time.sleep(60)
                body_text = page.evaluate("() => document.body.innerText")

            human_scroll(page, random.randint(3, 7))
            random_mouse(page)

            body_html = page.content()

            # ── Layer 1: emails directly in page source ───────────────────
            gmails_page, all_emails_page = extract_all_emails(body_text)
            gmails_page |= extract_gmails(body_html)

            # ── Layer 2: Name ─────────────────────────────────────────────
            name = ""
            try:
                h1 = page.query_selector("h1")
                if h1:
                    name = h1.inner_text().strip()
            except Exception:
                pass

            # ── Layer 3: Headline ─────────────────────────────────────────
            headline = ""
            for sel in [
                ".text-body-medium.break-words",
                ".pv-text-details__left-panel .text-body-medium",
                "[data-generated-suggestion-target]",
            ]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        t = el.inner_text().strip()
                        if t:
                            headline = t
                            break
                except Exception:
                    pass

            # ── Layer 4: About section (enhanced) ─────────────────────────
            about = scrape_about_section(page)
            gmails_about, all_emails_about = extract_all_emails(about)

            # ── Layer 5: Contact info modal ───────────────────────────────
            modal_text, websites = open_contact_modal(page)
            gmails_modal, all_emails_modal = extract_all_emails(modal_text)

            # ── Merge all found emails ────────────────────────────────────
            all_gmails  = gmails_page | gmails_about | gmails_modal
            all_emails  = all_emails_page | all_emails_about | all_emails_modal

            # ── Apply filter ──────────────────────────────────────────────
            if require_gmail and not all_gmails:
                return None

            website = websites[0] if websites else ""

            return {
                "Full Name"   : name,
                "Headline"    : headline,
                "About"       : about[:400] if about else "",
                "Website"     : website,
                "Gmail"       : "; ".join(sorted(all_gmails)),
                "Other Email" : "; ".join(sorted(all_emails - all_gmails)),
                "LinkedIn URL": url,
            }

        except PlaywrightTimeout:
            print(f"         ⏱ Timeout on {url} (attempt {attempt+1})")
            if attempt < MAX_RETRIES:
                human_delay(5, 10)
            continue
        except Exception as e:
            print(f"         [Error] {e}")
            return None

    return None

# ── Google Search → LinkedIn URLs ─────────────────────────────────────────────
def collect_urls(page, query, max_pages, engine='google'):
    print(f"\n  Querying {engine.title()}: {query}\n")
    all_urls = []
    seen     = set()

    for p in range(max_pages):
        start = p * 10
        if engine == 'bing':
            url = (
                f"https://www.bing.com/search"
                f"?q={urllib.parse.quote(query)}&count=10&first={start+1}"
            )
            page_label = f"Bing page {p+1}/{max_pages}"
        elif engine == 'duckduckgo':
            url = (
                f"https://duckduckgo.com/html/"
                f"?q={urllib.parse.quote(query)}&s={start}"
            )
            page_label = f"DuckDuckGo page {p+1}/{max_pages}"
        else:
            url = (
                f"https://www.google.com/search"
                f"?q={urllib.parse.quote(query)}&num=10&start={start}"
            )
            page_label = f"Google page {p+1}/{max_pages}"
        print(f"  {page_label}…", end="", flush=True)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            human_delay(2, 5)
            page.evaluate(STEALTH_JS)

            if is_search_challenge(page):
                if not wait_for_manual_challenge(page, 'Solve the search challenge in the browser, then press ENTER to continue...', attempts=3):
                    print('  CAPTCHA persists — stopping collection to avoid further blocks.')
                    break
                human_delay(3, 6)
                page.evaluate(STEALTH_JS)
                if is_search_challenge(page):
                    print('  Still blocked after manual solve — stopping collection.')
                    break

            # Accept cookie banner if present
            for btn_text in ["Accept all", "Accept", "I agree", "Agree"]:
                try:
                    b = page.query_selector(f'button:has-text("{btn_text}")')
                    if b:
                        b.click(); micro(); break
                except Exception:
                    pass

            human_scroll(page, random.randint(2, 4))
            random_mouse(page)

            links = page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(h => h.includes('linkedin.com/in/'))
            """)

            new = 0
            for lnk in links:
                m = LI_RE.search(lnk)
                if m:
                    clean = m.group(0).rstrip("/").split("?")[0]
                    if clean not in seen:
                        seen.add(clean)
                        all_urls.append(clean)
                        new += 1

            print(f" +{new} (total {len(all_urls)})")

            if engine == 'google':
                next_selector = 'a#pnnext, a[aria-label="Next"]'
            elif engine == 'bing':
                next_selector = 'a.sb_pagN, a[title="Next page"]'
            else:
                next_selector = 'a.result--more__btn, a.pagination__btn--next'

            if not page.query_selector(next_selector) and p < max_pages-1:
                print(f"  No more {engine.title()} pages.")
                break

            human_delay(4, 9)

        except Exception as e:
            print(f" Error: {e}")
            human_delay(6, 12)

    print(f"\n  ✅ {len(all_urls)} unique LinkedIn URLs found.")
    return all_urls

# ── Config Prompt ─────────────────────────────────────────────────────────────
def prompt_config():
    print("\n" + "="*60)
    print("  SEARCH CONFIGURATION")
    print("="*60)
    print('\n  Examples:')
    print('  site:linkedin.com/in "doctor" "California" "@gmail.com"')
    print('  site:linkedin.com/in "physician" "Texas" "@gmail.com"')
    print('  site:linkedin.com/in "dentist" "New York" "@gmail.com"')
    print('  site:linkedin.com/in "surgeon" "Florida" "@gmail.com"')

    q = input("\n  Enter Google query (ENTER = default California doctor): ").strip()
    if not q:
        q = 'site:linkedin.com/in "doctor" "California" "@gmail.com"'

    pages = input("  Search pages to scrape (default 5): ").strip()
    try:    pages = int(pages)
    except: pages = 5

    engine = input("  Search engine [G]oogle, [B]ing, [D]uckDuckGo (default Google): ").strip().lower() or 'g'
    if engine.startswith('b'):
        engine = 'bing'
    elif engine.startswith('d'):
        engine = 'duckduckgo'
    else:
        engine = 'google'

    gmail_only = input("  Save ONLY gmail profiles? (Y/n): ").strip().lower()
    require_gmail = gmail_only != "n"

    out = f"linkedin_results_{TIMESTAMP}.csv"
    return q, pages, out, require_gmail, engine

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  LinkedIn Gmail Scraper — Fixed Anti-Block Edition")
    print("="*60)
    print("""
  [1] Save LinkedIn cookies  (do ONCE — or when session expires)
  [P] Paste cookies from clipboard/text (JSON or name=value list)
  [2] Run scraper
  [3] Exit
""")
    choice = input("  Choice: ").strip()

    if choice == "1":
        save_cookies()
        print("\n  Now run again and choose [2].\n")
        return

    if choice.lower() == 'p':
        paste_cookies_prompt(save_to_file=True)
        return

    if choice == "3":
        print("\n  Bye!\n")
        return

    if choice != "2":
        print("\n  Invalid choice.\n")
        return main()

    # ── Load cookies (prompt if missing) ──────────────────────────────────────
    cookies = load_cookies()
    if not cookies:
        print('\n  No saved cookies found.')
        choice = input('  Paste cookies now (P), Save via browser (S), or Exit (E)? [P/S/E]: ').strip().lower() or 'p'
        if choice.startswith('p'):
            ok = paste_cookies_prompt(save_to_file=True)
            if not ok:
                print('  Cookies not provided — aborting.')
                return
            cookies = load_cookies()
        elif choice.startswith('s'):
            save_cookies()
            cookies = load_cookies()
            if not cookies:
                print('  Still no cookies after save — aborting.')
                return
        else:
            print('  Exiting.')
            return

    query, max_pages, out_file, require_gmail, engine = prompt_config()
    url_file = f"linkedin_urls_{TIMESTAMP}.txt"

    fieldnames = ["Full Name","Headline","About","Website","Gmail","Other Email","LinkedIn URL"]
    csv_out    = open(out_file, "w", newline="", encoding="utf-8")
    writer     = csv.DictWriter(csv_out, fieldnames=fieldnames)
    writer.writeheader()

    saved = 0
    skipped = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--start-maximized",
                "--disable-web-security",
            ]
        )
        ctx = browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport=viewport(),
            locale="en-US",
            timezone_id="America/Los_Angeles",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        ctx.add_cookies(cookies)
        ctx.add_init_script(STEALTH_JS)
        page = ctx.new_page()

        # Warm up — visit LinkedIn feed first to confirm session is alive
        print("\n  Warming up session…")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        human_delay(3, 5)
        if is_login_wall(page):
            print("\n  ❌ Your cookies are expired. Please re-run option [1] to save fresh cookies.\n")
            browser.close()
            csv_out.close()
            return
        print("  ✅ Session confirmed — logged in.\n")

        # ── Phase 1: Collect URLs from search engine ────────────────────
        print(f"  PHASE 1 — Collecting LinkedIn URLs from {engine.title()}…")
        urls = collect_urls(page, query, max_pages, engine)

        if not urls:
            print("\n  No URLs found. Try a different query.")
            browser.close()
            csv_out.close()
            return

        with open(url_file, "w") as f:
            f.write("\n".join(urls))
        print(f"  ✅ URL list saved → {url_file}")

        # ── Phase 2: Scrape each profile ─────────────────────────────────
        print(f"\n  PHASE 2 — Scraping {len(urls)} profiles…")
        label = "(Gmail only)" if require_gmail else "(all profiles)"
        print(f"  Filter: {label}\n")

        for i, url in enumerate(urls, 1):
            print(f"  [{i:>4}/{len(urls)}] {url}")

            # Rotate UA every 8 profiles
            if i % 8 == 0:
                ctx.set_extra_http_headers({"User-Agent": random.choice(USER_AGENTS)})

            result = scrape_profile(page, url, ctx, require_gmail=require_gmail)

            if result:
                writer.writerow(result)
                csv_out.flush()
                saved += 1
                print(f"         ✉  Gmail   : {result['Gmail'] or '—'}")
                print(f"         📧 Other   : {result['Other Email'] or '—'}")
                print(f"         👤 Name    : {result['Full Name']}")
                print(f"         🏷  Headline: {result['Headline'][:70]}")
            else:
                skipped += 1
                print(f"         ⚠  {'No Gmail — skipped' if require_gmail else 'No data extracted'}")

            print()

            # Pacing — long break every 5 profiles
            if i % 5 == 0:
                long_pause(10, 20)
            else:
                human_delay(3, 8)

        browser.close()

    csv_out.close()

    print("\n" + "="*60)
    print("  ✅  DONE")
    print("="*60)
    print(f"  URL list  → {url_file}")
    print(f"  Results   → {out_file}")
    print(f"  Saved     : {saved}")
    print(f"  Skipped   : {skipped}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()