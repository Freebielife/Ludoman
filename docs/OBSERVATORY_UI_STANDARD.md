# Observatory UI Standard — v1.0 (prototype)

This document records the reusable design and interaction rules validated in **Ludoman Observatory**. It does not claim that token-specific on-chain collectors or pool/contract addresses have already been generalized. KITO is outside this work.

## Non-negotiable rules

- **One standalone `index.html`** with embedded CSS, JS, snapshot, and artwork. No external runtime fonts, CSS frameworks, icon CDNs, or UI dependencies.
- **RU/EN** interface, mobile-first, keyboard-usable controls, all links clickable and correct, no page-wide horizontal scrolling at 360, 390, 768, or 1280 px.
- Never alter on-chain integer values or trade matching for presentation. Render token quantities, GRAM, USD, market cap, volume, stakes, locks, and percentages to **one fractional digit** using the locale. Nonzero absolute values that would otherwise display zero use `<0,1` / `<0.1`. Exact dates, hashes, addresses, domain IDs, ranks, discrete counts, and exchange fee parameters remain intact and do not acquire misleading decimals.
- Only display a service name or its emoji when its wallet-role identification comes from the verified identity data; do not infer identity from transaction patterns alone.

## Operations

- Separate transaction cards with adequate padding, vertical rhythm, and legible mobile text. The **LUDOMAN amount and GRAM amount are opposite each other**, at equal font weight and comparable prominence. The token name is a subordinate label.
- Wallet address or name gets its own row. **Only a four-digit `.ton` domain badge appears beside the wallet name**; OG, +888, project NFTs, JVault, burned-token badges, etc. appear below in a wrapping badge area.
- Green buy and red sell styling; **animated fire / amber-red-gold color flow across the whole burn card**; reduce or disable animation when `prefers-reduced-motion` is enabled.
- Collapsible **Filter** below the operation-type tabs: text search across available badge names, multi-select badge criteria (logical AND), existing minimum GRAM/domain controls, and Reset. All badge sources are configured by the project and must use the same ownership verification rules as the displayed badges.
- **Exactly 10 most recent matching transactions** are shown initially; one arrow-marked button below the feed reveals the remaining matching entries (up to the 50 loaded by the existing feed) and can collapse them again.
- Each transaction is already a complete card: **date and time only once in the top header**, with **no per-card expand/collapse button** and no repeated details. A lower-right **«Транзакция» / “Transaction”** hyperlink opens that transaction on gram.org directly.
- No chart technical readout, chart refresh details, or capitalization methodology paragraph below the chart.

## Rankings

- **Diamond Hands 💎:** top 10 holders only. A shimmering multicolour precious-stones frame and gemstone ornament, without compromising text legibility.
- **Paper Hands 🧻:** top 10 sellers **in the 7-day and 30-day views only**. Animated frame, with repeated semi-transparent toilet-roll ornament across the card background. No Paper Hands in the 24-hour sellers view.
- Both rank labels are **visual honors, not additional blockchain claims**. Other verified project/NFT badges remain visible.

## Banner and global interface

- Keep token-specific logo, name, and short description in a responsive hero. Primary button links to the market graph; secondary links to the project Telegram (project-specific URL). No clipping or overlap on narrow mobile screens.
- Reserve modest, reusable emoji for stable section headings and navigation: 📈 Market, 🔄 Operations, 🏆 Rankings, 💧 Pools, 🔒 Locks/Staking, 🔗 Links. Translate labels to RU and EN; never hardcode LUDOMAN text into the eventual shared UI framework.
- Keep market snapshot, pools, staking and locks update architecture independent of CSS/markup; avoid introducing additional remote requests or display-only dependencies.

## Before marking future projects as supported

Replace hard-coded LUDOMAN/GRAM symbols, master contract, art, URLs, all wallet badge source definitions and upstream collector parameters with **validated project configuration**. Check trading pair addresses, frozen and staked amounts, badge ownership and update cadence before deployment. Current Ludoman is a reference implementation, not yet that configurable generator.

## Validation checklist

- Run `node --test tests/*.test.cjs`, `python3 -m unittest discover -s tests -p 'test_*.py'`, `python3 build.py`, and `python3 verify.py`.
- Chromium smoke test at 360 / 390 / 768 / 1280 px. Verify language switch, graph, navigation, filter/search/reset, seller periods, holder ranks, links, JS errors, mobile overflow and readable animations.
- Check generated `index.html` embeds all images/JS/CSS and data without unresolved template tokens or external framework assets.


## Ludoman interface refinement — 19 Nov 2026

- Operation cards stay compact: time in the header, token/GRAM amounts side by side, wallet and a simple "Транзакция" / "Transaction" hyperlink in the same footer row. No per-card chevrons, no arrows beside that hyperlink, no repeated timestamps. Buy and sell headings include small animated upward/downward chart marks; the full line remains visible when reduced motion is requested.
- Six navigation links: Market, Operations, Rankings, Liquidity (goes to #pools), Locks/Staking (goes to #supply), Links. On 360–390px viewports use a 3-by-2 grid with all six labels visible.
- Diamond Hands holders: moving multicolour border, gemstone motif, animated gemstone lettering on wallet/domain and honor label. Known service accounts (snapshot.identity.byWallet[wallet].role) also receive a gear, not inferred guesses.
- Liquidity pool cards have distinct dark accents: DeDust yellow, STON.fi blue, Tonco green; mixed providers use a neutral mixture. This is a visual rule and does not imply a Tonco pool exists when no verified pool is in the snapshot.
- Frozen balances (❄️) and staking (🔒) appear below Operations and Rankings, with an **estimated** USD value only when both a valid LUDOMAN/GRAM market quote and GRAM/USD rate exist. No exchange price or amount is invented when missing.
- Social links, DEX links and token pair labels receive embedded vector/monogram or existing local token-art marks. All runtime assets remain self-contained.
- Counts of actual swap events, seller transactions, holders and burns are **exact integers**. They can legitimately be odd. Never change an on-chain event count solely to make a visually even number, as this would misrepresent the data. For paired sub-events, only display even totals if confirmed from independently verified on-chain transfers, with clear labels and an explicit method.
- Section backgrounds gradually lighten top-to-bottom in the same dark palette. Desktop 1280px, tablet 768px and mobile 390px/360px are regression-tested in Chromium, including navigation labels, links, filters, currencies and overflow.
