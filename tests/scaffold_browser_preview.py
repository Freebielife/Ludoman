"""Browser smoke-test for a factory-created, unbranded TON observatory.

A synthetic CRC-correct token/pool is used; the placeholder is not live data.
"""
import base64
import binascii
import json
import shutil
import sys
from pathlib import Path
import subprocess

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.scaffold_observatory import scaffold

OUT = ROOT / "build/factory-visual-smoke"
SCREENS = ROOT / "build/screenshots"


def address(byte):
    raw = bytes([0x11, 0]) + bytes([byte]) * 32
    return base64.urlsafe_b64encode(raw + binascii.crc_hqx(raw, 0).to_bytes(2, "big")).decode()


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    cfg = {
        "slug": "neutral-test", "name": "Neutral Test", "symbol": "NEUTRAL",
        "master": address(77), "decimals": 6,
        "github": {"owner": "ExampleOrg", "repo": "NeutralTest"},
        "primary_pool": address(78),
        "pools": [
            {"address": address(78), "dex": "stonfi", "quote": "TON"},
            {"address": address(79), "dex": "dedust", "quote": "TON"}
        ],
        "links": {"website": "https://example.org"},
        "services": {}
    }
    conf = OUT / "example.json"
    conf.write_text(json.dumps(cfg))
    site = OUT / "site"
    scaffold(conf, site)
    subprocess.run([sys.executable, "build.py"], cwd=site, check=True)
    subprocess.run([sys.executable, "verify.py"], cwd=site, check=True)
    SCREENS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as browser_runner:
        browser = browser_runner.chromium.launch(headless=True)
        for width in (360, 390, 768, 1280):
            page = browser.new_page(viewport={"width": width, "height": 850}, device_scale_factor=1)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route("https://raw.githubusercontent.com/**", lambda route: route.abort())
            page.route("https://api.github.com/**", lambda route: route.abort())
            page.goto((site / "index.html").as_uri())
            page.wait_for_selector("#market #plot svg", timeout=10000)
            assert not errors, (width, errors)
            assert page.locator("#views button").count() == 3
            assert page.locator("#pools .knownPools .poolCard").count() == 2
            assert page.locator("#stats .statHeading").count() == 4
            assert page.locator("#market .marketChain .brandGlyph").count() == 3
            assert page.locator("#wallets .badgeLegend dt").count() == 4
            assert page.locator('#pools a[href^="https://dedust.io/pools/"]').count() == 1
            assert page.locator('#pools a[href^="https://app.ston.fi/pools/"]').count() == 1
            text = page.locator("body").inner_text()
            assert "LUDOMAN" not in text and "CryptoCheck" not in text
            assert "NEUTRAL" in text
            assert "TON" in text
            widths = page.evaluate("""() => ({
                doc: document.documentElement.scrollWidth,
                body: document.body.scrollWidth, viewport: window.innerWidth
            })""")
            assert max(widths["doc"], widths["body"]) <= widths["viewport"] + 2, (width, widths)
            page.locator("#views button").nth(2).click()
            assert page.locator("#sellerPeriods button").count() == 0
            page.locator("#en").click()
            assert page.evaluate("document.documentElement.lang") == "en"
            page.locator("#ru").click()
            assert page.evaluate("document.documentElement.lang") == "ru"
            assert not errors, (width, errors)
            page.screenshot(path=str(SCREENS / f"template-neutral-{width}.png"), full_page=True)
            page.close()
        browser.close()
    print("PASS: unbranded generic observatory at 360/390/768/1280px")


if __name__ == "__main__":
    main()
