#!/usr/bin/env python3
"""
LinkedIn Gmail Profile Scraper — v3 Anti-CAPTCHA Edition
=========================================================

ROOT CAUSES OF 2ND-RUN CAPTCHA (all fixed here):
  ✅ Google sees same browser fingerprint again     → Persistent browser profile
                                                      (reuses real cookies/history)
  ✅ LinkedIn session cookie expired between runs   → Auto-detect + prompt re-login
  ✅ Google rate-limits same IP + query pattern     → Bing fallback + query variation
  ✅ CAPTCHA appears mid-run with no recovery       → Manual-solve pause + auto-resume
  ✅ Already-scraped URLs re-visited on restart     → Progress file (resume support)
  ✅ Too many requests too fast                     → Adaptive pacing + jitter

HOW TO RUN (first time):
  pip install playwright
  playwright install chromium
  python linkedin_gmail_scraper.py
  → Choose [1] to create browser profile & log in (once)
  → Choose [2] every time after that

HOW TO RUN (subsequent times):
  python linkedin_gmail_scraper.py → Choose [2] directly
  (No need to redo option 1 unless LinkedIn asks you to log in again)
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROFILE_DIR   = Path("browser_profile")   # ← persistent Chromium profile
PROGRESS_FILE = "scrape_progress.json"    # ← tracks already-scraped URLs
TIMESTAMP     = datetime.now().strftime("%Y%m%d_%H%M%S")
MAX_RETRIES   = 2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  REGEX
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
LI_RE    = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+/?")

JUNK = {"example.com","test@","noreply","no-reply","placeholder",
        "sentry.io","wixpress","squarespace","wordpress","yourname"}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  USER AGENTS  (kept fresh for 2026)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Safari/537.36",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEALTH  (removes ALL Playwright/automation fingerprints)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEALTH_JS = """() => {
    // Core automation flags
    Object.defineProperty(navigator, 'webdriver',    { get: () => undefined });
    Object.defineProperty(navigator, 'plugins',      { get: () => [1,2,3,4,5] });
    Object.defineProperty(navigator, 'languages',    { get: () => ['en-US','en'] });
    Object.defineProperty(navigator, 'platform',     { get: () => 'Win32' });
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
    Object.defineProperty(screen, 'colorDepth',      { get: () => 24 });

    // Permissions spoof
    const origPQ = window.navigator.permissions.query;
    window.navigator.permissions.query = (p) =>
        p.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : origPQ(p);

    // Chrome object (headless Chrome lacks this)
    if (!window.chrome) {
        window.chrome = { runtime:{}, loadTimes:()=>{}, csi:()=>{}, app:{} };
    }

    // Remove Playwright globals
    ['__playwright','__pw_manual','calledSelenium','_Selenium_IDE_Recorder',
     '__webdriver_script_fn','__driver_evaluate','__webdriver_evaluate',
     '__selenium_evaluate','__fxdriver_evaluate','__driver_unwrapped',
     '__webdriver_unwrapped','__selenium_unwrapped','__fxdriver_unwrapped'
    ].forEach(k => { try { delete window[k]; } catch(e){} });
}"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TIMING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def human_delay(lo=2.0, hi=5.0):
    time.sleep(random.uniform(lo, hi))

def micro(lo=0.2, hi=0.9):
    time.sleep(random.uniform(lo, hi))

def long_pause(lo=12, hi=25):
    t = random.uniform(lo, hi)
    print(f"  ⏸  Cooling down {t:.0f}s …")
    time.sleep(t)

def human_scroll(page, n=4):
    for _ in range(n):
        page.evaluate(f"window.scrollBy(0, {random.randint(200,700)})")
        micro(0.3, 0.9)
    if random.random() > 0.5:
        page.evaluate(f"window.scrollBy(0, -{random.randint(60,200)})")
        micro(0.2, 0.6)

def random_mouse(page):
    try:
        page.mouse.move(random.randint(80,1200), random.randint(80,700))
        micro(0.1, 0.3)
    except Exception:
        pass

def vp():
    return random.choice([
        {"width":1920,"height":1080}, {"width":1440,"height":900},
        {"width":1366,"height":768},  {"width":1280,"height":800},
        {"width":1536,"height":864},
    ])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CAPTCHA / WALL DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def is_captcha(page):
    url  = page.url.lower()
    try:
        txt = page.evaluate("() => document.body.innerText").lower()
    except Exception:
        txt = ""
    signals = [
        "captcha" in url,
        "recaptcha" in txt,
        "security check" in txt,
        "are you a robot" in txt,
        "unusual traffic" in txt,
        "verify you're human" in txt,
        "challenge" in url and "google" in url,
        "/sorry/" in url,
    ]
    return any(signals)

