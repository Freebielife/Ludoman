"""Embed the snapshot, artwork, styles and scripts in the upload-ready HTML."""
import base64
import json
from pathlib import Path

root = Path(__file__).resolve().parent
data = root / "data/snapshot.json"
snapshot = json.loads(data.read_text())
web = root / "web"
template = (web / "page.html").read_text()
for marker, filename in (
    ("/*LOADER*/", "snapshot-loader.js"), ("/*MARKET_CAP*/", "market-cap.js"),
    ("/*STYLE*/", "style.css"), ("/*APP*/", "app.js"),
):
    template = template.replace(marker, (web / filename).read_text())
art = base64.b64encode((web / "ludoman.webp").read_bytes()).decode("ascii")
template = template.replace("__LUDOMAN_ART__", "data:image/webp;base64," + art)
for key in ("staking", "vnuk", "joystick", "phoenix", "blue"):
    icon = base64.b64encode((root / "web" / f"badge-{key}.webp").read_bytes()).decode("ascii")
    template = template.replace(f"__BADGE_{key.upper()}__", "data:image/webp;base64," + icon)
backdrop = base64.b64encode((web / "observatory-bg.webp").read_bytes()).decode("ascii")
template = template.replace("__OBSERVATORY_BG__", "data:image/webp;base64," + backdrop)
embedded = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).replace("<", r"\u003c")
(root / "index.html").write_text(template.replace("__SNAPSHOT__", embedded))
