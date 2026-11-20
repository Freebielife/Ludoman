# Observatory Factory — reusable TON sites

## What is separated

The existing Ludoman installation stays in its repository, using its exact
current assets and data. The factory creates a **new directory** from only the
shared presentation, validation and basic TON data collectors. It does not
overwrite or mutate Ludoman or KITO.

Reusable:
- the standalone offline-friendly HTML, dark responsive layout, RU/EN controls;
- market-cap line chart, 24-hour summary, trade feed, rankings, search/filter,
  OG/TON DNS/+888 common badges, burning, chart arrows and token watermarks;
- shared generic SVG icons, GitHub snapshot loader with retries and validations;
- TonAPI holders, verified native TON swap events, burn notifications,
  contract-role detection, GeckoTerminal pool discovery, CoinGecko TON/USD;
- CI workflow, snapshot verification and safe Git publication.

Project-only:
- master address, contract decimals, known trading pools, primary market source;
- token name and symbol, GitHub repository, social links and project logo;
- known service wallets (explicit addresses only);
- custom project NFT/balance/staking badges, JVault, TonRaffles and other
  contract-specific adapters. They are **not copied** into a new site.

## Create a site without manually editing source code

Prepare a JSON config outside the source directory, for example:

    {
      "slug": "exampletoken",
      "name": "Example Token",
      "symbol": "EXAMPLE",
      "master": "REPLACE_WITH_VERIFIED_FRIENDLY_TON_JETTON_MASTER",
      "decimals": 9,
      "github": {"owner": "Freebielife", "repo": "ExampleToken"},
      "primary_pool": "REPLACE_WITH_VERIFIED_PRIMARY_POOL",
      "pools": [
        {"address": "REPLACE_WITH_VERIFIED_PRIMARY_POOL",
         "dex": "stonfi", "quote": "TON"}
      ],
      "links": {
        "website": "https://example.com",
        "telegram": "https://t.me/example"
      },
      "services": {},
      "logo_file": "images/logo.webp",
      "background_file": "images/background.webp",
      "badges": [
        {
          "id": "community",
          "label": "Community",
          "description_ru": "Держатель выбранного jetton или NFT",
          "description_en": "Owns the configured jetton amount or NFT",
          "color": "#55BBDD",
          "icon_file": "images/community.gif",
          "url": "https://example.com",
          "match": "any",
          "criteria": [
            {"type": "jetton_min", "master": "REPLACE_WITH_VERIFIED_JETTON_MASTER", "min_balance": 200000},
            {"type": "nft_collection", "collection": "REPLACE_WITH_VERIFIED_NFT_COLLECTION"}
          ]
        }
      ]
    }

The above is intentionally **not executable** until the contract and pool
placeholders are replaced by independently confirmed, real addresses.

