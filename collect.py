"""Build a static LUDOMAN snapshot. Each source keeps its last good result on failure."""
import json
import sys
import time
from pathlib import Path

import assets
import domains
import trades

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "snapshot.json"
YEAR = 366 * 86400


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False))
    temporary.replace(path)


def refresh():
    now = int(time.time())
    snapshot = json.loads(DATA.read_text()) if DATA.exists() else {"schema": 1, "token": assets.MASTER}
    errors = []
    for key in ("holders", "burns", "trades"):
        try:
            old = snapshot.get(key, {})
            if key == "holders":
                result = assets.holders()
                if not result.get("holders") or not result.get("totalSupply"):
                    raise ValueError("missing token balances")
                section = {**result, "asOf": now}
            elif key == "trades":
                cutoff = now - YEAR
                previous = old if old.get("since", cutoff) <= cutoff else {}
                section = trades.collect(previous, cutoff, now)
            else:
                cutoff = now - YEAR
                previous = old if old.get("since", cutoff) <= cutoff else {}
                start_at = max(cutoff, previous.get("asOf", cutoff) - 3600)
                rows, start = assets.burns(previous.get("rows", []), start_at)
                start = max(cutoff, min(start, previous.get("since", start)))
                section = {"rows": [r for r in rows if r["time"] >= cutoff], "since": start, "asOf": now}
            snapshot[key] = section
            print(key, "OK", len(section.get("rows", section.get("holders", []))), flush=True)
        except Exception as error:
            errors.append(key)
            print(key, "FAILED:", error, file=sys.stderr, flush=True)
    core_updated = len(errors) < 3
    if core_updated:
        try:
            snapshot["domains"] = domains.enrich(snapshot, now)
        except Exception as error:
            errors.append("domains")
            print("domains FAILED:", error, file=sys.stderr, flush=True)
        try:
            snapshot["rates"] = {"asOf": now, "rows": trades.rates()}
        except Exception as error:
            errors.append("rates")
            print("rates FAILED:", error, file=sys.stderr, flush=True)
        snapshot.update(schema=1, token=assets.MASTER, updated=now, errors=errors)
        DATA.parent.mkdir(exist_ok=True)
        save(DATA, snapshot)
    return bool(errors)


if __name__ == "__main__":
    sys.exit(refresh())
