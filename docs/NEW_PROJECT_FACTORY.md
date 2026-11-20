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
      "services": {}
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
   repository. Each site's localStorage language/currency keys are isolated.
6. Running this factory is a **source-code scaffold**, not a verification that
   the supplied pool address belongs to the token. Always check that relation
   against reliable on-chain data before launch.

## New project validation checklist

- Compare generated token master and metadata decimals to chain results.
- Compare both token sides and DEX type for every configured pool.
- Check the primary chart's source and trade/burn sample transactions.
- Check labels, social links and token art; no other project's branding.
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
