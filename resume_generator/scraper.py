"""Playwright-based job scraper for LinkedIn, XING, and StepStone.

Uses stealth evasions to avoid bot detection on LinkedIn.
"""

import os
import re
import time
import random
import json
import requests
from pathlib import Path
from typing import List

from resume_generator.job_models import JobListing

# ─── Dotenv ─────────────────────────────────────────────────────────────────

def _load_dotenv():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and k not in os.environ:
                os.environ[k] = v

_load_dotenv()

# Session cookie cache (avoid re-login)
_COOKIES_DIR = Path(__file__).parent.parent / ".cookies"
_COOKIES_DIR.mkdir(exist_ok=True)


def _random_delay(min_ms=300, max_ms=1500):
    time.sleep(random.uniform(min_ms, max_ms) / 1000)


def _hours_to_linkedin_filter(hours: int) -> str:
    if hours <= 24:
        return "r86400"
    elif hours <= 168:
        return "r604800"
    else:
        return "r2592000"


def _create_stealth_context(browser):
    """Create a browser context with anti-detection measures."""
    ctx = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="Europe/Berlin",
        geolocation={"latitude": 49.45, "longitude": 11.08},
        permissions=["geolocation"],
        color_scheme="light",
    )
    # Apply stealth patches
    try:
        from playwright_stealth import Stealth
        stealth = Stealth()
        # Stealth will be applied per-page later
    except ImportError:
        pass
    return ctx


