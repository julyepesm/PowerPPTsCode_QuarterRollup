# Rollup investigation - September 18, 2026

The reported zero-match error was reproduced against the configured Power BI
dataset. The requested X codes are **Client Code** values; DMA Market Code uses
values such as ALBGA and ATLGA. The diagnostic snapshot is saved locally at
`Generated_Slides/diagnostics/rollup_catalog.csv`.

## Corrections

- Select brand plus Client Code. Buick XTPC includes both TALFL and PANFL.
  Per the user's correction, GMC XTPC is two separate reports, XTPC-PANFL and
  XTPC-TALFL; each filters its exact Market Code in discovery, summary, and YTD
  queries. The expected total is 23 decks (11 Buick and 12 GMC).
- Combine the selected client rows under the blueprint's display name before
  rendering the Executive Summary, avoiding a second single-DMA name filter.
- Executive Summary and cover: June-August 2026. Per the user's correction,
  YTD KBA and impressions: January-August 2026.
- Preserve low-volume tactics/months in the rollup by bypassing the monthly
  report's spend, video-completion, and YTD volume thresholds.
- Fix the YTD caller: chart functions return one Slide, not a presentation/slide
  tuple. Require the cover, summary, and both YTD slides before saving a rollup.
- Record every requested pair, continue after individual failures, and save
  readable CSV and machine-readable JSON results in each batch folder.
- The Windows rollup launcher uses the local `.venv` when available.

## Validation

- 32 regression tests passed; includes brand-specific XTPC splitting, Client Code selection, multi-DMA retention,
  partial-batch reporting, YTD return values, January-August query selection,
  and retention of low-volume January data.
- Streamlit AppTest passed startup and partial-result rendering.
- The corrected live batch contains 20 of the expected 23 decks: 8 Buick and 12 GMC.
  Both replacement GMC XTPC decks were generated and checked. Their eight DAX
  queries assert both Client Code XTPC and the respective Market Code. See
  `xtpc_query_validation.json` in the batch folder. The old combined GMC deck
  was moved to `Generated_Slides/diagnostics/superseded`.
- Saved deck inspection passed on 19 current decks: cover June-August, both YTD labels
  January-August, 5 or 6 slides (separate audience summaries where present).
  Buick Atlanta was locked by another process and could not be reopened for
  this inspection. No external application was closed to release it.
- Final test batch: `Generated_Slides/Buick_GMC_Rollup_2026-09-18_11-00-05`.
  Earlier test batches were removed. Logs remain under `Generated_Slides/diagnostics`.

## Remaining data/QC work

- Buick XALY (Albany) and XCLM (Columbus): no tactic rows returned for June-August.
- Buick XMAC (Macon): no brand/client pair in the live catalog.
- Confirm whether these are expected no-activity cases or missing source data.
  No alternative client mapping or empty deck has been invented.
- The generated decks are test outputs. Full numerical reconciliation against
  the monthly Proof of Performance reports and visual review remain outstanding;
  those monthly reports were not supplied in this checkout.

The Power BI calls queried the existing dataset; they did not refresh it.
