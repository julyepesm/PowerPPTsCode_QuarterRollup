# GBC MARKET X - Practical Filter Rules Guide

## 1. Purpose

This guide explains why a tactic may show different figures across:

- Executive Summary.
- Current-month tactic slide.
- Tactic slide history.
- YTD Outcomes.
- YTD Impressions.

All data is fictional. The threshold used in the examples is `$50.00`.

```text
Aggregated cost < $50.00  = low spend
Aggregated cost >= $50.00 = passes
```

The exact value of `$50.00` passes.

## 2. Example configuration

| Control | Value |
|---|---:|
| Brand | GBC |
| Market | MARKET X |
| Report Month | June 2026 |
| Tier | LMA |
| Audience | GEN |
| Minimum Aggregated Spend | $50.00 |
| Historical Window | 6 months |
| Exclude Months Below Spend Threshold | Enabled |
| Min YTD Outcomes | 100 |
| Min YTD Impressions | 1,000 |

## 3. Master example

### 3.1 Source rows

| Raw Tactic | Strategy | Site | Audience | Cost | Impressions | Video Completes | Video Plays | KBAs |
|---|---|---|---|---:|---:|---:|---:|---:|
| FEP | Awareness | ALPHA DSP | GEN | $120.00 | 100,000 | 95,000 | 98,000 | 20 |
| FEP | Awareness | ALPHA TRADE DESK | GEN | $80.00 | 50,000 | 45,000 | 47,000 | 10 |
| FEP | Awareness | BETA | GEN | $25.00 | 20,000 | 19,000 | 20,000 | 5 |
| YouTube | Video | ALPHA | GEN | $50.00 | 60,000 | 2,000 | 2,500 | 8 |
| Display | InMarket | GAMMA | GEN | $30.00 | 40,000 | 0 | 0 | 40 |
| Display | BT | GAMMA | GEN | $19.99 | 50,000 | 0 | 0 | 60 |
| Search | Search | DELTA | GEN | $40.00 | 0 | 0 | 0 | 0 |
| Audio | Audio | ALPHA | GEN | $75.00 | 80,000 | 0 | 0 | 0 |

### 3.2 Aggregated combinations

The code normalizes the data and then groups it by:

```text
Effective Tactic + Grouped Site + Audience
```

| Combination | Aggregated Cost | Impressions | KBAs | Status |
|---|---:|---:|---:|---|
| FEP + ALPHA + GEN | $200.00 | 150,000 | 30 | Passes |
| FEP + BETA + GEN | $25.00 | 20,000 | 5 | Low spend with performance |
| YouTube + ALPHA + GEN | $50.00 | 60,000 | 8 | Passes at the boundary |
| InMarket Display + GAMMA + GEN | $49.99 | 90,000 | 100 | Low spend with performance |
| Search + DELTA + GEN | $40.00 | 0 | 0 | Low spend without performance |
| Audio + ALPHA + GEN | $75.00 | 80,000 | 0 | Passes |

## 4. Processing order

```text
1. Filter Brand, Market, Month, Tier, and Client Code
2. Normalize Tactic, Strategy, and Site
3. Group by Effective Tactic + Grouped Site + Audience
4. Sum Cost and performance metrics
5. Compare aggregated Cost against $50
6. Apply the rule for the relevant view
7. Calculate KPI and benchmark
8. Record anomalies
```

The `$50` threshold is not applied to each source row.

### Example

The FEP ALPHA rows have costs of `$120` and `$80`.

```text
$120 + $80 = $200
```

The code evaluates `$200`, not each row separately.

## 5. Normalization before filtering

### Rule 5.1 - Equivalent tactic names

| Source Name | Effective Name |
|---|---|
| Pre-roll | PreRoll |
| Preroll | PreRoll |
| OLV | PreRoll |
| Digital Video | PreRoll |
| CTV | FEP |

### Rule 5.2 - Display depends on Strategy

| Strategy | Internal Name | Display Name |
|---|---|---|
| BT, InMarket, Purchase | BT Display | InMarket Display |
| Retargeting | Retargeting Display | Retargeting Display |
| Consideration, HPA | Consideration Display | Consideration Display |
| Blank or unknown | BT Display | InMarket Display |

### Example

```text
Display + InMarket + GAMMA = $30.00
Display + BT + GAMMA       = $19.99
Total InMarket Display     = $49.99
```

