"""Generate a clean TON observatory using Ludoman's reusable visual framework.

Fail-closed: only verified native TON pools, no copied Ludoman artwork,
NFT badges, locks, staking, external links or service wallet mappings.
"""
from __future__ import annotations

import argparse
import ast
import base64
import binascii
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DEXES = {"stonfi": ("STON.fi", "ston", "https://app.ston.fi"),
         "dedust": ("DeDust", "dedust", "https://dedust.io")}
CORE = ("assets.py", "trades.py", "pools.py", "collect.py", "domains.py",
        "verify.py", "web/app.js", "web/page.html", "web/style.css",
        "web/telegram-taste.css", "web/market-cap.js", "web/snapshot-loader.js",
        "scripts/icon_pack.py", "scripts/publish_snapshot.py",
        "tests/market-cap.test.cjs", "tests/snapshot-loader.test.cjs")
COMMON_SVGS = ("brands/telegram.svg", "brands/ton.svg", "brands/usdt.svg",
               "brands/github.svg", "brands/x.svg",
               "ui/arrow-left-right.svg", "ui/chart-no-axes-combined.svg",
               "ui/external-link.svg", "ui/list-filter.svg", "ui/lock.svg",
               "ui/search.svg", "ui/settings.svg", "ui/snowflake.svg",
               "ui/trophy.svg")


class ProjectError(ValueError):
    pass


def raw_address(address):
    """Decode TON-friendly basechain address with CRC-16 verification."""
    if not isinstance(address, str) or len(address) != 48:
        raise ProjectError("Expected a 48-character friendly TON address")
    try:
        data = base64.urlsafe_b64decode(address)
    except (ValueError, binascii.Error) as exc:
        raise ProjectError("Invalid TON address encoding") from exc
    if len(data) != 36 or (data[0] & 63) not in (0x11, 0x51):
        raise ProjectError("Invalid TON address tag")
    if binascii.crc_hqx(data[:34], 0) != int.from_bytes(data[34:], "big"):
        raise ProjectError("Invalid TON address checksum")
    chain = int.from_bytes(data[1:2], "big", signed=True)
    if chain != 0:
        raise ProjectError("Only TON basechain jettons are supported")
    return f"{chain}:{data[2:34].hex()}"


def require(data, key, typ=str):
    value = data.get(key)
    if not isinstance(value, typ) or (isinstance(value, str) and not value.strip()):
        raise ProjectError("Invalid or missing field: " + key)
    return value


def read_config(path):
    cfg = json.loads(path.read_text())
    slug, symbol, name = (require(cfg, k) for k in ("slug", "symbol", "name"))
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,30}", slug):
        raise ProjectError("Invalid slug")
    if not re.fullmatch(r"[A-Z0-9_]{2,12}", symbol):
        raise ProjectError("Token symbol must use ASCII capitals, digits or underscores")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 -]{0,45}", name):
        raise ProjectError("Name may not contain markup")
    raw_address(require(cfg, "master"))
    decimals = cfg.get("decimals")
    if type(decimals) is not int or not 0 <= decimals <= 18:
        raise ProjectError("Token decimals must be independently verified (0..18)")
    github = require(cfg, "github", dict)
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", require(github, "owner")):
        raise ProjectError("Invalid GitHub owner")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", require(github, "repo")):
        raise ProjectError("Invalid repository name")
    pools = require(cfg, "pools", list)
    if not 1 <= len(pools) <= 20:
        raise ProjectError("One or more confirmed native TON pools are required")
    addresses = set()
    for pool in pools:
        if not isinstance(pool, dict):
            raise ProjectError("Invalid pool definition")
        address = require(pool, "address")
        raw_address(address)
        if address in addresses:
            raise ProjectError("Duplicate pool")
        addresses.add(address)
        if pool.get("dex") not in DEXES or pool.get("quote") != "TON":
            raise ProjectError("Only direct native TON pools on STON.fi or DeDust are supported")
        if "fee" in pool and not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?%", str(pool["fee"])):
            raise ProjectError("Pool fee must be a verified percentage")
    if require(cfg, "primary_pool") not in addresses:
        raise ProjectError("Primary pool must be among the confirmed pool addresses")
    if cfg.get("quote", "TON") != "TON":
        raise ProjectError("Only native TON quote is supported by this collector")
    links = cfg.get("links", {})
    if not isinstance(links, dict) or set(links) - {"website", "telegram", "x"}:
        raise ProjectError("Unsupported link keys")
    for key, url in links.items():
        if not isinstance(url, str) or not re.fullmatch(r"https://[A-Za-z0-9.-]+(?::[0-9]+)?(?:/[^ \r\n\t<>]*)?", url):
            raise ProjectError("Invalid HTTPS link: " + key)
    services = cfg.get("services", {})
    if not isinstance(services, dict):
        raise ProjectError("services must be an address-to-name dictionary")
    cfg["_services"] = {raw_address(address): require({"name": title}, "name")
                        for address, title in services.items()}
    if cfg.get("logo_file"):
        logo = (path.parent / cfg["logo_file"]).resolve()
        if not logo.is_file() or logo.suffix.lower() != ".webp" or logo.stat().st_size > 150000:
            raise ProjectError("logo_file must be a local WebP smaller than 150 KB")
        cfg["_logo"] = logo
    return cfg


