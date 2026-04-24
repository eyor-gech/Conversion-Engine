from __future__ import annotations

import json
import urllib.parse
import urllib.robotparser
from pathlib import Path
from typing import Any

from core.cache import get_cache

_USER_AGENT = "ConversionEngineBot/1.0"


def _robots_allows(url: str) -> bool:
    """Return True if robots.txt permits fetching *url* for our user-agent."""
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        # If robots.txt is unreachable assume allowed (fail-open, conservative)
        return True
    return rp.can_fetch(_USER_AGENT, url)


def load_job_snapshot(path: Path) -> dict[str, int]:
    cache = get_cache()
    key = cache.make_key("load_job_snapshot", "structured", {"path": str(path)})
    cached = cache.get(key)
    if cached is not None:
        return {str(k): int(v) for k, v in cached.items()}

    data = json.loads(path.read_text(encoding="utf-8"))
    cache.set(key, data)
    return {str(k): int(v) for k, v in data.items()}


async def scrape_public_job_posts(url: str) -> dict[str, Any]:
    """
    Clean public scraping only.
    No login flows and no captcha bypass.
    Checks robots.txt before fetching; skips if disallowed.
    """
    cache = get_cache()
    key = cache.make_key("scrape_public_job_posts", "playwright_v2", {"url": url})
    cached = cache.get(key)
    if cached is not None:
        return dict(cached)

    if not _robots_allows(url):
        result = {"url": url, "titles": [], "note": "robots_txt_disallowed"}
        cache.set(key, result)
        return result

    try:
        from playwright.async_api import async_playwright
    except Exception:
        result = {"url": url, "titles": [], "note": "playwright_unavailable"}
        cache.set(key, result)
        return result

    titles: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(extra_http_headers={"User-Agent": _USER_AGENT})
        await page.goto(url, wait_until="domcontentloaded")
        elements = await page.locator("h1, h2, h3, [data-job-title]").all_inner_texts()
        titles = [t.strip() for t in elements if t.strip()][:40]
        await browser.close()

    result = {"url": url, "titles": titles}
    cache.set(key, result)
    return result
