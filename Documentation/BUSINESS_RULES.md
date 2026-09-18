# PowerPPTs — Business Rules Reference

All rules currently enforced by the Python codebase. Each section links to the source file.

---

## 1. Market Search & Identification

> Source: `data_queries.py` — `_build_common_filters_list`

### 1.1 Code-First Strategy
- **Market Code** is always preferred over Market Name.
- If `market_code` exists and is not `"XXXXX"`, it is the sole market identifier.
- Market Name is only used as fallback when no code is available.

### 1.2 Strict vs. Relaxed Name Matching
| Mode | When Used | DAX Filter |
|------|-----------|------------|
| **Strict** (`strict=True`) | Data slides, tactic queries | `[Market Name] = "exact name"` |
| **Relaxed** (`strict=False`) | Discovery, initial search | `CONTAINSSTRING([Market Name], "partial")` |

### 1.3 Required Filter Coupling
Every query always includes:
- Brand (`Brand (Reporting)`)
- Market (Code or Name)
- Date (`Month Year`) — when applicable
- Zone/LMA — when provided

### 1.4 Client Code Logic (LMA vs. ZONE)
| Tier | Client Code Behavior |
|------|---------------------|
| **LMA** | Client Code is kept as a mandatory filter (discriminates between dealerships sharing the same market) |
| **ZONE** | Client Code is set to `None` — all clients under the market code are aggregated |

---

#### Multiple Client Codes Under One Market Code

The same Market Code may be associated with more than one Client Code. The
reporting behavior depends on the selected tier:

| Scenario | Result |
|----------|--------|
| `Market Code = DETMI`, `Tier = LMA`, `Client Code = XDET` | Generate an LMA report filtered to `DETMI + XDET` only. |
| `Market Code = DETMI`, `Tier = LMA`, `Client Code = ABCD` | Generate a separate LMA report filtered to `DETMI + ABCD` only. |
| `Market Code = DETMI`, `Tier = ZONE` | Generate one ZONE report filtered to `DETMI + ZONE`; aggregate XDET, ABCD, and every other client belonging to that market's ZONE data. |

Therefore:

- Two Client Codes under the same Market Code produce **two separate LMA
  reports**, one per Client Code.
- They produce **one consolidated ZONE report** when ZONE is selected.
- LMA data must never be mixed across Client Codes.
- ZONE aggregation must not retain a Client Code filter; otherwise the ZONE
  report would be incomplete.

The batch generator applies this rule before running market queries:

```python
effective_client_code = None if sel_type == "ZONE" else client_code
```

The Client Code is preserved for LMA requests and deliberately removed for
ZONE requests.

### 1.5 Market Metadata Discovery Sequence

Before generating slides, the orchestrator resolves market metadata in this
order:

1. The UI provides the selected Brand, Market Code (when available), Market
   Name, report month, and tier (`LMA` or `ZONE`).
2. The metadata query uses the Market Code as the primary identifier when it
   is known and is not `"XXXXX"`.
3. If no usable Market Code is available, the query falls back to Market Name
   matching according to the selected strict/relaxed mode.
4. The returned canonical Market Name, Market Code, and Region are reused by
   all subsequent executive-summary, tactic, historical, YTD, and vehicle
   queries.

This prevents ambiguous names from selecting data belonging to another
market. For example, two markets with similar names may still be distinguished
when their Market Codes differ.

The code does not generally replace an explicitly requested LMA Client Code
with an arbitrary alternative client. A missing or invalid LMA client should
be treated as a data/configuration issue. Only ZONE requests intentionally
remove the Client Code filter so that all clients under the Market Code are
included.

---

## 2. Data Filtering Rules

### 2.0 Slide grain: title, site, and audience

- The slide's main title identifies the effective Tactic.
- The site and audience shown with the slide identify the data scope. For example, `Search` + `GoogleAds` + `GEN` is one reporting combination.
- Historical and current metrics must be aggregated by:

```text
Tactic + Site + Audience + Tier/Client
```

- `GEN` and `HIS` must never be combined.
- `Strategy (groups)` is not an additional filter for Search, FEP, YouTube, PreRoll, or other tactics whose title does not show a strategy-specific variant.
- `Strategy (groups)` is used only when the generic `Display` tactic is intentionally resolved into a title-specific variant such as `InMarket Display`, `Consideration/HPA Display`, or `Retargeting Display`.