def replace(source, old, new, label):
    if old not in source:
        raise ProjectError("Ludoman reference changed: " + label)
    return source.replace(old, new)


def generic(source, cfg):
    return (source.replace("__LUDOMAN_ART__", "__PROJECT_ART__")
            .replace("__OBSERVATORY_BG__", "__PROJECT_BG__")
            .replace("LUDOMAN", cfg["symbol"])
            .replace("Ludoman", cfg["name"])
            .replace("ludoman", "project")
            .replace("GRAM", "TON"))


def schema(source):
    source = source.replace('"project":', '"tokenAmount":')
    source = source.replace('["project"]', '["tokenAmount"]')
    return re.sub(r"\.project\b", ".tokenAmount", source)


def helper(source, name):
    tree = ast.parse(source)
    node = next((x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == name), None)
    if node is None:
        raise ProjectError("Helper missing from reference: " + name)
    return "\n".join(source.splitlines()[node.lineno-1:node.end_lineno]) + "\n"


def common_badges(source):
    methods = [helper(source, n) for n in
               ("raw_friendly", "decode_address", "fragment_number_owner",
                "refresh_fragment_numbers")]
    return ('''"""Reusable TON/DNS/Fragment badges. No project-specific NFT sources."""
import base64
import binascii
import re
import time
from assets import fetch, raw_address
from domains import pages, owned, check_queue

ZERO = "0:" + "0" * 64
FRAGMENT_NUMBERS = "0:0e41dc1dc3c9067ed24248580e12b3359818d83dee0304fabcf80845eafafdb2"

def refresh(previous, now):
    return {"sources": {}, "failed": []}
''' + "\n\n".join(methods))


def common_observatory(source, cfg):
    methods = [helper(source, n) for n in
               ("hash_hex", "to_zero", "zero_burns", "activation", "identity")]
    head = '''"""Zero-address burns and identified TON accounts. No staking assumptions."""
import base64
import time
from urllib.parse import urlencode
from assets import DOMAIN, MASTER, MASTER_RAW, fetch, raw_address, resolved_domain, token_amount
from domains import DIGITS
from badges import ZERO

TONCENTER = "https://toncenter.com/api/v3"
ROLES = {"dedust_vault":"DeDust Vault","stonfi_router_v2":"STON.fi Router V2",
         "stonfi_router_v1":"STON.fi Router V1","dedust_pool":"DeDust Pool",
         "stonfi_pool_v2":"STON.fi Pool V2","stonfi_pool_v1":"STON.fi Pool V1"}
RECOVERABLE = (OSError, ValueError, KeyError, RuntimeError)
'''
    head += "\nKNOWN_SERVICES = " + repr(cfg["_services"]) + "\n"
    head += '''def role(wallet, account):
    if wallet in KNOWN_SERVICES:
        return KNOWN_SERVICES[wallet]
    return next((ROLES[i] for i in account.get("interfaces", []) if i in ROLES), None)
'''
    return schema(generic(head + "\n\n".join(methods), cfg))