From Ludoman's checkout:

    python3 scripts/scaffold_observatory.py --config /path/to/project.json --output /path/to/new-repo
    cd /path/to/new-repo
    python3 build.py
    python3 verify.py
    node --check web/app.js
    node --test tests/*.test.cjs

Then initialize the new GitHub repository, give Actions permission to write
contents, and invoke the generated update workflow only once the jetton and pool
contracts have been independently confirmed. Run the collector to replace the
initial **empty** snapshot:

    python3 collect.py
    python3 build.py
    python3 verify.py

Only then publish the generated index.html in TON Sites (for example through
Resistance Tools). The initial placeholder deliberately shows no market numbers;
it is not a live quote.

To schedule automatic refreshes, register the new repository and workflow in the
shared Cloudflare Observatory Runner. Its deployment and GitHub credentials must
be configured separately. The generator does **not** install secrets, create
repositories, deploy Cloudflare Workers, or publish a TON Storage bag.

## Common ecosystem flags and verified wallet identities

The factory automatically embeds a **sanitized** static WebP atlas of owner-approved
TONecoFlags for ecosystem services: TON #002, Telegram #001, STON.fi #019,
DeDust #020 and other individually mapped common services. Project-specific
Ludoman, KITO, GRAM and unverified placeholder tiles are physically blanked
during generation. The original source is retained only in the Ludoman repository.
Install **Pillow** in the build environment (`pip install Pillow`) to extract
this neutral atlas; the resulting single HTML remains entirely offline.

The project token logo is always sourced from that project's own `logo_file`.
A project website gets its own token emblem by matching the **exact configured
hostname**, rather than hard-coded names like Ludoman or TAC. A quote-asset
emblem is drawn only if a trading pool identifies a verified native TON or
USDT master contract; other ticker names remain plain text to avoid false
identity claims.

For wallet classification, the generated `observatory.py` can recognize
specifically identified DeDust/STON.fi contract interfaces and independently
configured service wallet addresses. An active TON smart contract that does not
implement a wallet interface is labelled **unclassified smart contract**, not
a confirmed exchange, bridge or person. Enabling identity enrichment in the
scheduler is required for labels to appear; the program must never infer
services from unusually large balances.

The pools section does not display the previous dated GeckoTerminal audit line.
The data itself keeps its `asOf` field for checking provenance.

## Per-project theme and badges

- **Hero Telegram button:** appears only when \`links.telegram\` is configured. Its URL is copied from that project only; if Telegram is not configured, the hero has no Telegram button. The bottom links panel follows the same rule.
- **Project background:** optional \`background_file\`, a local WebP (up to 750 KB) relative to the input JSON; when absent, a generic dark geometric background is used. The image becomes base64 data inside \`index.html\`, with no runtime network dependency.
- **Logo:** optional \`logo_file\`, local WebP up to 150 KB, otherwise a neutral symbol placeholder.
- **Custom badges:** optional \`badges\` array (up to 12 entries). Each badge requires a unique ID, an on-screen label, descriptions in RU and EN, and **1–3 independently confirmed on-chain proof conditions**. Optional \`icon_file\` may be a local WebP (including an animated WebP) or GIF, up to 150 KB. Without an icon, a text fallback is displayed. Optional \`color\` is a six-digit CSS RGB color and \`url\` is a verified HTTPS detail link.
- Supported proof types are \`{"type":"jetton_min","master":"<address>","min_balance":200000}\` and \`{"type":"nft_collection","collection":"<address>"}\`. Set \`"match":"any"\` for OR across the conditions or \`"match":"all"\` for AND. The collector reads qualified wallet addresses via TonAPI, verifies the requested jetton metadata or collection ownership information, and refreshes source data no more frequently than every **six hours**. Partial or failed source checks never qualify previously unverified wallets. Wallet display suppresses proof data older than 24 hours.
- Configured badges automatically appear beside qualifying wallets, in the **Operations** filter list, and inside the bilingual expandable **Badge Guide** with their own artwork and descriptions.
- **Do not invent badge eligibility:** the generator validates address shape and proof rule structure, but the owner must independently verify each real contract address and its meaning before launch.
- **Preferences:** localStorage language and currency keys include the new token's slug and master identifier; multiple sites sharing one origin do not overwrite each other's choices.

All selected images and badge icons are bundled into the standalone HTML. The generator also copies the source art into the new project under \`web/\` and preserves their paths in the exported \`project.json\`. To change badges or images after generation, run the scaffold with the revised project JSON into a **new empty directory**; it deliberately refuses to overwrite existing projects.

## Important limits

1. Basic event collection currently supports **direct token/native TON swaps**
   on STON.fi and DeDust. The address and DEX must be verified on-chain, and
   fee percentages are shown only when supplied and verified. Other quote
   assets require additional parser support, not string substitutions.
2. The base valuation uses a primary DEX source and native TON/USD from
   CoinGecko. It is an **estimate**, not a quote obtained from an executable
   order book. The shared event model explicitly separates raw token decimals
   from TON's nine decimals.
3. Custom badges, staking/locking contracts and farming APR are token-specific
   and remain disabled until their source, meaning and amount calculation are
   independently verified. An unsupported section must not display fabricated
   totals, yields or associations.
4. The factory deliberately excludes the Ludoman image, emoji atlas, branded
   background, all project badge assets and all historical Ludoman transactions.
   New projects may supply their own local WebP through the optional logo_file
   setting; when omitted, a neutral symbol placeholder is generated.
5. The new GitHub repository must be independently authorized for its own
   Actions token/permissions. The generated snapshot loader always targets that
   repository. Each site's language/currency keys are separated by token slug and master address.
6. Running this factory is a **source-code scaffold**, not a verification that
   the supplied pool address belongs to the token. Always check that relation
   against reliable on-chain data before launch.

## New project validation checklist

- Compare generated token master and metadata decimals to chain results.
- Compare both token sides and DEX type for every configured pool.
- Check the primary chart's source and trade/burn sample transactions.
- Check labels, optional hero Telegram link, social links and token background/art; no other project's branding.
- Check each custom badge condition, artwork, on-chain proof, bilingual help and filter behavior.
- Run the Python unit tests and Node tests; build, verify, then check browser
  layout at 360, 390, 768 and 1280 px, with RU/EN switching.
- Confirm GitHub remote refresh and the first real snapshot.
- Test the exported single HTML in TON Sites before announcing the domain.

## Maintenance policy

Enhance the shared interface and factory once, rather than manually patching
new site copies. When a new token requires an unsupported blockchain adapter,
implement it behind its own verified configuration, add a regression fixture,
and never enable it in other projects automatically.

The factory is versioned inside Ludoman now; extracting a separately versioned
engine repository is possible later without disrupting the production site.