Examples:

```text
Search + GoogleAds + GEN
  Include all Search strategy values for GoogleAds and GEN.

Display + GoogleAds + GEN + InMarket Display
  Include only the strategy values that resolve to InMarket Display.
```

### 2.1 Tactic Slide — Historical Data Window
> Source: `main_slide_generator.py` L969–978

- **6-month rolling window** ending at the selected report month.
- Example: If report month = April 2026, window = Nov 2025 → Apr 2026.

### 2.2 Tactic Slide — Current Month Spend Threshold
> Source: `main_slide_generator.py`, `filters_manager.py`

- Spend is aggregated first within each effective Tactic + grouped `Site (Reporting)` + Audience combination.
- `min_tactic_spend` defaults to `$50` and is configurable in the UI.
- If aggregated spend is below the threshold and performance is zero (impressions, KBAs, video, and clicks are all zero), the tactic slide is skipped.
- If aggregated spend is below the threshold but performance exists, the slide is kept and an anomaly is logged, preserving the former `$0`-cost behavior.
- The threshold is inclusive: `$50.00` passes when the configured minimum is `$50.00`; `$49.99` is below threshold.

#### Current-month zero-cost rule

- A current-month tactic/site/audience combination with `$0` spend but measurable activity is kept and logged as an anomaly.
- A combination with `$0` spend and no measurable activity is skipped.
- `GEN` and `HIS` are separate audiences. Performance from `GEN` must never be added to an `HIS` slide, and vice versa.

### 2.3 Tactic Slide — Historical Window Spend Filter (STRICT)
> Source: `main_slide_generator.py`

```
If aggregated Total Cost for a tactic/month is below min_tactic_spend,
that month is removed from the chart and KBA table.
```

- This filter applies per tactic, per month when `Exclude Months Below Spend Threshold` is enabled.
- It checks only cost, not KBAs, impressions, or any other metric.
- The threshold boundary is included.

#### Historical zero-cost rule

- Historical data is evaluated after filtering to the exact Tactic + Site + Audience combination for the slide. Strategy is added only for a strategy-specific Display variant.
- A historical month with `$0` total spend is removed, even if it has impressions, video completions, clicks, or KBAs.
- If a month contains both paid rows and `$0`-cost rows for the same Tactic + Site + Audience, all rows are included in that month's aggregate. The month passes because its combined spend is positive.
- A `$0`-cost row from another audience is never included. For example, a `GEN` row must not be added to an `HIS` slide.

Example:

```text
April | FEP | EMRGE | HIS | $5,000 | 100,000 completions
April | FEP | EMRGE | HIS | $0     | 10,000 completions
April total for HIS = $5,000 and 110,000 completions
```

The second row is included because it belongs to the same filtered combination and the month has positive spend.

```text
April | FEP | EMRGE | HIS | $0 | 10,000 completions
```

This month is removed from the historical chart because its total spend is `$0`.
### 2.4 Video Tactic — 0 Completions Skip
> Source: `main_slide_generator.py` L830–848

- Video tactics: `FEP, YouTube, OLV, CTV, Meta Video, Pinterest Video, TikTok, PreRoll`.
- If a video tactic has `0 video completions` and no other activity (no impressions, no KBAs), it is **skipped**.
- If it has 0 completions but has impressions or KBAs, the slide is **kept**.

### 2.5 Executive Summary — Cost & Spend Filters
> Source: `measures.py` L239–250, `executive_summary.py`

- Executive Summary spend is controlled by `min_tactic_spend`; there is no separate hardcoded `$0 total cost` exclusion.
- The threshold is applied first at the same granularity as tactic slides: effective tactic + grouped site + audience.
- Only site combinations that meet the threshold contribute impressions, KBAs, and other metrics to the final tactic card.
- With `min_tactic_spend = 0`, zero-cost combinations remain eligible for the executive summary.
- Executive Summary cards are also audience-specific. `GEN` and `HIS` combinations must not be combined.

### 2.6 Investment by Nameplate
> Source: `spend_outcomes.py`, `components/table_components_mixin.py`