def artwork(cfg):
    name = html.escape(cfg["symbol"][:3])
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">'
           '<defs><linearGradient id="g"><stop stop-color="#277cd2"/>'
           '<stop offset="1" stop-color="#142a4e"/></linearGradient></defs>'
           '<rect width="128" height="128" rx="32" fill="url(#g)"/>'
           '<text x="64" y="72" text-anchor="middle" font-size="36" '
           'font-family="system-ui" font-weight="800" fill="#e7f5ff">'
           + name + '</text></svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def page_html(source, cfg):
    symbol = html.escape(cfg["symbol"])
    first = next(p for p in cfg["pools"] if p["address"] == cfg["primary_pool"])
    venue, venue_logo, _ = DEXES[first["dex"]]
    venues = list(dict.fromkeys(p["dex"] for p in cfg["pools"]))
    tag = ' / '.join('<span class="brandInline" data-brand="' + DEXES[dex][1] + '">' +
                     DEXES[dex][0] + '</span>' for dex in venues)
    cap = ('<div class="eyebrow marketChain"><span class="brandInline" data-brand="' +
           venue_logo + '">' + venue + '</span><span>/</span>' +
           '<span class="brandInline" data-brand="project">' + symbol + '</span> · ' +
           '<span class="brandInline" data-brand="ton">TON</span></div>')
    source, count = re.subn(r'<div class="eyebrow marketChain">.*?</div>',
                            lambda _: cap, source, count=1)
    if count != 1:
        raise ProjectError("Missing market brand heading")
    source, count = re.subn(r'<span class="tag dexTag">.*?</span></span>',
                            lambda _: '<span class="tag dexTag">' + tag + '</span>',
                            source, count=1)
    if count != 1:
        raise ProjectError("Missing operation-DEX heading")
    guide = ('<details class="badgeLegend"><summary><span aria-hidden="true">ⓘ </span>'
             '<span data-t="badgeLegend"></span></summary><dl>'
             '<dt>OG</dt><dd data-t="badgeOg"></dd>'
             '<dt>+888</dt><dd data-t="badgeFragment"></dd>'
             '<dt>0000.ton</dt><dd data-t="badgeDigits"></dd>'
             '<dt>🔥</dt><dd data-t="badgeBurn"></dd></dl></details>')
    source, count = re.subn(r'<details class="badgeLegend">.*?</details>',
                            lambda _: guide, source, count=1, flags=re.S)
    if count != 1:
        raise ProjectError("Cannot isolate foreign-project badge guide")
    cards = []
    for pool in cfg["pools"]:
        address = pool["address"]
        dexname, _, base = DEXES[pool["dex"]]
        swap = (base + "/swap?ft=" + quote(cfg["master"]) + "&tt=TON"
                if pool["dex"] == "stonfi" else base + "/swap/" + quote(cfg["master"]) + "/TON")
        actions = (
            '<a href="' + html.escape(swap, quote=True) +
            '"><span lang="ru">Обмен</span><span lang="en">Swap</span></a>' +
            '<a href="' + base + '/pools/' + address +
            '"><span lang="ru">Пул</span><span lang="en">Pool</span></a>' +
            '<a href="https://www.geckoterminal.com/ton/pools/' + address +
            '"><span lang="ru">Аналитика</span><span lang="en">Analytics</span></a>' +
            '<a href="https://gram.org/address/' + address +
            '"><span lang="ru">Контракт</span><span lang="en">Contract</span></a>')
        fee = " · " + html.escape(str(pool["fee"])) + " fee" if pool.get("fee") else ""
        cards.append('<article class="poolCard"><h3>' + symbol +
                     ' / TON</h3><p>' + dexname + fee +
                     '</p><div class="poolActions">' + actions + '</div></article>')
    pool_html = ('<section id="pools" class="panel resources" aria-labelledby="pools-title">'
                 '<h2 id="pools-title"><span lang="ru">🔁 Торговые пулы</span>'
                 '<span lang="en">🔁 Trading pools</span></h2>'
                 '<p class="poolIntro"><span lang="ru">Проверенные прямые пулы.</span>'
                 '<span lang="en">Verified direct pools.</span></p>'
                 '<div class="poolGrid knownPools">' + "".join(cards) + '</div>'
                 '<div class="poolGrid" id="discoveredPools" hidden></div>'
                 '<p class="poolSources" id="poolChecked"></p></section>')
    source, count = re.subn(r'<section id="pools" .*?</section>',
                            lambda _: pool_html, source, count=1, flags=re.S)
    if count != 1:
        raise ProjectError("Cannot isolate project pool directory")
    supply = ('<section id="supply" class="panel resources supplyPanel">'
              '<h2 data-t="supplyTitle"></h2>'
              '<p class="note" lang="ru">Источники заморозки и стейкинга не подключены.</p>'
              '<p class="note" lang="en">No verified lock or staking sources configured.</p>'
              '<div class="supplyGrid">'
              '<div><span data-t="supplyFrozen"></span><strong id="frozenTotal">—</strong>'
              '<small id="frozenUsd">—</small></div>'
              '<div><span data-t="supplyStaked"></span><strong id="stakingTotal">—</strong>'
              '<small id="stakingUsd">—</small></div></div></section>')
    source, count = re.subn(r'<section id="supply" .*?</section>',
                            lambda _: supply, source, count=1, flags=re.S)
    if count != 1:
        raise ProjectError("Cannot isolate project staking/lock integrations")
    resources = []
    for key, label in (("website", cfg["name"]), ("telegram", "Telegram"), ("x", "X")):
        if key in cfg.get("links", {}):
            resources.append('<a href="' + html.escape(cfg["links"][key], quote=True) +
                             '" target="_blank" rel="noopener noreferrer">' +
                             html.escape(label) + '</a>')
    gh = "https://github.com/" + cfg["github"]["owner"] + "/" + cfg["github"]["repo"]
    resources.append('<a href="' + html.escape(gh, quote=True) + '">GitHub</a>')
    links_html = ('<section id="links" class="panel resources"><h2 data-t="links"></h2>'
                  '<div class="resourcesGrid"><article><h3 data-t="projectResources"></h3>'
                  '<div class="resourceList">' + "".join(resources) + '</div></article>'
                  '<article><h3 data-t="contractLabel"></h3>'
                  '<p class="contract" id="contractAddress"></p><div class="resourceList">'
                  '<a id="contract" data-t="exploreContract"></a><button id="copy"></button>'
                  '</div></article></div></section>')
    source, count = re.subn(r'<section id="links" .*?</section>',
                            lambda _: links_html, source, count=1, flags=re.S)
    if count != 1:
        raise ProjectError("Cannot isolate project social links")
    source, count = re.subn(
        r'<template id="badge-icon-arni">.*?</template>(?:<template .*?</template>)*',
        "", source, count=1, flags=re.S)
    if count != 1:
        raise ProjectError("Cannot remove project-specific badge images")
    return source


