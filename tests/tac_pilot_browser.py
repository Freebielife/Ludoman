"""Browser verification for the independent TAC pilot after standalone build."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "build/tac-pilot"
SCREENS = ROOT / "build/tac-pilot/screenshots"
MASTER = "EQBE_gBrU3mPI9hHjlJoR_kYyrhQgyCFD6EUWfa42W8T7EBP"
POOL = "EQCg4hnMxXk6TemtkO9jUEmbAdxj7W5vY7OVmo41h3rvZEUI"

def main():
    SCREENS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for width in (360, 390, 768, 1280):
            page = browser.new_page(viewport={"width": width, "height": 900})
            errors = []
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.route("https://raw.githubusercontent.com/**", lambda route: route.abort())
            page.route("https://api.github.com/**", lambda route: route.abort())
            page.route("https://tonapi.io/**", lambda route: route.abort())
            page.goto((SITE / "index.html").as_uri())
            page.wait_for_selector("#market #plot svg", timeout=20000)
            assert not errors, (width, errors)
            assert page.locator("#pools .knownPools .poolCard").count() == 1
            assert page.locator("#views button").count() == 3
            assert page.locator("#stats .statHeading").count() == 4
            assert page.locator('a[href="https://t.me/TACbuild"]').count() >= 1
            assert page.locator('a[href="https://x.com/TacBuild"]').count() >= 1
            assert page.locator('a[href="https://tac.build/"]').count() >= 1
            assert page.locator("body").inner_text().find("LUDOMAN") == -1
            assert MASTER in page.locator("#contractAddress").inner_text()
            assert POOL in page.locator("#pools").inner_html()
            assert page.locator("#wallets .badgeLegend dt").count() == 4
            assert page.locator('#pools .knownPools a[href*="geckoterminal.com"]').count() == 1
            assert page.locator('#pools .knownPools a[href*="app.ston.fi/pools/"]').count() == 1
            assert page.locator("#stats .statHeading").count() == 4
            assert page.locator("img[src^='https://']").count() == 0, "No remote images"
            sizes = page.evaluate("""() => ({
                doc: document.documentElement.scrollWidth,
                body: document.body.scrollWidth, viewport: innerWidth
            })""")
            assert max(sizes["doc"], sizes["body"]) <= sizes["viewport"] + 2, (width, sizes)
            page.locator("#en").click()
            assert page.evaluate("document.documentElement.lang") == "en"
            page.locator("#ru").click()
            assert page.evaluate("document.documentElement.lang") == "ru"
            page.screenshot(path=str(SCREENS / f"TAC-{width}.png"), full_page=True)
            page.close()
        browser.close()
    print("PASS: TAC offline Chromium site at 360/390/768/1280px")

if __name__ == "__main__":
    main()