def is_linkedin_wall(page):
    url = page.url.lower()
    try:
        txt = page.evaluate("() => document.body.innerText").lower()
    except Exception:
        txt = ""
    return (
        "linkedin.com/login"  in url or
        "linkedin.com/signup" in url or
        "authwall"            in url or
        ("join linkedin"      in txt) or
        ("sign in"            in txt and "/feed" not in url and "/in/" not in url)
    )

def handle_captcha(page, source=""):
    """Pause and let the user solve the CAPTCHA manually."""
    print(f"\n  🤖  CAPTCHA detected on {source}")
    print("  ┌─────────────────────────────────────────────────────┐")
    print("  │  Please solve the CAPTCHA in the browser window.   │")
    print("  │  Once you're past it, press ENTER here to resume.  │")
    print("  └─────────────────────────────────────────────────────┘")
    input("  ▶ Press ENTER after solving CAPTCHA … ")
    human_delay(2, 4)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PERSISTENT BROWSER PROFILE  ← KEY FIX FOR 2ND-RUN CAPTCHA
#
#  Using launch_persistent_context() means Chromium stores cookies,
#  localStorage, and history on disk — exactly like a real browser.
#  Google and LinkedIn see a "returning" browser, not a fresh one every run.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def launch_browser(pw):
    """Launch Chromium with a persistent user data directory."""
    PROFILE_DIR.mkdir(exist_ok=True)
    ctx = pw.chromium.launch_persistent_context(
        str(PROFILE_DIR),
        headless=False,
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-infobars",
            "--start-maximized",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            f"--user-agent={random.choice(USER_AGENTS)}",
        ],
        viewport=vp(),
        locale="en-US",
        timezone_id="America/Los_Angeles",
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        ignore_https_errors=True,
    )
    ctx.add_init_script(STEALTH_JS)
    return ctx

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SESSION SETUP  (option 1 — run once)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def setup_session():
    """
    Opens the persistent browser so the user can log into LinkedIn
    and optionally Google.  Saves the session inside PROFILE_DIR.
    """
    print("\n" + "="*60)
    print("  ONE-TIME SETUP: Log In to LinkedIn (& optionally Google)")
    print("="*60)
    print("""
  A browser window will open.
  1. Log into LinkedIn  →  wait for your feed
  2. Open a new tab, go to google.com  →  log into Google (optional
     but helps avoid CAPTCHA on Google searches)
  3. Come back here and press ENTER.

  Your session is saved in the 'browser_profile/' folder.
  You won't need to log in again unless LinkedIn signs you out.
""")
    with sync_playwright() as pw:
        ctx  = launch_browser(pw)
        page = ctx.new_page()
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        input("  ▶ Press ENTER once logged in (feed visible) … ")
        print(f"\n  ✅ Session saved in: {PROFILE_DIR}/")
        ctx.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SESSION CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_linkedin_session(page):
    """
    Navigate to LinkedIn feed to confirm session is live.
    If hit with login wall, prompt manual login and wait.
    Returns True if session ok, False if unrecoverable.
    """
    print("  Checking LinkedIn session…")
    page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
    human_delay(2, 4)

    if is_captcha(page):
        handle_captcha(page, "LinkedIn")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        human_delay(2, 4)

    if is_linkedin_wall(page):
        print("\n  ⚠  LinkedIn session expired — please log in in the browser window.")
        print("  Press ENTER once you are on your LinkedIn feed.\n")
        input("  ▶ Press ENTER after logging in … ")
        human_delay(2, 4)
        if is_linkedin_wall(page):
            print("  ❌ Still hitting login wall. Run option [1] again.")
            return False

    print("  ✅ LinkedIn session confirmed.\n")
    return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROGRESS / RESUME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def load_progress():
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE) as f:
            return set(json.load(f))
    return set()

def save_progress(done_set):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(list(done_set), f)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  EMAIL EXTRACTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def clean_emails(raw_set):
    return {e for e in raw_set if not any(j in e.lower() for j in JUNK)}

def find_emails(text):
    return clean_emails(set(EMAIL_RE.findall(text)))