def app_js(source, cfg):
    source = replace(source,
                     'const MASTER="EQDbKihXMZuNfl7m7VcNrHIyYYYgCFPhccIqNN_ocNn-PBCb";',
                     'const MASTER=' + json.dumps(cfg["master"]) + ';', "master in UI")
    source, n = re.subn(r'const authorCollection="[^"]+";', 'const authorCollection="";',
                        source, count=1)
    if n != 1:
        raise ProjectError("Cannot remove NFT collection")
    source, n = re.subn(r'const projectBadgeDefs=\[.*?\];', 'const projectBadgeDefs=[];',
                        source, count=1, flags=re.S)
    if n != 1:
        raise ProjectError("Cannot remove project badges")
    source, n = re.subn(r'const badgeFilterDefs=\[.*?\];',
                        'const badgeFilterDefs=[["og","OG"],["fragmentNumber","+888"],'
                        '["digits","0000.ton"],["burner","🔥 Burn"]];',
                        source, count=1, flags=re.S)
    if n != 1:
        raise ProjectError("Cannot remove project badge filters")
    source = replace(source, 'const brandLabels={project:"L"',
                     'const brandLabels={project:' + json.dumps(cfg["symbol"][0]),
                     "project brand fallback")
    precision = str(cfg["decimals"])
    source = replace(source, r'!/^\d{0,9}$/.test(fraction)',
                     '!/^\\d{0,' + precision + '}$/.test(fraction)',
                     "token fractional precision")
    source = replace(source, '10n**9n', '10n**' + precision + 'n',
                     "integer token base units")
    source = replace(source, 'padEnd(9,"0")', 'padEnd(' + precision + ',"0")',
                     "fraction padding")
    source = replace(source,
                     'function volumeBars(start,end,width,left,right){\n const main=$("tradeVolume");',
                     'function volumeBars(start,end,width,left,right){\n const main=$("tradeVolume");\n'
                     ' if(!snapshot.trades){\n'
                     '   $("volumeBuys").textContent=t("buys")+" · —";\n'
                     '   $("volumeSells").textContent=t("sells")+" · —";\n'
                     '   $("volumeEmpty").hidden=false;\n'
                     '   $("volumeEmpty").textContent=t("no");\n'
                     '   main.replaceChildren();\n'
                     '   return;\n'
                     ' }\n',
                     "avoid fake zero volume before first snapshot")
    source = replace(source, 'const axisTime=seconds=>new Date(seconds*1000).toLocaleString',
                     'const axisTime=seconds=>Number.isFinite(seconds)?new Date(seconds*1000).toLocaleString',
                     "avoid invalid dates before initial snapshot")
    source = replace(source, ":{day:'numeric',month:'short',year:'2-digit'});",
                     ":{day:'numeric',month:'short',year:'2-digit'}):'—';",
                     "empty snapshot chart axis")
    return source


