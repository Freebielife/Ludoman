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
                    for section in ("market", "activity", "wallets", "pools", "supply", "links"):
                        assert page.locator(f"#{section}").count() == 1, section
                    sizes = page.evaluate("""() => ({
                        viewport: window.innerWidth,
                        document: document.documentElement.scrollWidth,
                        body: document.body.scrollWidth
                    })""")
                    assert max(sizes["document"], sizes["body"]) <= sizes["viewport"] + 2, (
                        f"Horizontal overflow at {width}px: {sizes}"
                    )
                    assert page.locator("#nav a").count() == 6
                    assert page.locator("#nav a[href='#pools']").count() == 1
                    assert page.locator("#nav a[href='#supply']").count() == 1
                    assert page.locator("#supply").evaluate("(el) => el.offsetTop") > page.locator("#wallets").evaluate("(el) => el.offsetTop")
                    assert page.locator("#supply .supplyUsd").count() == 2
                    assert page.locator("#pools .poolCard.dex-ston").count() >= 1
                    assert page.locator("#pools .poolCard.dex-dedust").count() >= 1
                    assert page.locator("#pools .poolCard .brandGlyph").count() >= 2
                    assert page.locator("#links a.brandedLink .brandGlyph").count() >= 4
                    assert page.evaluate("Boolean(window.OBSERVATORY_ICON_PACK?.telegram && window.OBSERVATORY_ICON_PACK?.github)")
                    # Approved emoji imagery is a self-contained, color WebP sprite.
                    assert page.evaluate("Boolean(window.OBSERVATORY_BRAND_ATLAS?.positions?.gram)")
                    assert page.locator('.introLinks a[href*="t.me"] .brandGlyph .brandTile').count() == 1
                    assert page.locator('#links .brandGlyph .brandTile').count() >= 4
                    assert page.locator('.brand .brandMark .brandTile').count() == 1
                    assert page.locator('#pools .poolCard .dexMarks .brandTile').count() >= 2
                    assert page.locator('#supply .brandGlyph .brandTile').count() == 2
                    assert page.locator('#links .brandGlyph img').count() >= 1
                    assert page.evaluate("""async () => {
                      const picture = new Image();
                      picture.src = window.OBSERVATORY_BRAND_ATLAS.image;
                      await picture.decode();
                      return picture.naturalWidth === 240 && picture.naturalHeight === 160;
                    }""")
                    page.wait_for_function("""() => [...document.querySelectorAll('.brandGlyph img')]
                        .every(n => n.complete && n.naturalWidth > 0)""", timeout=10000)
                    assert page.locator('.brandGlyph img').evaluate_all(
                        "(nodes) => nodes.every(n => n.src.startsWith('data:image/svg+xml;base64,'))"
                    )
                    assert not errors, f"JavaScript errors at {width}: {errors}"
                    # The chart stays visible, but user-facing technical diagnostics are gone.
                    assert page.locator("#readout, #chartInfo, .capMethod").count() == 0
                    assert page.locator("#feed .operationRow .opAmounts").count() > 0
                    assert page.locator("#feed .operationRow .opAmountValue").count() >= 2
                    # Show exactly ten recent transactions initially; expand/collapse via one footer control.
                    total = page.evaluate("(snapshot.trades?.rows?.length ?? 0) + burnRows().length")
                    initial_count = min(10, total)
                    assert page.locator("#feed .operationRow").count() == initial_count
                    assert page.locator("#feed .operationRow .opToggle, #feed .operationRow .opMobile").count() == 0
                    cards_ok = page.locator("#feed .operationRow").evaluate_all(
                        """nodes => nodes.every(card =>
                            card.querySelectorAll('.opHeader time').length === 1 &&
                            card.querySelectorAll('.opDate').length === 1 &&
                            card.querySelectorAll('.opTransaction').length === 1 &&
                            card.querySelector('.opTransaction').textContent.trim() === 'Транзакция' &&
                            card.querySelector('.opTransaction').href.startsWith('https://gram.org/tx/')
                        )"""
                    )
                    assert cards_ok, f"Transaction-card structure or link incorrect at {width}px"
                    assert page.locator("#feed .operationRow .opFooter .opWallet").count() == initial_count
                    assert page.locator("#feed .operationRow .opFooter .opTransaction").count() == initial_count
                    assert page.locator("#feed .operationRow .opTransaction").first.evaluate(
                        "(a) => getComputedStyle(a, '::after').content"
                    ) in ("none", "normal", '""')
                    assert page.locator("#feed .operationRow.trade-buy .trendMini").count() > 0
                    assert page.locator("#feed .operationRow.trade-sell .trendMini").count() > 0
                    if width == 390:
                        page.locator("#activity").scroll_into_view_if_needed()
                        page.screenshot(path=str(SCREENSHOTS / "ludoman-operations-390.png"))
                    if total > 10:
                        assert page.locator("#more").is_visible()
                        assert page.locator("#more").get_attribute("aria-expanded") == "false"
                        page.locator("#more").click()
                        assert page.locator("#feed .operationRow").count() == min(total, 50)
                        assert page.locator("#more").get_attribute("aria-expanded") == "true"
                        page.locator("#more").click()
                        assert page.locator("#feed .operationRow").count() == 10
                    else:
                        assert page.locator("#more").is_hidden()
                    assert page.locator("#badgeFilterPanel").is_hidden()
                    page.locator("#badgeFilterToggle").click()
                    assert page.locator("#badgeFilterPanel").is_visible()
                    assert page.locator("#badgeFilterList input").count() >= 12
                    page.locator("#badgeFilterSearch").fill("888")
                    assert page.locator("#badgeFilterList input").count() == 1
                    page.locator("#badgeFilterList input").check()
                    assert page.locator("#badgeFilterCount").inner_text() == "(1)"
                    page.locator("#clearBadgeFilters").click()
                    assert page.locator("#badgeFilterCount").inner_text() == ""
                    page.locator("#badgeFilterToggle").click()
                    assert page.locator("#badgeFilterPanel").is_hidden()
                    if width == 390:
                        page.locator("#badgeFilterToggle").click()
                        page.locator("#activity").scroll_into_view_if_needed()
                        page.screenshot(path=str(SCREENSHOTS / "ludoman-filters-390.png"))
                        page.locator("#badgeFilterToggle").click()
                    # Only 7- and 30-day top sellers receive Paper Hands.
                    page.locator("#views button").nth(1).click()
                    page.locator("#sellerPeriods button").nth(0).click()
                    assert page.locator("#rank .paperHands").count() == 0
                    page.locator("#sellerPeriods button").nth(1).click()
                    assert page.locator("#rank .paperHands").count() == min(10, page.locator("#rank .rankingRow").count())
                    if width == 390:
                        page.locator("#wallets").scroll_into_view_if_needed()
                        page.screenshot(path=str(SCREENSHOTS / "ludoman-paper-hands-390.png"))
                    page.locator("#sellerPeriods button").nth(2).click()
                    assert page.locator("#rank .paperHands").count() == min(10, page.locator("#rank .rankingRow").count())
                    page.locator("#views button").nth(0).click()
                    assert page.locator("#rank .diamondHands").count() == min(10, page.locator("#rank .rankingRow").count())
                    assert page.locator("#rank .paperHands").count() == 0
                    if page.locator("#rank .diamondHands").count():
                        assert page.locator("#rank .diamondHands .walletAddress").first.evaluate(
                            "(el) => getComputedStyle(el).backgroundImage"
                        ) != "none"
                    # Locale-aware decimal formatting; monetary value always has one place.
                    example = page.evaluate("format(156643.9396)")
                    assert example.endswith(",9"), example
                    assert not errors, f"Javascript errors after filter/ranking checks at {width}: {errors}"
                    # Every mobile tab must be wholly visible (not clipped offscreen).
                    nav_rects = page.locator("#nav a").evaluate_all(
                        "(nodes) => nodes.map(n => ({left:n.getBoundingClientRect().left,"
                        +"right:n.getBoundingClientRect().right}))"
                    )
                    assert all(r["left"] >= -2 and r["right"] <= width + 2 for r in nav_rects), (
                        f"Clipped navigation at {width}px: {nav_rects}"
                    )
                    # Language switch + header navigation + dynamic chart selectors.
                    page.locator("#en").click()
                    assert page.evaluate("document.documentElement.lang") == "en"
                    page.locator("#ru").click()
                    assert page.evaluate("document.documentElement.lang") == "ru"
                    page.locator("#nav a[href='#market']").click()
                    assert page.evaluate("window.location.hash") == "#market"
                    page.locator("#nav a[href='#pools']").click()
                    assert page.evaluate("window.location.hash") == "#pools"
                    page.locator("#nav a[href='#supply']").click()
                    assert page.evaluate("window.location.hash") == "#supply"
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