Result: the combination is low spend because `$49.99 < $50.00`.

### Rule 5.3 - Equivalent sites are grouped

Example:

```text
Ampersand-Spectrum
Ampersand MSP FEP
Ampersand-GEN
```

All three may become `AMPERSAND`. If tactic and audience also match, their costs are summed before filtering.

### Rule 5.4 - Social and Meta

| Input | Result |
|---|---|
| Social Display, Meta Display, Paid Social, or a Meta/Facebook/Instagram site | Meta Display |
| Social Video or Meta Video | Meta Video |
| Pinterest or TikTok | Keeps its own tactic |

Example: a `Paid Social` row from the `Facebook Ads` site is processed as `Meta Display`; it is not combined with Pinterest.

## 6. Core rule by view

| View | Combination < $50 with performance | Combination < $50 without performance | Combination >= $50 |
|---|---|---|---|
| Executive Summary | Excludes | Excludes | Includes |
| Current tactic slide | Keeps and logs anomaly | Skips | Includes |
| Tactic history | Removes month when control is enabled | Removes month | Includes month |
| YTD | Does not use spend | Does not use spend | Does not use spend |

This table explains most deck differences.

## 7. Current-month tactic slide

### Rule 7.1 - Low spend with performance

The slide is kept and an anomaly is logged.

#### Example

FEP BETA:

```text
Aggregated Cost: $25.00
Impressions: 20,000
Video Completes: 19,000
KBAs: 5
```

Result:

- The tactic slide is generated.
- Error Summary records low spend with performance.
- Its metrics do not contribute to Executive Summary.

### Rule 7.2 - Low spend without performance

The slide is skipped.

#### Example

Search DELTA:

```text
Aggregated Cost: $40.00
Impressions: 0
KBAs: 0
Video Completes: 0
Clicks: 0
```

Result: the tactic slide is not generated.

### Rule 7.3 - Cost at the boundary

YouTube ALPHA has `$50.00`.

```text
$50.00 >= $50.00
```

Result: it passes and the slide is generated.

## 8. Tactic slide history

### Rule 8.1 - Historical window

`Historical Window (Months)` defines how many months are considered, ending with the report month.

Example for June 2026:

| UI Value | Period |
|---:|---|
| 6 | January through June 2026 |
| 3 | April through June 2026 |
| 1 | June 2026 |

### Rule 8.2 - Monthly spend filter

When `Exclude Months Below Spend Threshold` is enabled, history checks only the aggregated monthly cost.

| FEP ALPHA Month | Cost | Impressions | Result |
|---|---:|---:|---|
| January | $40.00 | 30,000 | Removed |
| February | $50.00 | 35,000 | Included |
| March | $80.00 | 45,000 | Included |
| April | $0.00 | 20,000 | Removed |
| May | $120.00 | 90,000 | Included |
| June | $200.00 | 150,000 | Included |

January and April are removed even though they have impressions. History uses cost, not performance.

When the control is disabled, those months are not removed because of spend.
## 9. Executive Summary

### Rule 9.1 - Filter combinations before building the card

For each audience, Executive Summary performs these steps:

```text
1. Group by Effective Tactic + Grouped Site + Audience
2. Exclude each combination with Cost < $50
3. Sum the surviving combinations by tactic
4. Calculate the card KPI from the surviving totals
```

Performance does not rescue a low-spend combination in this view.

### FEP example

| Combination | Cost | Impressions | Summary |
|---|---:|---:|---|
| FEP + ALPHA + GEN | $200.00 | 150,000 | Included |
| FEP + BETA + GEN | $25.00 | 20,000 | Excluded |

FEP card result:

```text
Impressions = 150,000
```

It does not show `170,000`, because BETA fails the threshold.

### Rule 9.2 - When Summary matches the tactic slide

If ALPHA is the only FEP combination that passes:

| View | Impressions |
|---|---:|
| Executive Summary - FEP | 150,000 |
| Tactic slide - FEP ALPHA | 150,000 |

The match is correct. It does not mean both views use exactly the same rule; it means only one combination survived in Summary.

### Rule 9.3 - When the figures should differ

Assume there is a second valid combination:

| Combination | Cost | Impressions |
|---|---:|---:|
| FEP + ALPHA + GEN | $200.00 | 150,000 |
| FEP + OMEGA + GEN | $60.00 | 10,000 |