def python_sources(cfg, dest):
    file = dest / "assets.py"
    source = file.read_text()
    source = replace(source, 'MASTER = "EQDbKihXMZuNfl7m7VcNrHIyYYYgCFPhccIqNN_ocNn-PBCb"',
                     'MASTER = ' + repr(cfg["master"]), "token address")
    source = replace(source,
                     'MASTER_RAW = "0:db2a2857319b8d7e5ee6ed570dac72326186200853e171c22a34dfe870d9fe3c"',
                     'MASTER_RAW = ' + repr(raw_address(cfg["master"])), "raw address")
    source = replace(source, 'HOLDER_LIMIT = 100',
                     'DECIMALS = ' + str(cfg["decimals"]) + '\nHOLDER_LIMIT = 100',
                     "token precision")
    token_amount = '''def token_amount(units):
    if not re.fullmatch(r"[0-9]+", str(units)):
        raise ValueError("Invalid base-unit quantity")
    whole, fraction = divmod(int(units), 10 ** DECIMALS)
    return str(whole) if DECIMALS == 0 else (f"{whole}.{fraction:0{DECIMALS}d}").rstrip("0").rstrip(".")

def native_amount(units):
    if not re.fullmatch(r"[0-9]+", str(units)):
        raise ValueError("Invalid native TON quantity")
    whole, fraction = divmod(int(units), 10**9)
    return (f"{whole}.{fraction:09d}").rstrip("0").rstrip(".")

def resolved_domain'''
    source, n = re.subn(r'def token_amount\(units\):.*?\n\ndef resolved_domain',
                        lambda _: token_amount, source, count=1, flags=re.S)
    if n != 1:
        raise ProjectError("Missing token amount conversion")
    source = replace(source, 'int(metadata["decimals"]) != 9',
                     'int(metadata["decimals"]) != DECIMALS', "on-chain decimal validation")
    file.write_text(source)
    file = dest / "trades.py"
    source = file.read_text()
    pools = {pool["address"]: (pool["dex"], DEXES[pool["dex"]][0])
             for pool in cfg["pools"]}
    fields = 'PRIMARY = ' + repr(cfg["primary_pool"]) + '\nPOOLS = ' + repr(pools)
    source, n = re.subn(r'PRIMARY = .*?\nPOOLS = \{.*?\n\}',
                        lambda _: fields, source, count=1, flags=re.S)
    if n != 1:
        raise ProjectError("Missing legacy pool registry")
    source = replace(source, 'fetch, raw_address, token_amount',
                     'fetch, raw_address, token_amount, native_amount', "TON amount helper")
    source = replace(source,
                     'jetton, gram = token_amount(jetton), token_amount(gram)',
                     'jetton, gram = token_amount(jetton), native_amount(gram)',
                     "native TON amount is always nine decimals")
    file.write_text(source)
    file = dest / "collect.py"
    source = replace(file.read_text(),
                     '(("pools", pools.collect), ("vesting", observatory.vesting), ("staking", observatory.staking))',
                     '(("pools", pools.collect),)', "disable foreign staking integrations")
    file.write_text(source)


