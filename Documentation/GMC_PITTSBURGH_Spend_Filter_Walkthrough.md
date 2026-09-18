# GMC Pittsburgh - Dataset-to-Deck Walkthrough

This guide starts with the complete provided dataset and follows it through every expected slide in a full deck.

## 1. Complete dataset

| Year | Month | Day | Brand | Audience | Tier | Market Code | Market Name | Tactic | Subtactic | Strategy | Site | Total Cost | Impressions |
|---:|---|---:|---|---|---|---|---|---|---|---|---|---:|---:|
| 2026 | June | 1 | GMC | GEN | LMA | PITPA | PITTSBURGH, PA | Display | Standard | BT/InMarket | EMRGE | $9,604.24 | 3,373,848 |
| 2026 | June | 1 | GMC | GEN | LMA | PITPA | PITTSBURGH, PA | Display | Standard | HPA | EMRGE | $4,262.49 | 1,384,830 |
| 2026 | June | 1 | GMC | GEN | LMA | PITPA | PITTSBURGH, PA | FEP | FEP | BT/InMarket | EMRGE | $19,234.66 | 841,116 |
| 2026 | June | 1 | GMC | GEN | LMA | PITPA | PITTSBURGH, PA | FEP | FEP | BT/InMarket | SportsnetPittsburgh | $0.00 | 181,138 |
| 2026 | June | 1 | GMC | GEN | LMA | PITPA | PITTSBURGH, PA | Meta Display | Social Display | Sales | Meta | $10,255.00 | 1,027,446 |
| 2026 | June | 1 | GMC | GEN | LMA | PITPA | PITTSBURGH, PA | PreRoll | PreRoll | BT/InMarket | EMRGE | $11,346.91 | 1,475,574 |
| 2026 | June | 1 | GMC | GEN | LMA | PITPA | PITTSBURGH, PA | PreRoll | PreRoll | HPA | EMRGE | $7,073.35 | 645,299 |
| 2026 | June | 1 | GMC | GEN | LMA | PITPA | PITTSBURGH, PA | YouTube | YouTube | BT/InMarket | EMRGE | $15,582.64 | 1,664,047 |
| **Total** | | | | | | | | | | | | **$77,359.29** | **10,593,298** |

The table contains `Sum of Total Cost` and `Sum of Impressions`. Each visible row may already combine multiple campaign-level source records.

## 2. Rules applied before slides are created

### 2.1 Report scope

Every row has the same report scope:

```text
Brand: GMC
Market: PITTSBURGH, PA
Market Code: PITPA
Month: June 2026
Tier: LMA
Audience: GEN
Minimum Aggregated Spend: $50
```

Because all rows are GEN, the deck needs one GEN Executive Summary.

### 2.2 Tactic normalization

Strategy splits the generic `Display` tactic. It does not split FEP, PreRoll, YouTube, or Meta Display.

| Raw Tactic | Strategy | Effective Tactic |
|---|---|---|
| Display | BT/InMarket | BT Display, shown as InMarket Display |
| Display | HPA | Consideration Display |
| FEP | BT/InMarket | FEP |
| Meta Display | Sales | Meta Display |
| PreRoll | BT/InMarket or HPA | PreRoll |
| YouTube | BT/InMarket | YouTube |

Therefore:

```text
The two Display rows become two different tactics.
The two PreRoll rows remain one tactic.
```

### 2.3 Combination aggregation

The spend unit is:

```text
Effective Tactic + Grouped Site + Audience
```

| Final Combination | Source Rows Used | Aggregated Cost | Aggregated Impressions |
|---|---|---:|---:|
| InMarket Display + EMRGE + GEN | Display / BT-InMarket | $9,604.24 | 3,373,848 |
| Consideration Display + EMRGE + GEN | Display / HPA | $4,262.49 | 1,384,830 |
| FEP + EMRGE + GEN | FEP / EMRGE | $19,234.66 | 841,116 |
| FEP + SportsnetPittsburgh + GEN | FEP / SportsnetPittsburgh | $0.00 | 181,138 |
| Meta Display + Meta + GEN | Meta Display / Meta | $10,255.00 | 1,027,446 |
| PreRoll + EMRGE + GEN | Both PreRoll rows | $18,420.26 | 2,120,873 |
| YouTube + EMRGE + GEN | YouTube / EMRGE | $15,582.64 | 1,664,047 |

PreRoll is aggregated as follows:

```text
Cost        = $11,346.91 + $7,073.35 = $18,420.26
Impressions = 1,475,574 + 645,299    = 2,120,873
```

### 2.4 Spend decision

```text
Aggregated Cost < $50  = low spend
Aggregated Cost >= $50 = passes
```

