# Mickey Handoff: Buick/GMC Executive Summary Rollup

## Objective

Generate 22 PowerPoint decks:

- 11 specified markets.
- Buick and GMC for each market.
- June-August 2026 data.
- One consolidated Executive Summary per market/brand.
- Tactics that ran in any month of the period must remain represented.
- Include the three-month YTD KBA and impressions slides.

Market codes:

`XALY`, `XATL`, `XAUG`, `XBIR`, `XCHN`, `XCLM`, `XHUN`, `XMAC`, `XMON`, `XMOB`, `XTPC`.

## What Was Changed

### 1. Date-range DAX support

`Scripts/data_queries.py:4` now accepts optional `start_month_year` and
`end_month_year` filters. The Executive Summary and tactic-discovery queries
can therefore cover the inclusive June-August period instead of one month.

`Scripts/main_slide_generator.py:356` contains the dedicated per-market rollup
generator. It creates the cover, consolidated Executive Summary, three-month
YTD slides, and glossary without generating monthly tactic slides.

### 2. Dedicated rollup interface

The monthly interface remains in `Scripts/app_ui.py`.

The rollup interface is separate in `Scripts/rollup_ui.py:13` and should be
started with:

```powershell
python -m streamlit run Scripts/rollup_ui.py
```

The user should leave the dates at June 1, 2026 and August 1, 2026, then click
`GENERATE 22 ROLLUP DECKS`. No brand, tier, or market selection is required.

### 3. Authentication reuse

`Scripts/powerbi_connector.py:31` now reuses a valid access token and tracks
its expiry. This prevents the rollup from attempting interactive login once
for every market.

### 4. Market-code matching

`Scripts/main_slide_generator.py:1750` contains `resolve_rollup_market_rows`.
It matches both exact codes and compound values such as `XALY-BU00`, grouping
those values under the requested `XALY` market.

`Scripts/data_queries.py:13` accepts a list of actual market codes and emits
an OR filter for Power BI.

### 5. Diagnostics and tests

`Scripts/test_rollup_catalog.py` is a local regression test. It creates
representative compound codes and prints all 22 expected matches.

Run it with:

```powershell
Push-Location Scripts
python -m unittest -v test_rollup_catalog
Pop-Location
```

The live Power BI diagnostic is exposed at
`Scripts/main_slide_generator.py:1890`:

```powershell
python Scripts/main_slide_generator.py --diagnose-rollup-catalog
```

It prints the actual returned columns, sample rows, brands, actual market
codes, and a line like:

```text
LIVE ROLLUP MATCHES: N of 22
```

## Current Blocker

The live run currently reports:

```text
Power BI returned no Buick/GMC rows for the configured market codes.
Returned catalog rows: 1736.
Expected codes: XALY, XATL, XAUG, XBIR, XCHN, XCLM, XHUN, XMAC, XMON, XMOB, XTPC
```

This means the catalog query returns rows, but the current brand/code matcher
finds zero target pairs. The next action is to run the live diagnostic and
inspect the actual `Brand` and `MarketCode` values. Do not guess new market
codes until that output is reviewed.

Useful checks from the diagnostic output:

- Are brand values exactly `Buick` and `GMC`, or do they use another reporting label?
- Are market codes exact, compound, or stored in another column?
- Are the target codes present under a different brand/type filter?
- Does the DAX response return aliases, table-qualified names, or unexpected fields?

## Commit History

- `ce63810` Initial repository and quarter-rollup implementation.
- `6708a82` Separate rollup UI and reuse Power BI token.
- `94a8a59` Add catalog diagnostics for zero matches.
- `6181546` Handle qualified Power BI column names.
- `0e2b792` Match compound market codes and support code lists in DAX.
- `1b46074` Add live diagnostic CLI and catalog regression test.

## Validation Already Completed

- Python compilation passes for modified modules.
- Focused regression suite passes: 8 tests.
- Local rollup catalog test prints 22 matches.
- Streamlit 1.61.1 starts the dedicated UI and responds with HTTP 200.

The live Power BI diagnostic remains the required next check because it needs
an authenticated Power BI session and the actual dataset values.