Then:

| View | Impressions |
|---|---:|
| Executive Summary - FEP | 160,000 |
| Tactic slide - FEP ALPHA | 150,000 |
| Tactic slide - FEP OMEGA | 10,000 |

Summary consolidates valid sites. Each tactic slide keeps its own site.

### Rule 9.4 - One Summary slide per audience

GEN, HIS, and other audiences are not mixed in the same Summary slide. A blank audience is treated as GEN.

Example: `FEP + ALPHA + GEN` and `FEP + ALPHA + HIS` create cards in separate Summary slides.

### Rule 9.5 - Strict LMA video filter

After the spend filter, LMA removes FEP and YouTube cards whose total Video Completions is `0`.

| Tier | Tactic | Cost | Video Completes | Summary Result |
|---|---|---:|---:|---|
| LMA | FEP | $200.00 | 0 | Excluded |
| LMA | YouTube | $50.00 | 0 | Excluded |
| LMA | PreRoll | $80.00 | 0 | Special rule does not apply |
| ZONE | FEP | $200.00 | 0 | Special rule does not apply |

## 10. Video rule for tactic slides

The `Skip Video Tactics w/ 0 Completions` control checks normalized video tactics.

| Video Completes | Impressions or KBAs | Result |
|---:|---:|---|
| 0 | 0 | Skips the tactic slide |
| 0 | Greater than 0 | Keeps the tactic slide |
| Greater than 0 | Any value | Keeps the tactic slide |

### Example

FEP OMEGA has `$70` in cost, `10,000` impressions, and `0` completions. The slide is kept because it has activity.

Implementation note: the UI help text says `LMA only`, but the tactic-slide code block that applies this checkbox does not explicitly check the tier. The strict FEP/YouTube filter in Executive Summary does explicitly check LMA.

## 11. YTD: metric-based, not cost-based

YTD does not use `Minimum Aggregated Spend` or `Exclude Months Below Spend Threshold`.

### Rule 11.1 - YTD period

Only the selected year and months through the report month are included.

Example: June 2026 includes January-June 2026. It excludes December 2025 and July 2026.

### Rule 11.2 - YTD Outcomes

With `Min YTD Outcomes = 100`, outcomes from all tactics are summed by month.

| Month | FEP KBAs | Display KBAs | Total | Result |
|---|---:|---:|---:|---|
| January | 60 | 39 | 99 | Excluded |
| February | 60 | 40 | 100 | Included |

The exact boundary passes.

### Rule 11.3 - YTD Impressions

With `Min YTD Impressions = 1,000`, impressions from all vehicles are summed by month.

| Month | Vehicle A | Vehicle B | Total | Result |
|---|---:|---:|---:|---|
| March | 600 | 399 | 999 | Excluded |
| April | 700 | 300 | 1,000 | Included |

### Rule 11.4 - YTD checkbox disabled

When `Apply YTD Threshold Filter` is disabled, the `100` and `1,000` minimums are not applied. However, a month with a total of `0` is still removed.

Example: a month with `$0` in cost and `25` KBAs may appear in YTD Outcomes. A month with `$500` in cost and `0` KBAs does not appear in that chart.

## 12. Actual scope of UI controls

| Control | Executive Summary | Current Tactic | Tactic History | YTD | Actual Purpose |
|---|---|---|---|---|---|
| Minimum Aggregated Spend (USD) | Yes | Yes | Yes, when its checkbox is enabled | No | Defines the threshold; `$50` passes |
| Exclude Months Below Spend Threshold | No | No | Yes | No | Enables or disables monthly historical cost filtering |
| Historical Window (Months) | No | No | Yes | No | Defines the number of months in charts and KBA tables |
| Skip Video Tactics w/ 0 Completions | No | Yes | No | No | Skips video with no completions, impressions, or KBAs |
| Apply YTD Threshold Filter | No | No | No | Yes | Enables monthly Outcomes and Impressions minimums |
| Min YTD Outcomes | No | No | No | Yes | Minimum monthly total outcomes |
| Min YTD Impressions | No | No | No | Yes | Minimum monthly total impressions |

`Skip $0 Cost & Perf Tactics` was removed. Its function is already covered by the core spend and performance rule.
## 13. Market scope

### Rule 13.1 - Market Code takes priority

When a valid Market Code exists and is not `XXXXX`, the code uses it as the market identifier. Market Name is the fallback.

