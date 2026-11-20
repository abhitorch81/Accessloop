"""Optional, read-only browser evidence collection using Playwright."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class PageEvidence:
    url: str
    title: str
    controls: list[dict[str, str]]
    focus_order: list[dict[str, str]]
    screenshot: str | None = None


def inspect_page(url: str, *, tabs: int = 12, screenshot: str | None = None) -> PageEvidence:
    """Inspect one user-specified page without submitting forms or clicking links.

    Browser navigation may load third-party assets. Use a site you own or are
    authorized to inspect; review screenshots before sharing them.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https", "file"}:
        raise ValueError("Expected an http, https, or file URL")
    if not 1 <= tabs <= 100:
        raise ValueError("tabs must be between 1 and 100")
    if screenshot:
        path = Path(screenshot).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Install browser support with pip install 'accessloop-agent[browser]' and run playwright install chromium") from exc
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            # DOM metadata is evidence, not a complete accessibility assessment.
            controls = page.locator("button, a[href], input, select, textarea, [role='button']").evaluate_all("""nodes => nodes.slice(0, 100).map(n => ({
                tag: n.tagName.toLowerCase(),
                text: (n.innerText || n.value || '').trim().slice(0, 120),
                label: n.getAttribute('aria-label') || '',
                id: n.id || ''
            }))""")
            focus = []
            for _ in range(tabs):
                page.keyboard.press("Tab")
                focus.append(page.evaluate("""() => ({
                    tag: document.activeElement?.tagName?.toLowerCase() || '',
                    text: (document.activeElement?.innerText || document.activeElement?.value || '').trim().slice(0, 120),
                    label: document.activeElement?.getAttribute('aria-label') || '',
                    id: document.activeElement?.id || ''
                })"""))
            if screenshot:
                page.screenshot(path=str(path), full_page=True)
            return PageEvidence(page.url, page.title(), controls, focus, str(path) if screenshot else None)
        finally:
            browser.close()