| Combination | Cost | Decision |
|---|---:|---|
| InMarket Display + EMRGE + GEN | $9,604.24 | Passes |
| Consideration Display + EMRGE + GEN | $4,262.49 | Passes |
| FEP + EMRGE + GEN | $19,234.66 | Passes |
| FEP + SportsnetPittsburgh + GEN | $0.00 | Low spend |
| Meta Display + Meta + GEN | $10,255.00 | Passes |
| PreRoll + EMRGE + GEN | $18,420.26 | Passes |
| YouTube + EMRGE + GEN | $15,582.64 | Passes |

Only SportsnetPittsburgh is below the `$50` threshold.

## 3. Expected full-deck order

Assuming full-deck mode and the required historical data is available:

| Slide | Expected Content |
|---:|---|
| 1 | Title |
| 2 | Executive Summary - GEN |
| 3 | FEP - EMRGE - GEN |
| 4 | FEP - SportsnetPittsburgh - GEN |
| 5 | PreRoll - EMRGE - GEN |
| 6 | YouTube - EMRGE - GEN |
| 7 | InMarket Display - EMRGE - GEN |
| 8 | Consideration Display - EMRGE - GEN |
| 9 | Meta Display - Meta - GEN |
| 10 | YTD KBA |
| 11 | YTD Impressions by Vehicle |
| 12 | Glossary |
| 13 | Error Summary |

The Error Summary is conditional. In this case, the SportsnetPittsburgh low-spend performance should create at least one anomaly in full-deck mode.

## 4. Slide 1 - Title

### Data used

```text
GMC
PITTSBURGH, PA
June 2026
LMA
```

### Rule

The title slide identifies the report. It does not aggregate spend or performance metrics.

## 5. Slide 2 - Executive Summary GEN

### Processing

```text
Start with the seven final combinations
-> remove FEP + SportsnetPittsburgh + GEN because $0 < $50
-> consolidate surviving sites by Effective Tactic + Audience
-> build one card per surviving tactic
```

### Expected cards

| Card | Included Source | Cost | Impressions |
|---|---|---:|---:|
| InMarket Display | Display / BT-InMarket / EMRGE | $9,604.24 | 3,373,848 |
| Consideration Display | Display / HPA / EMRGE | $4,262.49 | 1,384,830 |
| FEP | FEP / EMRGE only | $19,234.66 | 841,116 |
| Meta Display | Meta Display / Meta | $10,255.00 | 1,027,446 |
| PreRoll | Both PreRoll Strategy rows / EMRGE | $18,420.26 | 2,120,873 |
| YouTube | YouTube / EMRGE | $15,582.64 | 1,664,047 |
| **Summary total** | | **$77,359.29** | **10,412,160** |

### Why FEP shows 841,116

```text
All FEP impressions         = 841,116 + 181,138 = 1,022,254
Excluded Sportsnet          = 181,138
Executive Summary FEP       = 841,116
```

The Summary card does not include SportsnetPittsburgh, even though that combination has impressions.

### Not validated by this dataset

The screenshot does not contain Video Completions, Video Plays, KBAs, or Clicks. Therefore, it cannot validate the card KPI, benchmark color, or Total KBAs.

## 6. Slide 3 - FEP EMRGE GEN

### Source used

| Tactic | Strategy | Site | Cost | Impressions |
|---|---|---|---:|---:|
| FEP | BT/InMarket | EMRGE | $19,234.66 | 841,116 |

### Result

```text
Aggregated cost = $19,234.66
$19,234.66 >= $50
Decision = generate the slide
Impressions shown = 841,116
```

This slide matches the FEP Summary card because EMRGE is the only FEP site that passes the Summary spend filter.

Video Completes, VCR, KBAs, and historical values require additional fields.

## 7. Slide 4 - FEP SportsnetPittsburgh GEN

### Source used

| Tactic | Strategy | Site | Cost | Impressions |
|---|---|---|---:|---:|
| FEP | BT/InMarket | SportsnetPittsburgh | $0.00 | 181,138 |

### Result

```text
Aggregated cost = $0.00
$0.00 < $50
Impressions = 181,138
Decision = generate the current-month slide and log an anomaly
```

This slide is kept because it has performance. It is excluded from Executive Summary because Summary does not use performance to rescue low spend.

If historical spend filtering is enabled, June is removed from this slide's historical chart and KBA table because its monthly cost is below `$50`. The current-month metric boxes can still show the June data.

## 8. Slide 5 - PreRoll EMRGE GEN

### Sources used

| Strategy | Cost | Impressions |
|---|---:|---:|
| BT/InMarket | $11,346.91 | 1,475,574 |
| HPA | $7,073.35 | 645,299 |

### Result

```text
Both rows remain PreRoll.
Both rows have the same Site and Audience.
They become one PreRoll combination and one tactic slide.

Cost        = $18,420.26
Impressions = 2,120,873
Decision    = generate the slide
```