def build_py(cfg):
    return '''"""Bundle a configured, independent observatory into one HTML file."""
import base64
import json
from pathlib import Path
from scripts.icon_pack import embedded_script

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
template = (WEB / "page.html").read_text()
for marker, filename in (
    ("/*LOADER*/", "snapshot-loader.js"),
    ("/*MARKET_CAP*/", "market-cap.js"),
    ("/*STYLE*/", "style.css"),
    ("/*APP*/", "app.js"),
):
    content = (WEB / filename).read_text()
    if filename == "style.css":
        content += "\\n" + (WEB / "telegram-taste.css").read_text()
    template = template.replace(marker, content)
template = template.replace("/*ICONS*/", embedded_script())
if (WEB / "project-logo.webp").exists():
    art = "data:image/webp;base64," + base64.b64encode((WEB / "project-logo.webp").read_bytes()).decode("ascii")
else:
    art = ''' + repr(artwork(cfg)) + '''
background = "data:image/svg+xml;base64," + base64.b64encode(
    b'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120">'
    b'<rect width="120" height="120" fill="#090e18"/>'
    b'<path d="M0 0L120 120M120 0L0 120" stroke="#25415a" stroke-opacity=".3"/>'
    b'</svg>').decode("ascii")
template = template.replace("__PROJECT_ART__", art).replace("__PROJECT_BG__", background)
snapshot = json.loads((ROOT / "data/snapshot.json").read_text())
payload = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).replace("<", r"\\u003c")
result = template.replace("__SNAPSHOT__", payload)
if any(x in result for x in ("/*APP*/", "/*STYLE*/", "/*LOADER*/", "/*MARKET_CAP*/",
                             "__PROJECT_ART__", "__PROJECT_BG__", "__BADGE_")):
    raise ValueError("Unresolved template marker")
(ROOT / "index.html").write_text(result)
'''


def workflow():
    return '''name: Update TON observatory
on:
  workflow_dispatch:
  push:
    branches: [main]
    paths:
      - '*.py'
      - 'web/**'
      - 'scripts/**'
      - 'tests/**'
      - 'project.json'
      - '.github/workflows/update.yml'
permissions:
  contents: write
concurrency:
  group: observatory-data
  cancel-in-progress: false
jobs:
  refresh:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v4
        with:
          ref: main
          fetch-depth: 20
      - name: Validate engine
        run: |
          node --check web/app.js
          node --test tests/*.test.cjs
      - name: Collect on-chain data
        id: collect
        continue-on-error: true
        run: python3 collect.py
      - name: Build and publish verified snapshot
        run: |
          python3 build.py
          python3 verify.py
          python3 scripts/publish_snapshot.py
      - name: Report partial collection
        if: steps.collect.outcome == 'failure'
        run: exit 1
'''