- Include every nameplate with positive investment activity.
- Do not exclude a nameplate solely because its share of total investment is below `1%`.
- Nameplates with activity below `0.5%` are displayed as `0.0%` in the Investment by Nameplate table.
- Nameplates with zero investment are excluded.

### 2.7 Executive Summary — LMA Video Filter
> Source: `executive_summary.py` L83–106

- **LMA only**: `FEP` and `YouTube` tactics with `0 video completions` are removed from the exec summary.
- ZONE does not apply this strict filter.

### 2.8 YTD Slides — Spend and Metric Filters
> Source: `main_slide_generator.py` L1227—1240

- YTD queries return rows at the chart grain (Month + Tactic for KBA and Month
  + Vehicle for Impressions), but spend is summed across all categories to
  obtain one aggregated Total Cost per month.
- The monthly total must meet the configurable `min_tactic_spend`. The commonly
  used `$50` value is only the current/default configuration, not a hardcoded
  YTD rule. This replaces the former zero-cost month rule.
- If monthly spend is below the threshold, the entire month is removed from
  both YTD views and one deduplicated anomaly is added to the Error Summary.
- The threshold is inclusive: a month equal to `min_tactic_spend` remains.
- After spend filtering:
  1. Monthly totals are calculated across the remaining category columns.
  2. Any month with a total of `0` is removed from the pivoted chart.
  3. If the YTD metric filter is enabled, the remaining month-level total must meet a threshold:
     - **Impressions slides** use `ytd_min_impressions`.
     - **KBA / outcomes slides** use `ytd_min_outcomes`.

### 2.9 YTD Slides — Year Limit
> Source: `main_slide_generator.py` L1213—1217

- YTD data is limited to the **selected year** and **up to the selected month**.
- Example: April 2026 → only Jan—Apr 2026 data is included.

---

### 2.10 Vehicle Insights & Summary Slides
> Source: `vehicle_catalog.py`, `config/vehicle_images.json`, `vehicle_insights_summary.py`, `main_slide_generator.py`

- Applies to Buick, GMC, and Cadillac full decks.
- Each Insights/Summary pair is inserted after both YTD slides and before the Glossary.
- Raw Power BI vehicle values are resolved through JSON aliases to a canonical model before any aggregation.
- Each JSON entry also declares its taxonomy classification/status and whether it may generate slides. Approved models and multiline values generate; explicit rollups, cross-brand errors, and ambiguous values do not.
- Current-month rows are aggregated by canonical Vehicle + effective Tactic + grouped Site + Audience, so aliases of the same model contribute to one spend decision and one slide pair.
- The configured `min_tactic_spend` is inclusive; only qualifying combinations feed the vehicle slides.
- A vehicle receives its Insights/Summary pair when at least one combination qualifies.
- A vehicle with no qualifying combination is omitted and recorded in the Error Summary with its total spend and highest combination spend. A taxonomy-excluded value is also omitted and recorded with the reason stored in JSON.
- Insights charts use a three-month rolling window. When historical spend filtering is enabled, the same inclusive spend threshold is applied at the vehicle combination/month grain.
- The JSON catalog is the only source for canonical names, aliases, and Insights/Exec image paths; Python does not infer images from filenames or contain model-specific fallbacks.
- An approved JSON model with a missing configured path, intentional null image, or absent file still generates and renders `NO IMAGE CAR`.
- A Power BI value absent from the JSON remains independently identified but does not generate slides; it is recorded as a pending-review anomaly. This prevents unknown/truncated values from being merged or printed silently.

---

## 3. Tactic Normalization

### 3.1 Name Mappings (JSON-driven)
> Source: `config/normalization_rules.json`

| Raw Name in PBI | Normalized To |
|----------------|---------------|
| Pre-roll | PreRoll |
| Preroll | PreRoll |
| Digital Video | PreRoll |
| OLV | PreRoll |
| CTV | FEP |

### 3.2 Display Tactic Resolution (Strategy-based)
> Source: `display_resolution.py`

The generic `Display` tactic is split based on the `Strategy (groups)` field.
The internal name and the visible slide title are not always identical:

