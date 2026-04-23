from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.cache import get_cache


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
    """
    cache = get_cache()
    key = cache.make_key("scrape_public_job_posts", "playwright", {"url": url})
    cached = cache.get(key)
    if cached is not None:
        return dict(cached)

    try:
        from playwright.async_api import async_playwright
    except Exception:
        result = {"url": url, "titles": [], "note": "playwright_unavailable"}
        cache.set(key, result)
        return result

    titles: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        elements = await page.locator("h1, h2, h3, [data-job-title]").all_inner_texts()
        titles = [t.strip() for t in elements if t.strip()][:40]
        await browser.close()

    result = {"url": url, "titles": titles}
    cache.set(key, result)
    return result