Example: `MKTX1` identifies MARKET X even when the name arrives as `MARKET X, PA`.

### Rule 13.2 - Strict and relaxed matching

| Mode | Use | Example |
|---|---|---|
| Strict | Data and tactic queries | `Market Name = MARKET X` |
| Relaxed | Initial discovery | A name containing `MARKET X` |

### Rule 13.3 - Coupled filters

Each query includes Brand, Market, Month Year when applicable, and Zone/LMA when provided.

Example: GBC data for MARKET X, June 2026, and LMA must not mix with another brand, market, month, or tier.

### Rule 13.4 - Client Code depends on tier

| Tier | Client Code |
|---|---|
| LMA | Kept as a required filter |
| ZONE | Removed so clients under the Market Code are aggregated |

## 14. Tactic slide content and order

### Rule 14.1 - Order

Main order:

```text
FEP -> PreRoll -> YouTube -> InMarket Display -> Consideration Display
-> Retargeting Display -> Meta Display -> Meta Video
-> Pinterest Display -> Pinterest Video -> TikTok -> Search -> Audio
```

Within FEP: EMRGE, MSP, then other sites. For the same tactic, GEN appears before HIS.

### Rule 14.2 - Displayed metrics

| Tactic | Main Metrics |
|---|---|
| FEP | Impressions, Video Completes, VCR |
| PreRoll | Impressions, Video Completes, VCR, Viewability |
| YouTube | Impressions, Video Completes, CPCV, YT Viewability |
| Display variants | Impressions, Total KBAs, CPA, Viewability |
| Meta Display | Impressions, Total KBAs, CPA |
| Meta Video | Impressions, Video Completes, VCR |
| Pinterest Display/Video | Impressions, Total KBAs, CPA |
| TikTok | Impressions, Video Completes, CPCV |
| Search | Impressions, Clicks, CPC |
| Audio | Impressions, Audio Completes, ACR |

### Rule 14.3 - Historical chart

| Tactic | Bars | Line |
|---|---|---|
| FEP, PreRoll, Meta Video | Video Completes | VCR |
| YouTube, TikTok | Video Completes | CPCV |
| Display variants, Meta Display, Pinterest | Conversions or KBAs | CPA |
| Search | Clicks | CPC |
| Audio | Audio Completes | ACR |

Example: the FEP slide uses Video Completes as bars and VCR as the line, only for historical months that survived the cost filter.

## 15. KPI, benchmark, and color

### Rule 15.1 - Formulas

| KPI | Formula |
|---|---|
| VCR | Video Completions / Video Plays |
| CPCV | Total Cost / Video Completions |
| CPA | Total Cost / Total Conversions |
| CPC | Total Cost / Clicks |
| ACR | Audio Completes / Audio Starts |
| Viewability | Unique Viewable Impressions / Unique Measured Impressions |
| YT Viewability | Active Viewable Impressions / Active View Measurable Impressions |

Every division with a denominator of `0` returns `0`.

### Examples

```text
FEP VCR = 140,000 / 145,000 = 96.55%
YouTube CPCV = $50 / 2,000 = $0.025
Display CPA = $200 / 100 = $2.00
Search CPC = $80 / 40 = $2.00
Audio ACR = 7,500 / 8,000 = 93.75%
```

### Rule 15.2 - Summary card KPI

| Tactic | KPI |
|---|---|
| FEP, PreRoll, Meta Video | VCR |
| YouTube, TikTok | CPCV |
| Display variants, Meta Display, Pinterest | CPA |
| Search | CPC |
| Audio | ACR |

The KPI is calculated after filtering and aggregation. KPIs from source rows are not averaged.

### Rule 15.3 - Benchmark color

| KPI Type | Green | Red |
|---|---|---|
| CPA, CPCV, CPC | Value <= benchmark | Value > benchmark |
| VCR, ACR, CTR | Value >= benchmark | Value < benchmark |

A `TBD` benchmark is neutral black; `N/A` is neutral gray. Viewability uses `>70%`, and YT Viewability uses `>90%` as fixed references.

When a benchmark changes over time, the code selects the latest version whose start date is less than or equal to the report month.

Example: with a VCR benchmark of `90%`, an FEP result of `96.55%` is green.

## 16. Anomalies

