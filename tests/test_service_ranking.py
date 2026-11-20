"""Regression coverage for service-only ranks and official DEX navigation."""
import unittest
from pathlib import Path

from assets import HOLDER_LIMIT
from observatory import KNOWN_SERVICES, role

ROOT = Path(__file__).resolve().parents[1]


class ServiceAndNavigationTests(unittest.TestCase):
    def test_crypto_check_is_explicitly_named(self):
        address = "0:2d7075bcc5a3baceff8d869f9c466be6f0ee699700859811ad9da68f6aacc89a"
        self.assertEqual(KNOWN_SERVICES.get(address), "CryptoCheck")
        self.assertEqual(role(address, {"interfaces": []}), "CryptoCheck")
        self.assertIsNone(role("0:" + "f" * 64, {"interfaces": []}))

    def test_sample_supports_twenty_human_holders_after_filtering(self):
        self.assertGreaterEqual(HOLDER_LIMIT, 100)
        js = (ROOT / "web" / "app.js").read_text()
        self.assertIn('const views=["holders","sellers","services"]', js)
        self.assertIn('rankedSellers(source).filter(r=>!serviceRole(r.wallet))', js)
        self.assertIn('Boolean(serviceRole(r.wallet))===isService', js)
        self.assertNotIn("Paper Hands", js)

    def test_pool_navigation_differentiates_dex_from_analytics(self):
        html = (ROOT / "web" / "page.html").read_text()
        for url in ("https://app.ston.fi/pools/", "https://dedust.io/pools/",
                    "https://www.geckoterminal.com/ton/pools/"):
            self.assertIn(url, html)
        self.assertIn('data-brand="ton"', html)
        self.assertIn('data-brand="gram"', html)


if __name__ == "__main__":
    unittest.main()
