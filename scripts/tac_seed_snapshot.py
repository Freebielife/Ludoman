"""Stage real TAC on-chain data without waiting for full historical burn scanning.

Writes each fully verified source atomically, retaining good data if a later
fetch fails or the runner reaches its deadline. No invented on-chain rows.
"""
import importlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "build/tac-pilot"
DATA = SITE / "data/snapshot.json"
sys.path.insert(0, str(SITE))

assets = importlib.import_module("assets")
trades = importlib.import_module("trades")
pools = importlib.import_module("pools")

def atomic_save(value):
    temporary = DATA.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False))
    os.replace(temporary, DATA)

def main():
    snapshot = json.loads(DATA.read_text())
    now = int(time.time())
    errors = set(snapshot.get("errors", []))
    # Historic burns, zero-address burns, wallet role labels and ownership badges
    # are unavailable until explicitly indexed. Keep their status partial.
    errors.update(("burns", "zeroBurns", "identity", "domains", "badges"))
    snapshot["updated"] = now
    snapshot["token"] = assets.MASTER
    snapshot["errors"] = sorted(errors)
    atomic_save(snapshot)

    def stage(name, collector):
        nonlocal snapshot
        print("Fetching", name, flush=True)
        try:
            item = collector()
            if not isinstance(item, dict):
                raise ValueError("Data source returned unexpected shape")
            snapshot[name] = item
            errors.discard(name)
            snapshot["updated"] = int(time.time())
            snapshot["errors"] = sorted(errors)
            atomic_save(snapshot)
            print(name, "SAVED", len(item.get("rows", item.get("holders", []))), flush=True)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
            print(name, "UNAVAILABLE", type(error).__name__, str(error)[:220], flush=True)

    stage("holders", lambda: {**assets.holders(), "asOf": now})
    stage("trades", lambda: trades.collect({}, now - 7 * 86400, now, max_pages=35))
    stage("rates", lambda: {"asOf": now, "rows": trades.rates()})
    stage("pools", lambda: pools.collect(now))
    print("Verified sections:", [k for k in ("holders","trades","rates","pools") if k in snapshot], flush=True)
    print("Incomplete sections:", snapshot["errors"], flush=True)

if __name__ == "__main__":
    main()
