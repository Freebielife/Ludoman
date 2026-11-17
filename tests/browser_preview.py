"""Browser smoke checks for the self-contained Ludoman preview.

Requires: python -m pip install playwright; python -m playwright install chromium
Runs against the generated index.html over a temporary localhost server.
"""
from __future__ import annotations

import functools
import http.server
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "build" / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)


def main() -> None:
    assert (ROOT / "index.html").is_file(), "Run python3 build.py first"
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                for width in (360, 390, 768, 1280):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    # Block remote APIs: the embedded snapshot must be usable offline.
                    def route_request(route):
                        url = route.request.url
                        if url.startswith(f"http://127.0.0.1:{httpd.server_port}/"):
                            route.continue_()
                        else:
                            route.abort()
                    page.route("**/*", route_request)
                    page.goto(
                        f"http://127.0.0.1:{httpd.server_port}/index.html",
                        wait_until="domcontentloaded",
                        timeout=30000,
                    )
                    page.wait_for_selector("#stats .stat", timeout=15000)
                    page.wait_for_selector("#plot svg", timeout=15000)
                    for section in ("market", "activity", "wallets", "pools", "links"):
                        assert page.locator(f"#{section}").count() == 1, section
                    sizes = page.evaluate("""() => ({
                        viewport: window.innerWidth,
                        document: document.documentElement.scrollWidth,
                        body: document.body.scrollWidth
                    })""")
                    assert max(sizes["document"], sizes["body"]) <= sizes["viewport"] + 2, (
                        f"Horizontal overflow at {width}px: {sizes}"
                    )
                    assert not errors, f"JavaScript errors at {width}: {errors}"
                    # Language switch + header navigation + dynamic chart selectors.
                    page.locator("#en").click()
                    assert page.evaluate("document.documentElement.lang") == "en"
                    page.locator("#ru").click()
                    assert page.evaluate("document.documentElement.lang") == "ru"
                    page.locator("#nav a[href='#market']").click()
                    assert page.evaluate("window.location.hash") == "#market"
                    assert page.locator("#currency button").count() == 2
                    page.locator("#currency button").last.click()
                    assert not errors, f"Errors after controls at {width}: {errors}"
                    for href in page.locator("#pools .poolActions a, #links a").evaluate_all(
                        "(nodes) => nodes.map(node => node.getAttribute('href'))"
                    ):
                        assert href and (href.startswith("https://") or href.startswith("#")), href
                    page.evaluate("window.scrollTo(0, 0)")
                    page.wait_for_timeout(200)
                    page.screenshot(path=str(SCREENSHOTS / f"ludoman-{width}.png"), full_page=True)
                    print(f"PASS {width}px: layout, chart, navigation, language, links, JS")
                    page.close()
            finally:
                browser.close()
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