| Case | Action | Example |
|---|---|---|
| Low spend with performance | Keeps tactic slide and logs error | FEP BETA: `$25`, 20,000 impressions |
| VCR above 100% | Logs error and caps the chart at 100% | 105 completions / 100 plays |
| Another brand's vehicle in YTD | Logs error and removes the series | Vehicle Z belongs to another brand |

Error Summary is added only when at least one anomaly is detected.

## 17. Deck structure and output

### General order

```text
1. Title
2. Executive Summary, one per audience
3. Tactic slides
4. YTD KBA
5. YTD Impressions by Vehicle
6. Glossary
7. Error Summary, only when anomalies exist
```

In `summary_only` mode, tactic slides, YTD charts, and the glossary are not generated.

### File name

| Tier | Pattern |
|---|---|
| LMA | `{prefix} {Brand} {Month Year} Digital Metrics.pptx` |
| ZONE | `{market_code}-{Month Year} {Brand} Zone Reporting.pptx` |

For LMA, `prefix` uses the UI prefix first, then Client Code, then Market Code. If the file name already exists, Market Code is appended to avoid a collision.

Expected folder:

```text
Generated_Slides/{Zone|LMA}/{Brand}/{MM - MonthName}/{Region}/
```

## 18. Business change: legacy versus current behavior

| Element | Legacy Reference | Current Code |
|---|---|---|
| Spend cutoff | Cost equal to `$0` | Cost below the UI threshold |
| Value | Fixed at `$0` | Initially `$50`, configurable |
| Boundary | Any cost above `$0` passed | The exact threshold passes |
| Current tactic and history | Evaluated at the slide combination level | Keeps the same aggregated unit |
| Executive Summary | Filtered after aggregating the full tactic | Filters combinations, then consolidates the tactic |
| YTD | Metric-based filtering | Unchanged |

The current code satisfies the target rule:

```text
An aggregated combination with cost below $50 is treated as an
aggregated combination with $0 cost was treated before.
```

Source rows are not filtered individually, and spend is not applied to YTD.

### Important Summary distinction

Changing `$0` to `$50` is not the only observable difference from the legacy reference. The application point in Executive Summary was also aligned with tactic slides:

```text
Legacy reference: sum all FEP -> filter the full tactic
Current code: filter each FEP + Site + Audience -> sum the survivors
```

This alignment prevents a low-spend site from contributing impressions to Summary. It explains why FEP may match its tactic slide when only one site passes.

## 19. Diagnosing differences

When two slides do not match, check in this order:

1. Same Brand, Market, Month, Tier, Client Code, and Audience.
2. Same effective tactic after normalization.
3. Same grouped Site.
4. Aggregated cost of each combination against the threshold.
5. Whether Summary is adding more than one valid site.
6. Whether LMA removed FEP or YouTube because Video Completions is `0`.
7. Whether the comparison uses cost-filtered history or metric-filtered YTD.
8. Whether an anomaly was recorded.

### Quick FEP diagnosis

```text
Summary FEP = sum of all valid FEP sites for the audience
Tactic FEP  = one specific grouped site for the audience
```

If both show `841,116`, the result is correct when that site is the only FEP combination that passes the Summary filter. If another FEP site has cost `>= $50`, Summary should be greater than that individual tactic slide.

## 20. Code references

| Rule | File |
|---|---|
| Threshold and configuration | `Scripts/filters_manager.py` |
| UI controls | `Scripts/app_ui.py` |
| Summary combination filtering and KPI | `Scripts/measures.py` |
| Strict LMA Summary filter | `Scripts/executive_summary.py` |
| Current tactic, history, video, and YTD | `Scripts/main_slide_generator.py` |
| Display normalization | `Scripts/display_resolution.py` |
| Mappings, sites, and ordering | `Scripts/config/normalization_rules.json` |
| Tactic metrics and charts | `Scripts/tactic_config.py` |

## Executive summary

- Cost is summed by `Effective Tactic + Grouped Site + Audience`.
- Below `$50` is low spend; exactly `$50` passes.
- Executive Summary excludes every low-spend combination.
- The current tactic slide keeps low spend only when performance exists and logs the anomaly.
- History removes low-spend months when its checkbox is enabled.
- YTD filters by monthly metric, not by cost.
- Summary consolidates valid sites; a tactic slide represents one specific site.
- Normalization, KPI, benchmark, order, and anomaly rules remain; Summary now filters combinations before consolidating the card.