import unittest
from pathlib import Path
from scripts.icon_pack import load_pack, load_brand_atlas, embedded_script, validate_svg, gallery, ROOT
import tempfile

class IconPackTests(unittest.TestCase):
    def test_known_sources_bundled(self):
        pack=load_pack()
        self.assertEqual(len(pack),14)
        for key in ("telegram","x","github","ton","usdt","search","snowflake"):
            self.assertTrue(pack[key].startswith("data:image/svg+xml;base64,"))

    def test_owner_approved_brand_atlas(self):
        atlas=load_brand_atlas()
        self.assertEqual((atlas["cols"],atlas["rows"]),(6,4))
        self.assertEqual(len(atlas["positions"]),21)
        self.assertTrue(atlas["image"].startswith("data:image/webp;base64,"))
        for key in ("ludoman","gram","kito","ton","ston","dedust",
                    "tonco","jvault","getgems","gecko","gramorg",
                    "usdt","fragment","dexscreener","tonviewer","telegram","x",
                    "tonraffles","usda","rton","web"):
            self.assertIn(key,atlas["positions"])
        original=__import__("json").loads(
            (ROOT/"assets/icon-pack/approved-brand-atlas.json").read_text())
        for key in ("usda","rton","web","tonraffles"):
            self.assertIn("196",original["sources"][key])

    def test_script_safe(self):
        out=embedded_script()
        self.assertIn("window.OBSERVATORY_ICON_PACK",out)
        self.assertIn("window.OBSERVATORY_BRAND_ATLAS",out)
        self.assertNotIn("https://",out)
        self.assertNotIn("<script",out)

    def test_svg_validation(self):
        for svg in ('<svg><script></script></svg>','<svg><path onload="x"/></svg>',
                    '<svg><path href="https://bad"/></svg>'):
            with self.assertRaises(ValueError):
                validate_svg(svg)

    def test_standalone_gallery(self):
        with tempfile.TemporaryDirectory() as tmp:
            html=gallery(output=Path(tmp)/"icon-gallery.html").read_text()
            self.assertIn("TON Observatory",html)
            self.assertIn("data:image/svg+xml;base64",html)
            self.assertNotIn('src="http',html)

    def test_markup_anchor(self):
        self.assertIn("/*ICONS*/",(ROOT/"web/page.html").read_text())
        self.assertIn("window.OBSERVATORY_ICON_PACK",(ROOT/"web/app.js").read_text())
        self.assertIn("window.OBSERVATORY_BRAND_ATLAS",(ROOT/"web/app.js").read_text())
