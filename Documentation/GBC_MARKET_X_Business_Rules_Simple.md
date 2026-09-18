# PowerPPTs - Business Rules (Simple)

## 1. Data scope

- Use Market Code when available; otherwise use Market Name.
- Always filter by Brand, Market, Report Month, and Tier.
- LMA keeps Client Code as a required filter.
- ZONE combines clients under the selected Market Code.
- GEN, HIS, and other audiences are processed separately.
- A blank audience is treated as GEN.

## 2. Normalization

- Normalize tactic names before filtering.
- `Pre-roll`, `Preroll`, `OLV`, and `Digital Video` become `PreRoll`.
- `CTV` becomes `FEP`.
- Display is resolved by Strategy:
  - BT, InMarket, or Purchase becomes `BT Display`, shown as `InMarket Display`.
  - Retargeting becomes `Retargeting Display`.
  - Consideration or HPA becomes `Consideration Display`.
- Equivalent sites are grouped before totals are calculated.
- Social and Meta naming is normalized to `Meta Display` or `Meta Video`.
- Pinterest and TikTok remain separate tactics.

## 3. Spend threshold

- The default minimum aggregated spend is `$50`.
- The UI can change this value.
- Aggregate source rows before applying the threshold.
- Evaluate spend by:

```text
Effective Tactic + Grouped Site + Audience
```

- Cost below the threshold is low spend.
- Cost equal to or above the threshold passes.
- The threshold is not applied to individual source rows.
- The spend threshold does not apply to YTD slides.

### Critical aggregation difference

Tactic slides are not filtered one source row at a time. Both views aggregate source rows first.

| View | Aggregation rule |
|---|---|
| Tactic slide | Aggregates all source rows for one `Effective Tactic + Grouped Site + Audience` combination. Each combination gets its own slide. |
| Executive Summary | Starts with the same combinations, removes low-spend combinations, and then adds all surviving sites into one card per `Effective Tactic + Audience`. |

Processing flow:

```text
Tactic slide:
Source rows -> one Tactic + Site + Audience total -> apply spend rule

Executive Summary:
Source rows -> Tactic + Site + Audience totals -> remove low spend
-> add surviving sites into one Tactic + Audience card
```

Concrete FEP example from GMC Pittsburgh:

| Combination | Cost | Impressions | Tactic Slide | Executive Summary |
|---|---:|---:|---|---|
| FEP + EMRGE + GEN | $19,234.66 | 841,116 | Separate EMRGE slide | Included in FEP card |
| FEP + SportsnetPittsburgh + GEN | $0.00 | 181,138 | Kept with anomaly | Excluded from FEP card |

```text
All FEP source data       = 841,116 + 181,138 = 1,022,254
FEP Executive Summary     = 841,116 impressions
FEP EMRGE tactic slide    = 841,116 impressions
FEP Sportsnet tactic slide = 181,138 impressions
```

See the [GMC Pittsburgh step-by-step walkthrough](GMC_PITTSBURGH_Spend_Filter_Walkthrough.md) for the complete reconciliation.

## 4. Executive Summary

- Exclude every low-spend combination, even when it has performance.
- After filtering, combine surviving sites into one card per tactic and audience.
- Calculate metrics and KPIs only from surviving combinations.
- One Executive Summary slide is generated per audience.
- For LMA, remove FEP and YouTube cards when total Video Completions is `0`.
- The strict FEP and YouTube rule does not apply to ZONE.

## 5. Current-month tactic slides

- A combination at or above the spend threshold is included.
- A low-spend combination with performance is included and logged as an anomaly.
- A low-spend combination without performance is skipped.
- Performance means at least one of these is greater than `0`:
  - Impressions.
  - KBAs.
  - Video Completions.
  - Clicks.

## 6. Historical tactic data

- Use the number of months selected in `Historical Window (Months)`.
- The window ends with the report month.
- When `Exclude Months Below Spend Threshold` is enabled, remove historical months below the spend threshold.
- Historical spend is evaluated after monthly aggregation.
- This rule checks cost only; performance does not rescue the month.
- When the control is disabled, months are not removed because of spend.

## 7. Video tactic slides

When `Skip Video Tactics w/ 0 Completions` is enabled:

- Skip a video tactic with `0` Video Completions, `0` Impressions, and `0` KBAs.
- Keep a video tactic with `0` Video Completions when Impressions or KBAs are greater than `0`.

## 8. YTD slides

- YTD uses metric thresholds, not spend thresholds.
- Include only the selected year through the report month.
- YTD Outcomes evaluates the total monthly outcomes across tactics.
- YTD Impressions evaluates the total monthly impressions across vehicles.
- When `Apply YTD Threshold Filter` is enabled:
  - Keep Outcomes months at or above `Min YTD Outcomes`.
  - Keep Impressions months at or above `Min YTD Impressions`.
- The exact YTD threshold passes.
- A month with a total metric of `0` is always removed.

## 9. KPI calculations

| KPI | Formula |
|---|---|
| VCR | Video Completions / Video Plays |
| CPCV | Total Cost / Video Completions |
| CPA | Total Cost / Total Conversions |
| CPC | Total Cost / Clicks |
| ACR | Audio Completes / Audio Starts |
| Viewability | Viewable Impressions / Measured Impressions |

- Division by `0` returns `0`.
- Calculate KPIs after filtering and aggregation.
- Do not average row-level KPIs.
- Lower is better for CPA, CPCV, and CPC.
- Higher is better for VCR, ACR, and CTR.

## 10. Anomalies

Log an anomaly when:

- A low-spend tactic has performance.
- VCR is greater than `100%`.
- A YTD vehicle belongs to another brand.

The Error Summary slide is generated only when anomalies exist.

## 11. Final rule summary

```text
Aggregate source rows first.
Tactic slide = one Effective Tactic + Grouped Site + Audience combination.
Executive Summary = all surviving combinations added by Tactic + Audience.
Below $50 is low spend; exactly $50 passes.
Summary excludes low spend.
Current tactic slides may keep low spend with performance.
History filters by monthly cost.
YTD filters by monthly metric, not cost.
```