def split_gmail(emails):
    g = {e for e in emails if "gmail.com" in e.lower()}
    return g, emails - g

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ABOUT SECTION EXTRACTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_about(page):
    selectors = [
        "#about ~ * span[aria-hidden='true']",
        "#about + div span[aria-hidden='true']",
        "div[data-generated-suggestion-target] span[aria-hidden='true']",
        ".pv-shared-text-with-see-more span[aria-hidden='true']",
        ".pv-about-section .pv-about__summary-text",
        "section.pv-about-section",
    ]
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                t = el.inner_text().strip()
                if len(t) > 20:
                    return t
        except Exception:
            pass

    # Text fallback: scan for "About" header in page body
    try:
        lines = page.evaluate("() => document.body.innerText").split("\n")
        for i, ln in enumerate(lines):
            if ln.strip().lower() == "about":
                chunk, stops = [], {"experience","education","skills","licenses",
                                    "certifications","contact","featured","activity"}
                for j in range(i+1, min(i+40, len(lines))):
                    if lines[j].strip().lower() in stops:
                        break
                    chunk.append(lines[j].strip())
                out = " ".join(x for x in chunk if x)
                if out:
                    return out[:700]
    except Exception:
        pass
    return ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONTACT INFO MODAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def open_contact_modal(page):
    btn_selectors = [
        'a[href*="contact-info"]',
        'a#contact-info',
        'span.link-without-visited-state:has-text("Contact info")',
        'a:has-text("Contact info")',
        'button:has-text("Contact info")',
        '#contact-info',
    ]
    clicked = False
    for sel in btn_selectors:
        try:
            btn = page.query_selector(sel)
            if btn:
                page.evaluate("el => el.scrollIntoView({block:'center'})", btn)
                micro(0.4, 0.8)
                btn.click()
                human_delay(1.5, 3.5)
                clicked = True
                break
        except Exception:
            pass

    if not clicked:
        return "", []

    modal_text, websites = "", []
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
            ).map(a=>a.href).filter(h =>
                h.startsWith('http') &&
                !h.includes('linkedin.com') &&
                !h.includes('google.com') &&
                !h.startsWith('javascript')
            )
        """)
    except Exception:
        pass

    # Close modal
    for sel in ['button[aria-label="Dismiss"]','button[aria-label="Close"]','button.artdeco-modal__dismiss']:
        try:
            b = page.query_selector(sel)
            if b:
                b.click(); micro(0.4, 0.9); break
        except Exception:
            pass

    return modal_text, websites

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROFILE SCRAPER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def scrape_profile(page, url, require_gmail=True):
    for attempt in range(MAX_RETRIES + 1):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=35000)
            human_delay(2.5, 5.5)
            page.evaluate(STEALTH_JS)

            # CAPTCHA check
            if is_captcha(page):
                handle_captcha(page, url)
                page.goto(url, wait_until="domcontentloaded", timeout=35000)
                human_delay(2, 4)

            # Login wall check
            if is_linkedin_wall(page):
                if attempt < MAX_RETRIES:
                    print("         🔒 Login wall — waiting for manual re-login…")
                    print("         ▶ Please log in the browser, then press ENTER.")
                    input()
                    continue
                else:
                    print("         🔒 Persistent login wall — skipping profile.")
                    return None

            body_text = page.evaluate("() => document.body.innerText")
            body_html = page.content()

            # Scroll to load lazy sections
            human_scroll(page, random.randint(4, 8))
            random_mouse(page)

            # ── Name ──────────────────────────────────────────────────────
            name = ""
            try:
                h1 = page.query_selector("h1")
                if h1:
                    name = h1.inner_text().strip()
            except Exception:
                pass

            # ── Headline ──────────────────────────────────────────────────
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
                            headline = t; break
                except Exception:
                    pass

            # ── About ─────────────────────────────────────────────────────
            about = get_about(page)
            # Re-read body text after scroll (lazy-loaded content)
            body_text = page.evaluate("() => document.body.innerText")

            # ── Email: all layers ─────────────────────────────────────────
            emails_body  = find_emails(body_text)
            emails_html  = find_emails(body_html)
            emails_about = find_emails(about)

            # ── Contact modal ─────────────────────────────────────────────
            modal_text, websites = open_contact_modal(page)
            emails_modal = find_emails(modal_text)

            # Merge
            all_emails = emails_body | emails_html | emails_about | emails_modal
            gmails, others = split_gmail(all_emails)

            if require_gmail and not gmails:
                return None

            return {
                "Full Name"   : name,
                "Headline"    : headline,
                "About"       : about[:450] if about else "",
                "Website"     : websites[0] if websites else "",
                "Gmail"       : "; ".join(sorted(gmails)),
                "Other Email" : "; ".join(sorted(others)),
                "LinkedIn URL": url,
            }

        except PlaywrightTimeout:
            print(f"         ⏱  Timeout (attempt {attempt+1})")
            if attempt < MAX_RETRIES:
                human_delay(5, 10)
        except Exception as e:
            print(f"         [Error] {e}")
            return None

    return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GOOGLE / BING SEARCH  →  LinkedIn URLs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Slight query variations to reduce Google's pattern detection
def vary_query(q):
    variations = [
        q,
        q.replace('"@gmail.com"', '"gmail.com"'),
        q.replace('"@gmail.com"', 'gmail'),
        q + " -jobs -apply",
    ]
    return random.choice(variations)

def collect_urls_google(page, query, max_pages):
    print("  Source: Google")
    all_urls, seen = [], set()

    for p in range(max_pages):
        q_var = vary_query(query)
        start = p * 10
        url   = (f"https://www.google.com/search"
                 f"?q={urllib.parse.quote(q_var)}&num=10&start={start}&hl=en")

        print(f"  Page {p+1}/{max_pages}…", end="", flush=True)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            human_delay(2, 5)
            page.evaluate(STEALTH_JS)

            # Accept cookie/consent banner
            for label in ["Accept all","Accept","I agree","Agree","Reject all"]:
                try:
                    b = page.query_selector(f'button:has-text("{label}")')
                    if b: b.click(); micro(); break
                except Exception:
                    pass

            # CAPTCHA?
            if is_captcha(page):
                handle_captcha(page, f"Google page {p+1}")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                human_delay(2, 4)
                if is_captcha(page):
                    print(" CAPTCHA not solved — switching to Bing")
                    return all_urls, True   # signal: try Bing

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
                        seen.add(clean); all_urls.append(clean); new += 1

            print(f" +{new} (total {len(all_urls)})")

            has_next = page.query_selector('a#pnnext, a[aria-label="Next"]')
            if not has_next and p < max_pages - 1:
                print("  No more Google pages.")
                break

            human_delay(5, 12)   # longer gap between pages

        except Exception as e:
            print(f" Error: {e}")
            human_delay(6, 12)

    return all_urls, False

def collect_urls_bing(page, query, max_pages):
    """Bing fallback when Google keeps CAPTCHAing."""
    print("  Source: Bing (Google CAPTCHA fallback)")
    # Convert Google syntax to Bing syntax
    bing_query = query.replace("site:linkedin.com/in", "site:linkedin.com/in")
    all_urls, seen = [], set()

    for p in range(max_pages):
        first = p * 10 + 1
        url   = (f"https://www.bing.com/search"
                 f"?q={urllib.parse.quote(bing_query)}&first={first}&count=10")

        print(f"  Bing page {p+1}/{max_pages}…", end="", flush=True)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            human_delay(2, 5)
            page.evaluate(STEALTH_JS)

            if is_captcha(page):
                handle_captcha(page, f"Bing page {p+1}")

            human_scroll(page, 3)

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
                        seen.add(clean); all_urls.append(clean); new += 1

            print(f" +{new} (total {len(all_urls)})")
            human_delay(4, 9)

        except Exception as e:
            print(f" Error: {e}")
            human_delay(5, 10)

    return all_urls

def collect_urls(page, query, max_pages):
    urls, use_bing = collect_urls_google(page, query, max_pages)
    if use_bing:
        extra = collect_urls_bing(page, query, max_pages)
        seen  = set(urls)
        for u in extra:
            if u not in seen:
                urls.append(u); seen.add(u)
    print(f"\n  ✅ {len(urls)} unique LinkedIn URLs collected.")
    return urls

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROMPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def prompt_config():
    print("\n" + "="*60)
    print("  SEARCH CONFIGURATION")
    print("="*60)
    print("""
  Query examples:
    site:linkedin.com/in "doctor"      "California"  "@gmail.com"
    site:linkedin.com/in "physician"   "Texas"        "@gmail.com"
    site:linkedin.com/in "dentist"     "New York"     "@gmail.com"
    site:linkedin.com/in "surgeon"     "Florida"      "@gmail.com"
    site:linkedin.com/in "therapist"   "Illinois"     "@gmail.com"
