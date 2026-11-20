"""Prepare offline TAC Observatory pilot with project logo from verifiable sources."""
import io
import json
import shutil
import urllib.request
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from scripts.scaffold_observatory import ROOT, scaffold

CONFIG = ROOT / "examples/tac-pilot/project.json"
OUTPUT = ROOT / "build/tac-pilot"
URLS = (
    ("user provided metadata", "https://habrastorage.org/webt/yy/ph/l-/yyphl-uznnokzbessqbrewgqo5g.png"),
    ("official TacBuild tokenlist", "https://res.cloudinary.com/dqz8o8js4/image/upload/v1752369223/Copy_of_TAC-logo-symbol-purple_xx17mf.png"),
)

def logo(dest):
    for label, url in URLS:
        try:
            request = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (TON Observatory build)", "Accept": "image/png,image/webp,image/jpeg"})
            with urllib.request.urlopen(request, timeout=16) as response:
                payload = response.read(2_000_001)
            if len(payload) > 2_000_000:
                raise ValueError("oversized remote logo")
            with Image.open(io.BytesIO(payload)) as img:
                img.load()
                if img.width > 4096 or img.height > 4096:
                    raise ValueError("oversized image")
                img = img.convert("RGBA")
                img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                for quality in (85, 70, 50):
                    img.save(dest, format="WEBP", quality=quality, method=6)
                    if dest.stat().st_size <= 150_000:
                        print("Logo embedded:", label, dest.stat().st_size, flush=True)
                        return label
                raise ValueError("oversized generated WebP")
        except (OSError, ValueError, UnidentifiedImageError) as error:
            print("Logo URL failed:", label, type(error).__name__, flush=True)
    return "neutral fallback"

def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf8"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    dest = CONFIG.parent / "tac-logo.webp"
    label = logo(dest)
    if label == "neutral fallback":
        cfg.pop("logo_file", None)
    effective = CONFIG.parent / "build-config.json"
    effective.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
    try:
        scaffold(effective, OUTPUT)
    finally:
        effective.unlink(missing_ok=True)
    audit = (
        "# TAC Observatory pilot\n\n"
        "Independent informational site, not an official TAC product.\n"
        "Jetton master: EQBE_gBrU3mPI9hHjlJoR_kYyrhQgyCFD6EUWfa42W8T7EBP\n"
        "Raw account: 0:44fe006b53798f23d8478e526847f918cab8508320850fa11459f6b8d96f13ec\n"
        "TAC master and 18 decimals: https://github.com/TacBuild/tokenlist/blob/main/src/tokens/tac.json\n"
        "Primary TAC/TON pool STON.fi V2: EQCg4hnMxXk6TemtkO9jUEmbAdxj7W5vY7OVmo41h3rvZEUI\n"
        "Pool source: https://www.geckoterminal.com/ton/pools/EQCg4hnMxXk6TemtkO9jUEmbAdxj7W5vY7OVmo41h3rvZEUI\n"
        "Larger TAC/USDT pool is outside current TON-only trade collector.\n"
        "No TAC staking or special badge contracts have been verified for this build.\n"
        "Logo source: " + label + "\n"
        "Future snapshot URL targets Freebielife/TAC-Observatory, pending creation.\n"
    )
    (OUTPUT / "TAC_SOURCE_AUDIT.md").write_text(audit)
    print("Generated", OUTPUT)

if __name__ == "__main__":
    main()
