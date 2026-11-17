"""Non-invasive checks for the standalone visual design layer."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DesignLayerTests(unittest.TestCase):
    def test_standalone_build_embeds_visual_layer(self):
        build = (ROOT / "build.py").read_text()
        self.assertIn('"telegram-taste.css"', build)
        self.assertIn('filename == "style.css"', build)
        self.assertIn('template.replace("__SNAPSHOT__", embedded)', build)

    def test_mobile_dark_theme_and_badges(self):
        css = (ROOT / "web" / "telegram-taste.css").read_text()
        for width in (800, 590, 360):
            with self.subTest(width=width):
                self.assertIn(f"max-width:{width}px", css)
        self.assertIn("color-scheme:dark", css)
        self.assertIn(".projectBadge.fragmentNumber", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertNotIn("@import", css)
        self.assertNotIn("fonts.googleapis.com", css)


if __name__ == "__main__":
    unittest.main()