""")
    q = input("  Enter query (ENTER = California doctor default): ").strip()
    if not q:
        q = 'site:linkedin.com/in "doctor" "California" "@gmail.com"'

    pages = input("  Google pages to scrape (default 5): ").strip()
    try:    pages = int(pages)
    except: pages = 5

    gonly = input("  Save ONLY Gmail profiles? (Y/n): ").strip().lower()
    require_gmail = (gonly != "n")

    resume = input("  Resume previous run? (y/N): ").strip().lower()
    do_resume = (resume == "y")

    out = f"linkedin_results_{TIMESTAMP}.csv"
    return q, pages, out, require_gmail, do_resume

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    print("\n" + "="*60)
    print("  LinkedIn Gmail Scraper  —  v3 Anti-CAPTCHA Edition")
    print("="*60)
    print("""
  [1] First-time setup  (log in to LinkedIn + Google, save session)
  [2] Run scraper
  [3] Clear resume progress  (start fresh next run)
  [4] Exit
""")
    choice = input("  Choice: ").strip()

    if choice == "1":
        setup_session()
        print("\n  ✅ Setup done. Run the script again and choose [2].\n")
        return

    if choice == "3":
        if Path(PROGRESS_FILE).exists():
            os.remove(PROGRESS_FILE)
            print("\n  ✅ Progress cleared.\n")
        else:
            print("\n  Nothing to clear.\n")
        return

    if choice == "4":
        print("\n  Bye!\n"); return

    if choice != "2":
        print("\n  Invalid choice.\n"); return main()

    # ── Check profile exists ──────────────────────────────────────────────────
    if not PROFILE_DIR.exists():
        print("\n  ❌ No browser profile found.")
        print("  Run option [1] first to set up your session.\n")
        return

    query, max_pages, out_file, require_gmail, do_resume = prompt_config()
    url_file = f"linkedin_urls_{TIMESTAMP}.txt"

    # ── Load resume progress ──────────────────────────────────────────────────
    done_urls = load_progress() if do_resume else set()
    if done_urls:
        print(f"\n  📂 Resuming: {len(done_urls)} URLs already done — will skip them.\n")

    # ── CSV setup ─────────────────────────────────────────────────────────────
    fieldnames = ["Full Name","Headline","About","Website","Gmail","Other Email","LinkedIn URL"]
    csv_out    = open(out_file, "w", newline="", encoding="utf-8")
    writer     = csv.DictWriter(csv_out, fieldnames=fieldnames)
    writer.writeheader()

    saved = skipped = 0

    with sync_playwright() as pw:
        ctx  = launch_browser(pw)
        page = ctx.new_page()
        page.evaluate(STEALTH_JS)

        # ── Confirm LinkedIn session ──────────────────────────────────────────
        if not check_linkedin_session(page):
            ctx.close(); csv_out.close(); return

        # ── PHASE 1: Collect URLs ─────────────────────────────────────────────
        print("  PHASE 1 — Collecting LinkedIn URLs…")
        urls = collect_urls(page, query, max_pages)

        if not urls:
            print("\n  No URLs found. Try a different query.")
            ctx.close(); csv_out.close(); return

        # Filter already-done
        fresh_urls = [u for u in urls if u not in done_urls]
        print(f"  {len(fresh_urls)} new URLs to scrape"
              f" ({len(urls)-len(fresh_urls)} skipped as already done).")

        with open(url_file, "w") as f:
            f.write("\n".join(urls))
        print(f"  ✅ Full URL list → {url_file}")

        # ── PHASE 2: Scrape profiles ──────────────────────────────────────────
        print(f"\n  PHASE 2 — Scraping {len(fresh_urls)} profiles…")
        label = "(Gmail only)" if require_gmail else "(all profiles)"
        print(f"  Filter: {label}\n")

        for i, url in enumerate(fresh_urls, 1):
            print(f"  [{i:>4}/{len(fresh_urls)}] {url}")

            result = scrape_profile(page, url, require_gmail=require_gmail)

            # Mark as done regardless of result (avoid re-scraping on resume)
            done_urls.add(url)
            save_progress(done_urls)

            if result:
                writer.writerow(result)
                csv_out.flush()
                saved += 1
                print(f"         ✉  Gmail  : {result['Gmail'] or '—'}")
                print(f"         📧 Other  : {result['Other Email'] or '—'}")
                print(f"         👤 Name   : {result['Full Name']}")
                print(f"         🏷  Title  : {result['Headline'][:65]}")
            else:
                skipped += 1
                msg = "No Gmail — skipped" if require_gmail else "No data"
                print(f"         ⚠  {msg}")

            print()

            # Adaptive pacing
            if i % 5 == 0:
                long_pause(12, 25)
            elif i % 2 == 0:
                human_delay(4, 9)
            else:
                human_delay(2.5, 6)

        ctx.close()

    csv_out.close()

    print("\n" + "="*60)
    print("  ✅  ALL DONE")
    print("="*60)
    print(f"  URL list      → {url_file}")
    print(f"  Results CSV   → {out_file}")
    print(f"  Saved         : {saved}")
    print(f"  Skipped       : {skipped}")
    print(f"  Progress file → {PROGRESS_FILE}  (for resume)")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()