HPA does not create a Consideration Display slide here because the raw tactic is PreRoll, not Display.

## 9. Slide 6 - YouTube EMRGE GEN

### Source used

| Tactic | Strategy | Site | Cost | Impressions |
|---|---|---|---:|---:|
| YouTube | BT/InMarket | EMRGE | $15,582.64 | 1,664,047 |

### Result

```text
Aggregated cost = $15,582.64
Decision = generate the slide
Impressions shown = 1,664,047
```

For LMA, YouTube with total Video Completions of `0` is removed from Executive Summary. Video Completions is not present in this dataset, so that rule cannot be validated here.

## 10. Slide 7 - InMarket Display EMRGE GEN

### Source used

| Raw Tactic | Strategy | Site | Cost | Impressions |
|---|---|---|---:|---:|
| Display | BT/InMarket | EMRGE | $9,604.24 | 3,373,848 |

### Result

```text
Display + BT/InMarket -> BT Display
Visible title          -> InMarket Display
Aggregated cost        -> $9,604.24
Impressions shown      -> 3,373,848
Decision               -> generate the slide
```

This row is not combined with Display HPA because HPA resolves to a different effective tactic.

## 11. Slide 8 - Consideration Display EMRGE GEN

### Source used

| Raw Tactic | Strategy | Site | Cost | Impressions |
|---|---|---|---:|---:|
| Display | HPA | EMRGE | $4,262.49 | 1,384,830 |

### Result

```text
Display + HPA     -> Consideration Display
Aggregated cost   -> $4,262.49
Impressions shown -> 1,384,830
Decision          -> generate the slide
```

The Strategy changes this row's effective tactic before spend is evaluated.

## 12. Slide 9 - Meta Display Meta GEN

### Source used

| Tactic | Strategy | Site | Cost | Impressions |
|---|---|---|---:|---:|
| Meta Display | Sales | Meta | $10,255.00 | 1,027,446 |

### Result

```text
Effective tactic  = Meta Display
Aggregated cost   = $10,255.00
Impressions shown = 1,027,446
Decision          = generate the slide
```

The Sales Strategy does not rename Meta Display.

## 13. Slide 10 - YTD KBA

### Rule

YTD KBA is built from monthly KBA totals by tactic. It does not use the `$50` spend threshold.

### Current validation status

This dataset cannot produce the slide because it contains:

- Only June 2026.
- No KBA or Total Conversions field.

### Data required

```text
Month Year
Tactic
Total Conversions or KBA
```

Data should cover January through June 2026 for a complete June YTD slide.

## 14. Slide 11 - YTD Impressions by Vehicle

### Rule

YTD Impressions is built from monthly impressions by vehicle. It does not use the `$50` spend threshold.

### Current validation status

This dataset cannot produce the slide because it contains:

- Only June 2026.
- No Vehicle field.

### Data required

```text
Month Year
Vehicle
Impressions
```

Data should cover January through June 2026 for a complete June YTD slide.

## 15. Slide 12 - Glossary

The Glossary is static reference content. It does not use rows from this dataset and does not apply spend filtering.

## 16. Slide 13 - Error Summary

### Expected anomaly from this dataset

| Tactic | Site | Cost | Performance | Reason |
|---|---|---:|---:|---|
| FEP | SportsnetPittsburgh | $0.00 | 181,138 impressions | Low spend with performance |

The Error Summary should include this anomaly when the full deck generates the SportsnetPittsburgh tactic slide.

Other possible anomalies, such as VCR above `100%` or a cross-brand YTD vehicle, cannot be evaluated from the provided fields.

## 17. Final reconciliation

| Level | Cost | Impressions |
|---|---:|---:|
| Complete source dataset | $77,359.29 | 10,593,298 |
| Excluded from Executive Summary | $0.00 | 181,138 |
| Executive Summary after spend filtering | $77,359.29 | 10,412,160 |

```text
Executive Summary:
Filters combinations first, then consolidates surviving sites by tactic.

Tactic slides:
One slide per Effective Tactic + Grouped Site + Audience combination.
```

## 18. Additional data needed for complete slide validation

No additional data is needed to validate spend, normalization, impression totals, slide inclusion, or the FEP discrepancy.

To validate every displayed metric and conditional rule, provide:

- Video Completions.
- Video Plays.
- Total Conversions or KBAs.
- Clicks.
- Audio Completes and Audio Starts, if Audio exists.
- Viewable and Measured Impressions.
- Month Year history from January through June 2026.
- Vehicle for YTD Impressions.

With those fields, the team can also validate VCR, CPCV, CPA, CPC, ACR, Viewability, benchmarks, YTD slides, and strict LMA video filtering.