def scaffold(config_path, output):
    cfg = read_config(config_path)
    if output.exists() and any(output.iterdir()):
        raise ProjectError("Target directory must be empty")
    if output.resolve() == ROOT.resolve() or ROOT.resolve().is_relative_to(output.resolve()):
        raise ProjectError("Refusing to overwrite the original Ludoman repository")
    output.mkdir(parents=True, exist_ok=True)
    for relative in CORE:
        src = ROOT / relative
        if not src.is_file():
            raise ProjectError("Missing reference: " + relative)
        dest = output / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        value = src.read_text()
        if relative == "web/snapshot-loader.js":
            value = replace(value, "Freebielife/Ludoman",
                            cfg["github"]["owner"] + "/" + cfg["github"]["repo"],
                            "GitHub snapshot URL")
        value = generic(value, cfg)
        if relative in ("assets.py", "trades.py", "collect.py", "verify.py",
                        "web/app.js", "web/market-cap.js",
                        "tests/market-cap.test.cjs"):
            value = schema(value)
        if relative == "tests/market-cap.test.cjs":
            value = replace(value, "project:String(project)",
                            "tokenAmount:String(project)", "generic market-cap fixture")
        if relative == "web/app.js":
            value = app_js(value, cfg)
        if relative == "web/telegram-taste.css":
            value += ('\nhtml[lang="ru"] #supply [lang="en"], '
                      'html[lang="en"] #supply [lang="ru"]{display:none!important}\n')
        if relative == "pools.py":
            value = value.replace('"TON (TON)"', '"TON"')
        elif relative == "web/page.html":
            value = page_html(value, cfg)
        elif relative == "web/market-cap.js":
            first = next(p for p in cfg["pools"] if p["address"] == cfg["primary_pool"])
            value = replace(value, 'r.dex==="STON.fi"',
                            'r.dex===' + json.dumps(DEXES[first["dex"]][0]),
                            "source DEX for market chart")
        elif relative == "scripts/icon_pack.py":
            value = replace(
                value, '    data=json.loads((root/"approved-brand-atlas.json").read_text())',
                '    if not (root/"approved-brand-atlas.json").exists():\n'
                '        return {"image":"","cols":0,"rows":0,"positions":{}}\n'
                '    data=json.loads((root/"approved-brand-atlas.json").read_text())',
                "isolated brand atlas")
        dest.write_text(value)
    pack = output / "assets/icon-pack"
    for relative in COMMON_SVGS:
        dest = pack / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "assets/icon-pack" / relative, dest)
    manifest = json.loads((ROOT / "assets/icon-pack/manifest.json").read_text())
    manifest["assets"] = [x for x in manifest["assets"] if x["file"] in COMMON_SVGS]
    manifest["pending"] = []
    (pack / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    (output / "badges.py").write_text(common_badges((ROOT / "badges.py").read_text()))
    (output / "observatory.py").write_text(common_observatory(
        (ROOT / "observatory.py").read_text(), cfg))
    python_sources(cfg, output)
    (output / "build.py").write_text(build_py(cfg))
    (output / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (output / ".github/workflows/update.yml").write_text(workflow())
    (output / "data").mkdir()
    (output / "data/snapshot.json").write_text(json.dumps({
        "schema": 1, "token": cfg["master"], "updated": 1,
        "errors": ["holders", "trades", "burns", "domains", "rates"]}))
    (output / "project.json").write_text(json.dumps({
        k: v for k, v in cfg.items() if not k.startswith("_")
    }, ensure_ascii=False, indent=2))
    if cfg.get("_logo"):
        shutil.copy2(cfg["_logo"], output / "web/project-logo.webp")
    (output / ".gitignore").write_text("build/\n__pycache__/\n*.pyc\n")
    (output / "README.md").write_text(
        "# " + cfg["name"] + " Observatory\n\n"
        "Generated from a reusable TON UI, without Ludoman assets or references.\n\n"
        "Run python3 collect.py; python3 build.py; python3 verify.py.\n"
        "Publish index.html in TON Sites only after independent on-chain verification.\n"
        "The initial snapshot is EMPTY: no market data is claimed.\n"
        "Only native TON swap pairs supported. Locks, staking and custom project NFT "
        "badges must be implemented as separately verified adapters.\n"
        "Configure your GitHub workflow scheduler before launch.\n")
    banned = ("EQDbKihXMZuNfl7m7VcNrHIyYYYgCFPhccIqNN_ocNn-PBCb",
              "the1000ludoman", "1000ludoman.xyz", "CryptoCheck",
              "mRvnukICHlife", "joystickpro", "PHXPW", "TonArnold",
              "NAPIWASofficial", "__BADGE_")
    for relative in ("web/page.html", "web/app.js", "web/market-cap.js",
                     "web/style.css", "web/telegram-taste.css",
                     "assets.py", "trades.py", "observatory.py", "badges.py"):
        text = (output / relative).read_text()
        if any(x.lower() in text.lower() for x in banned):
            raise ProjectError("Foreign-project reference survived: " + relative)
    if set(p.name for p in (output / "web").glob("*.webp")) - {"project-logo.webp"}:
        raise ProjectError("Foreign token artwork survived the build")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a project-isolated TON Observatory")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    options = parser.parse_args(argv)
    try:
        target = scaffold(options.config, options.output)
    except (ProjectError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print("Created isolated observatory: " + str(target))
    print("Validate on-chain pools, then collect verified data before publishing.")


if __name__ == "__main__":
    main()