| Strategy Contains | Resolves To |
|-------------------|-------------|
| BT, InMarket, In Market, In-Market, Purchase | **BT Display** |
| Retargeting, Retarget | **Retargeting Display** |
| Consideration, HPA | **Consideration Display** |
| *(no strategy)* | **BT Display** (default) |

The display-title override presents the internal `BT Display` tactic as
**InMarket Display** on slides. Therefore the complete mapping is:

```text
Display + BT/InMarket  -> internal BT Display       -> shown as InMarket Display
Display + HPA          -> internal Consideration Display
Display + Retargeting  -> internal Retargeting Display
Display + no strategy  -> internal BT Display       -> shown as InMarket Display
```

If a strategy is unknown, the generic `Display` tactic defaults to internal
`BT Display` for safety. This fallback is not applied to unrelated tactics.

### 3.3 Social/Meta Normalization
> Source: `display_resolution.py`

| Raw Tactic or Site Contains | Resolves To |
|-----------------------------|-------------|
| Social Display, Meta Display, Paid Social, Facebook Display, Meta Ads | **Meta Display** |
| Social Video, Meta Video | **Meta Video** |
| Pinterest, TikTok | *(unchanged — excluded from Social normalization)* |

The following social site names or aliases also resolve to Meta when used as
the site context: `Facebook`, `Meta`, `Instagram`, `Twitter`, `Snapchat`,
`Social`, `IG`, and `FB`. Every alias must appear as an independent token, not
as part of a compound word. For example, `DetroitTigers`, `FBinvestors`, and
`MetaInvestors` do not resolve to Meta, while `IG Ads`, `Facebook Ads`, and
`FB/IG` do.

Already-normalized tactics such as `FEP`, `PreRoll`, `YouTube`, `Audio`,
`Search`, `Meta Display`, and `Meta Video` remain unchanged unless they match
an explicit social normalization rule.

### 3.4 Site Grouping
> Source: `config/normalization_rules.json`

Multiple raw site names are grouped into a single display name:

| Display Name | Raw Sites Included |
|-------------|-------------------|
| Ampersand | Ampersand-Spectrum, ampersand MSP FEP, Ampersand-GEN, etc. |

---

## 4. Slide Ordering

> Source: `config/normalization_rules.json` — `sorting_ranks`

Slides are ordered by tactic rank, then by audience (GEN before HIS):

| Rank | Tactic |
|------|--------|
| 10 | FEP |
| 30 | PreRoll |
| 40 | YouTube |
| 50 | BT Display |
| 55 | Consideration Display |
| 60 | Retargeting Display |
| 70 | Meta Display |
| 80 | Meta Video |
| 90 | Pinterest Display |
| 100 | Pinterest Video |
| 110 | TikTok |
| 120 | Search |
| 130 | Audio |

FEP has sub-sorting: EMRGE (11) — MSP (12) — Other (13).

---

## 5. Metrics Per Tactic

> Source: `tactic_config.py` — `_build_metric_definitions`

| Tactic | Box 1 | Box 2 | Box 3 | Box 4 |
|--------|-------|-------|-------|-------|
| FEP | Impressions | Video Completes | VCR | — |
| PreRoll | Impressions | Video Completes | VCR | Viewability |
| YouTube | Impressions | Video Completes | CPCV | YT Viewability |
| BT Display | Impressions | Total KBAs | CPA | Viewability |
| Consideration Display | Impressions | Total KBAs | CPA | Viewability |
| Retargeting Display | Impressions | Total KBAs | CPA | Viewability |
| Meta Display | Impressions | Total KBAs | CPA | — |
| Meta Video | Impressions | Video Completes | VCR | — |
| Pinterest Display | Impressions | Total KBAs | CPA | — |
| Pinterest Video | Impressions | Total KBAs | CPA | — |
| TikTok | Impressions | Video Completes | CPCV | — |
| Search | Impressions | Clicks | CPC | — |
| Audio | Impressions | Audio Completes | ACR | — |

4-box tactics: `PreRoll, YouTube, BT Display, Consideration Display, Retargeting Display`.

---

## 6. Chart Configuration Per Tactic

> Source: `tactic_config.py` — `_build_chart_configurations`