def _apply_stealth(page):
    """Apply stealth evasions to a page."""
    # Hide webdriver
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        window.chrome = { runtime: {} };
    """)
    try:
        from playwright_stealth import Stealth
        Stealth().apply_stealth(page)
    except Exception:
        pass


def _human_type(page, selector: str, text: str):
    """Type like a human with random delays between keystrokes."""
    page.click(selector)
    page.fill(selector, "")  # Clear first
    for char in text:
        page.type(selector, char, delay=random.randint(30, 100))


def _save_cookies(ctx, name: str):
    """Persist cookies to disk."""
    cookies = ctx.cookies()
    path = _COOKIES_DIR / f"{name}.json"
    path.write_text(json.dumps(cookies), encoding="utf-8")


def _load_cookies(ctx, name: str) -> bool:
    """Load cookies from disk. Returns True if cookies were loaded."""
    path = _COOKIES_DIR / f"{name}.json"
    if not path.is_file():
        return False
    try:
        cookies = json.loads(path.read_text(encoding="utf-8"))
        # Only use cookies less than 12 hours old
        ctx.add_cookies(cookies)
        return True
    except Exception:
        return False


# ─── LinkedIn ───────────────────────────────────────────────────────────────

def _scrape_linkedin(job_title: str, location: str, hours: int, max_jobs: int) -> List[JobListing]:
    """Scrape LinkedIn Jobs with stealth evasions."""
    from playwright.sync_api import sync_playwright

    email = os.environ.get("LINKEDIN_EMAIL", "")
    password = os.environ.get("LINKEDIN_PASSWORD", "")

    jobs = []
    with sync_playwright() as p:
        # Use headed mode if we need to log in fresh
        needs_login = bool(email and password) and not _COOKIES_DIR.joinpath("linkedin.json").is_file()
        browser = p.chromium.launch(
            headless=not needs_login,  # Show browser only when logging in
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        ctx = _create_stealth_context(browser)
        page = ctx.new_page()
        _apply_stealth(page)

        try:
            # ── Try cookie-based session ──
            if _load_cookies(ctx, "linkedin"):
                page.goto("https://www.linkedin.com/feed/", timeout=20000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                _random_delay(1000, 2000)
                # Check if we're still logged in
                current_url = page.url
                if "login" in current_url or "checkpoint" in current_url:
                    # Session expired, need fresh login
                    pass
                else:
                    print("[LinkedIn] Using cached session.")

            # ── Login if needed ──
            if email and password:
                page.goto("https://www.linkedin.com/login", timeout=30000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                _random_delay(1000, 2000)

                current_url = page.url
                if "login" in current_url or "checkpoint" in current_url:
                    # Actually need to log in
                    # Try multiple selectors (LinkedIn changes these)
                    username_sel = None
                    for sel in ["#username", "#session_key", 'input[name="session_key"]',
                                'input[autocomplete="username"]', 'input[type="text"]']:
                        if page.query_selector(sel):
                            username_sel = sel
                            break
                    if not username_sel:
                        print("[LinkedIn] Could not find username field. Login page structure changed.")
                        print(f"[LinkedIn] Page URL: {page.url}")
                        browser.close()
                        return jobs

                    password_sel = None
                    for sel in ["#password", "#session_password", 'input[name="session_password"]',
                                'input[autocomplete="current-password"]', 'input[type="password"]']:
                        if page.query_selector(sel):
                            password_sel = sel
                            break

                    _human_type(page, username_sel, email)
                    _random_delay(500, 1000)
                    if password_sel:
                        _human_type(page, password_sel, password)
                    _random_delay(500, 1000)

                    # Try multiple submit selectors
                    submitted = False
                    for btn_sel in ['button[type="submit"]', 'button[data-litms-control-urn="login-submit"]',
                                    'button.sign-in-form__submit-btn', 'button:has-text("Sign in")',
                                    'button:has-text("Sign In")']:
                        btn = page.query_selector(btn_sel)
                        if btn:
                            btn.click()
                            submitted = True
                            break
                    if not submitted:
                        page.keyboard.press("Enter")

                    # Wait for login to complete
                    try:
                        page.wait_for_url("**/feed/**", timeout=15000)
                    except Exception:
                        _random_delay(3000, 5000)
                        # Check for verification page
                        if "checkpoint" in page.url or "challenge" in page.url:
                            print("[LinkedIn] Verification required — check your email/LinkedIn app.")
                            browser.close()
                            return jobs
                        # Might have succeeded — check if we're past login
                        if "login" not in page.url:
                            print("[LinkedIn] Login likely succeeded (redirected away from login).")

                    _random_delay(2000, 4000)
                    _save_cookies(ctx, "linkedin")
                    print("[LinkedIn] Logged in and saved session.")

            # ── Search for jobs ──
            time_filter = _hours_to_linkedin_filter(hours)
            encoded_title = requests.utils.quote(job_title)
            encoded_loc = requests.utils.quote(location)
            search_url = (
                f"https://www.linkedin.com/jobs/search/?"
                f"keywords={encoded_title}"
                f"&location={encoded_loc}"
                f"&f_TPR={time_filter}"
                f"&f_E=2"  # Entry level
                f"&position=1&pageNum=0"
            )
            page.goto(search_url, timeout=45000)
            # Wait for either network idle OR the job list to appear
            try:
                page.wait_for_selector(".jobs-search-results-list, .jobs-search__results-list, .scaffold-layout__list, ul.jobs-search-results__list", timeout=20000)
            except Exception:
                page.wait_for_load_state("domcontentloaded", timeout=20000)
            _random_delay(3000, 5000)

            # Check if we hit a block page
            content = page.content().lower()
            if "security-check" in page.url or "unusual" in content or "verify you" in content:
                print("[LinkedIn] Blocked by security check. Try again later or use a different IP.")
                browser.close()
                return jobs

            # Check if we got an empty/no-results page
            if "no matching jobs" in content or "no results found" in content:
                print("[LinkedIn] No matching jobs found for this search.")
                browser.close()
                return jobs

            # ── Scroll to load results ──
            scroll_attempts = min(max_jobs // 5 + 1, 6)
            for _ in range(scroll_attempts):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                _random_delay(1500, 3000)
                # Click "Show more" if available
                try:
                    show_more = page.query_selector('button:has-text("Show more"), button:has-text("See more")')
                    if show_more:
                        show_more.click()
                        _random_delay(1000, 2000)
                except Exception:
                    pass

            # ── Extract job cards ──
            # LinkedIn changes class names frequently; use multiple fallback selectors
            card_selectors = [
                ".job-card-container",
                ".jobs-search-results__list-item",
                "li.jobs-search-results__list-item",
                '[data-job-id]',
                ".scaffold-layout__list-item",
            ]
            cards = []
            for sel in card_selectors:
                cards = page.query_selector_all(sel)
                if cards:
                    break

            if not cards:
                # Try getting the full page HTML to debug
                print(f"[LinkedIn] No job cards found. Page URL: {page.url}")
                print(f"[LinkedIn] Page title: {page.title()}")
                browser.close()
                return jobs

            count = 0
            for card in cards:
                if count >= max_jobs:
                    break
                try:
                    # Title selectors (in order of preference)
                    title_sel = [
                        "a.job-card-list__title",
                        ".job-card-list__title",
                        ".job-card-container__link",
                        "a[data-control-name='job_card_title']",
                        "a.job-card-container__link",
                        "h3 a",
                    ]
                    title = ""
                    link = ""
                    for tsel in title_sel:
                        el = card.query_selector(tsel)
                        if el:
                            title = el.inner_text().strip()
                            link = el.get_attribute("href") or ""
                            break

                    if not title:
                        continue

                    # Company
                    company_sel = [
                        ".job-card-container__company-name",
                        ".artdeco-entity-lockup__subtitle",
                        ".job-card-container__primary-description",
                        '[data-test-job-card-company]',
                    ]
                    company = ""
                    for csel in company_sel:
                        el = card.query_selector(csel)
                        if el:
                            company = el.inner_text().strip()
                            break

                    # Location
                    loc_sel = [
                        ".job-card-container__metadata-item",
                        ".artdeco-entity-lockup__caption",
                        "ul.job-card-container__metadata-wrapper li",
                        '[data-test-job-card-location]',
                    ]
                    loc = ""
                    for lsel in loc_sel:
                        el = card.query_selector(lsel)
                        if el:
                            loc = el.inner_text().strip()
                            break

                    # Date posted
                    date_sel = [".job-card-container__footer-job-pill", "time", ".job-search-card__listdate"]
                    date_posted = ""
                    for dsel in date_sel:
                        els = card.query_selector_all(dsel)
                        for el in els:
                            text = el.inner_text().strip()
                            if text and ("ago" in text.lower() or "day" in text.lower() or "hour" in text.lower() or "week" in text.lower() or "month" in text.lower()):
                                date_posted = text
                                break
                        if date_posted:
                            break

                    if link and not link.startswith("http"):
                        link = f"https://www.linkedin.com{link.split('?')[0]}"

                    jobs.append(JobListing(
                        title=title,
                        company=company,
                        location=loc,
                        date_posted=date_posted,
                        job_board="LinkedIn",
                        job_link=link,
                    ))
                    count += 1
                except Exception as e:
                    continue

            # ── Scrape full descriptions ──
            for i, job in enumerate(jobs):
                if not job.job_link:
                    continue
                try:
                    page.goto(job.job_link, timeout=15000)
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                    _random_delay(500, 1500)

                    desc_selectors = [
                        ".jobs-description__content",
                        ".jobs-box__html-content",
                        "#job-details",
                        ".jobs-description",
                        ".description__text",
                        "[data-test-job-description]",
                        "article",
                    ]
                    for dsel in desc_selectors:
                        el = page.query_selector(dsel)
                        if el:
                            text = el.inner_text().strip()
                            if len(text) > 100:
                                job.description = text[:3000]
                                break

                    # Respect rate limits
                    if i < len(jobs) - 1:
                        _random_delay(2000, 4000)

                except Exception:
                    continue

        finally:
            _save_cookies(ctx, "linkedin")
            browser.close()

    return jobs


# ─── StepStone ──────────────────────────────────────────────────────────────

def _scrape_stepstone(job_title: str, location: str, hours: int, max_jobs: int) -> List[JobListing]:
    """Scrape StepStone Germany."""
    from playwright.sync_api import sync_playwright

    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            search_url = (
                f"https://www.stepstone.de/jobs/{requests.utils.quote(job_title)}/"
                f"in-{requests.utils.quote(location)}"
                f"?radius=30&sort=date"
            )
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            _random_delay(2000, 4000)

            # Accept cookies
            try:
                page.click('button:has-text("Alle akzeptieren"), button:has-text("Accept all"), button:has-text("Accept")', timeout=3000)
                _random_delay()
            except Exception:
                pass

            cards = page.query_selector_all('[data-at="job-item"]')
            for card in cards[:max_jobs]:
                try:
                    title_el = card.query_selector('[data-testid="job-item-title"], h2, a[href*="/stellenangebote"]')
                    link_el = card.query_selector('a[href*="/stellenangebote"]')
                    # Company and location: get all text lines, parse them
                    full_text = card.inner_text().split('\n')
                    # Text pattern: Title, Company, Location, Description, "mehr", Time, Status
                    title = title_el.inner_text().strip() if title_el else ""
                    company = full_text[1].strip() if len(full_text) > 1 else ""
                    loc = full_text[2].strip() if len(full_text) > 2 else ""
                    # Skip if loc contains description text
                    if len(loc) > 80:
                        loc = ""
                    link = link_el.get_attribute("href") if link_el else ""
                    if link and not link.startswith("http"):
                        link = f"https://www.stepstone.de{link}"

                    if title:
                        jobs.append(JobListing(
                            title=title, company=company, location=loc,
                            job_board="StepStone", job_link=link,
                        ))
                except Exception:
                    continue

        finally:
            browser.close()

    return jobs


# ─── XING ───────────────────────────────────────────────────────────────────

def _scrape_xing(job_title: str, location: str, hours: int, max_jobs: int) -> List[JobListing]:
    """Scrape XING Jobs."""
    from playwright.sync_api import sync_playwright

    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            search_url = (
                f"https://www.xing.com/jobs/search?"
                f"keywords={requests.utils.quote(job_title)}"
                f"&location={requests.utils.quote(location)}"
            )
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            _random_delay(2000, 4000)

            cards = page.query_selector_all('[data-xds="JobCard"], .job-card, article, [data-testid="job-search-card"]')
            for card in cards[:max_jobs]:
                try:
                    title_el = card.query_selector('h2, h3, [data-testid="job-title"], a[href*="/jobs/"]')
                    company_el = card.query_selector('[data-testid="company-name"], .company-name, span')
                    location_el = card.query_selector('[data-testid="job-location"], .location')
                    link_el = card.query_selector('a[href*="/jobs/"]')

                    title = title_el.inner_text().strip() if title_el else ""
                    company = company_el.inner_text().strip() if company_el else ""
                    loc = location_el.inner_text().strip() if location_el else ""
                    link = link_el.get_attribute("href") if link_el else ""
                    if link and not link.startswith("http"):
                        link = f"https://www.xing.com{link}"

                    if title:
                        jobs.append(JobListing(
                            title=title, company=company, location=loc,
                            job_board="XING", job_link=link,
                        ))
                except Exception:
                    continue

        finally:
            browser.close()

    return jobs


# ─── Unified Interface ─────────────────────────────────────────────────────

def scrape_jobs(
    job_title: str,
    location: str,
    hours: int = 168,
    max_jobs: int = 10,
    boards: List[str] | None = None,
) -> List[JobListing]:
    """Scrape job listings from multiple boards."""
    if boards is None:
        boards = ["LinkedIn", "XING", "StepStone"]

    scrapers = {
        "LinkedIn": _scrape_linkedin,
        "XING": _scrape_xing,
        "StepStone": _scrape_stepstone,
    }

    all_jobs = []
    for board in boards:
        scraper = scrapers.get(board)
        if not scraper:
            continue
        try:
            jobs = scraper(job_title, location, hours, max_jobs)
            all_jobs.extend(jobs)
            print(f"[{board}] Found {len(jobs)} jobs.")
        except Exception as e:
            print(f"[{board}] Scraping failed: {e}")

    return all_jobs