| Tactic | Bar Metric | Line Metric |
|--------|-----------|-------------|
| FEP | Video Completions | VCR |
| PreRoll | Video Completions | VCR |
| YouTube | Video Completions | CPCV |
| Meta Video | Video Completions | VCR |
| TikTok | Video Completions | CPCV |
| BT/Consideration/Retargeting Display | Total Conversions | CPA |
| Meta Display | Total Conversions | CPA |
| Pinterest Display | Total KBAs | CPA |
| Pinterest Video | Total Conversions | CPA |
| Search | Clicks | CPC |
| Audio | Audio Completes | ACR |

---

## 7. KPI & Benchmark Rules

### 7.1 KPI Selection Per Tactic (Executive Summary)
> Source: `measures.py` — `select_kpi_value`

| Tactic | KPI Used |
|--------|----------|
| YouTube, TikTok | CPCV |
| FEP, PreRoll, Meta Video, Social Video | VCR |
| Display variants, Meta Display, Pinterest, Social Display | CPA |
| Search | CPC |
| Audio | ACR |

### 7.2 KPI Color Logic
> Source: `measures.py` — `determine_color`

| KPI Type | Green Condition | Red Condition |
|----------|----------------|---------------|
| CPA, CPCV, CPC | Value — Benchmark | Value > Benchmark |
| VCR, ACR, CTR | Value — Benchmark | Value < Benchmark |
| TBD benchmark | Black (neutral) | — |
| N/A benchmark | Gray (neutral) | — |

### 7.3 Fixed Benchmarks
| Metric | Fixed Value |
|--------|-------------|
| Viewability | >70% |
| YT Viewability | >90% |

### 7.4 Historical Benchmarks
> Source: `config/benchmarks.json`

Some benchmarks change over time (e.g., BT Display CPA). The system selects the **most recent benchmark date that is — the report month**.

Example for GMC — BT Display — CPA:
- Before 2024-02-01: $0.17
- 2024-02-01 to 2025-03-31: $0.35
- 2025-04-01 onward: $0.30

---

## 8. Derived Metric Calculations

> Source: `measures.py` — `calculate_metrics`

| Metric | Formula |
|--------|---------|
| VCR | Video Completions / Video Plays |
| CPCV | Total Cost / Video Completions |
| CPA | Total Cost / Total Conversions |
| CPC | Total Cost / Clicks |
| ACR | Audio Completes / Audio Starts |
| Viewability | Unique Viewable Impressions / Unique Measured Impressions |
| YT Viewability | Active View: Viewable Impressions / Active View: Measurable Impressions |

All divisions return 0 when the denominator is 0 (safe division).

---

## 9. File Naming & Output

> Source: `main_slide_generator.py` L1302–1355

### LMA Format
```
{prefix} {Brand} {Month Year} Digital Metrics.pptx
```
Where `prefix` = UI file_prefix — client_code — market_code (first available).

### ZONE Format
```
{market_code}-{Month Year} {Brand} Zone Reporting.pptx
```

### Folder Structure
```
Generated_Slides/{Zone|LMA}/{Brand}/{MM - MonthName}/{Region}/
```

### Collision Safety
If a file already exists, the market code is appended: `filename (MARKET_CODE).pptx`.

---

## 10. Deck Structure (Slide Order)

| # | Slide | Always Present |
|---|-------|---------------|
| 1 | Title Slide | — |
| 2+ | Executive Summary (one per audience) | — |
| 3+ | Tactic Slides (sorted by rank, then audience) | — (skipped in summary_only mode) |
| N-2 | YTD KBA Breakdown | — |
| N-1 | YTD Impressions by Vehicle | — |
| N | Glossary | — |
| Last | Error Summary (only if anomalies detected) | Conditional |

---

## 11. Anomaly Detection

> Source: `error_collector.py`, `slide_components.py`

The system logs anomalies that appear on a final "Error Summary" slide:

- **$0 cost with performance**: Tactic has impressions/video but no spend.
- **VCR > 100%**: Video Completion Rate exceeds 100% — clamped to 100% in the chart.
- **Cross-brand vehicles**: YTD Impressions chart detected a vehicle belonging to a different brand.

---

## 12. Display Title Override

> Source: `executive_summary.py` L284—287

| Internal Name | Displayed As |
|--------------|-------------|
| BT Display | InMarket Display |

This is a visual override only — internal processing uses `BT Display`.
