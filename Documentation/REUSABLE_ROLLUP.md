# Reusable rollup builder

The rollup UI now supports selecting a month range or calendar quarter, brand,
region, and individual markets. Use `Button_Rollup.bat` and open port 8502.

## Workflow and reporting rules

- Choose Month range using start/end month and year, or Quarter using Q1-Q4
  and year. A quarter covers January-March, April-June, July-September, or
  October-December. The default range is the last three completed months.
- Choose one supported brand and a tier. Zone and LMA remain separate, matching
  the monthly application's reporting model.
- Load markets queries the existing Power BI dataset for the complete period.
  It does not refresh the dataset. When sign-in is needed, the UI displays a Microsoft link and device code.
  Authentication is initiated only on loading,
  rather than automatically when opening the page.
- Choose a region, All regions, or Unassigned region if blank regional metadata
  exists. Region is an actual DAX filter on discovery, summary, and YTD queries.
- Choose specific markets, Select all, or Clear selection. Generation remains
  disabled until at least one market is selected. Changing region clears the
  market selection; changing brand, tier, or dates requires a matching catalog.
- The Executive Summary covers the selected period. YTD runs from January of
  the end year through the selected end month. Cross-year summaries are allowed;
  their titles show both years. YTD still refers only to the end year.
- LMA scopes use brand, tier, region, Client Code, and Market Code. Buick XTPC
  is the explicit combined-client exception; GMC XTPC uses separate PANFL and
  TALFL scopes. ZONE scopes aggregate clients within brand/tier/region/Market Code.
  The user reconfirmed that Buick XTPC stays combined because it is not split
  in Power BI; distinct markets in Power BI otherwise receive their own decks.
- Incomplete client/market mappings are displayed for review rather than guessed.
  For split scopes, records without a usable Market Code cannot be assigned to
  either deck. Blank regions are selectable and queried explicitly.
- The catalog is based on activity during the selected period. Unlike the original
  fixed batch, the UI does not promise output for markets absent from that catalog.

## Implementation

`Scripts/rollup_builder.py` owns period normalization, quarter boundaries,
period-aware catalog queries, target selection, and batch execution. The UI
keeps its authenticated generator and loaded catalog in per-session state;
credentials and catalog data are not shared through a global Streamlit cache.

`Scripts/powerbi_connector.py` accepts an optional device-code display callback;
the reusable UI uses it to show sign-in directly on the page. Existing terminal
instructions and token reuse remain available.

`Scripts/data_queries.py` and the corresponding orchestrator methods accept an
optional region filter. Existing monthly callers omit it and retain their
previous behavior. The rollup renderer also handles single-month and cross-year
titles and normalizes input dates to month starts.

New batches use a distinct `Generated_Slides/Rollup_<range>_<timestamp>` folder.
Decks are saved directly in the batch folder using the selected reporting mode:
`XTPC Buick June-Aug 2026 Summary.pptx` or `XTPC Buick Q3 2026 Summary.pptx`.
Calendar-quarter filenames are used only when Quarter mode is selected; Q3
means July-September. Split client reports retain a market suffix, for example
`XTPC-PANFL GMC Q3 2026 Summary.pptx`. Paths are capped at 240 characters for Windows/Office;
long filenames are shortened, and existing files receive a collision counter.
`selection.json` records the requested scopes. `rollup_results.csv` and
`rollup_results.json` are updated after each report so partial failures remain
reviewable. The JSON also records unresolved catalog mappings.

The original `--quarter-rollup` CLI and its fixed 23 expected scopes remain
available for reproducing the earlier Buick/GMC deliverable.

## Validation

The full 45-test suite passed after implementation, including Streamlit AppTest
coverage for brand/region selection, market selection, Select all/Clear selection,
quarter selection, generation, and stale-catalog protection. Backend tests cover
all four brands, both tiers, quarter/cross-year dates, region predicates across
the four report query types, XTPC scope rules, and persistent partial failures.

The read-only live catalog check passed for all eight brand/tier combinations
using June-August 2026. NCR, NER, SCR, SER, and WER were returned. Cadillac ZONE
had no data for that period; Chevrolet LMA included eight catalog records with
unusable mappings, which the builder reports for review instead of assigning.
Evidence is saved under `Generated_Slides/diagnostics/reusable_live_validation.json`.
No new complete set of live decks was generated for arbitrary periods or regions;
the prior deck checks cover the original June-August deliverable.
Generated PowerPoints and local diagnostic artifacts are not tracked in Git.
The earlier three Buick data gaps and outstanding monthly PoP reconciliation
remain documented in `ROLLUP_VALIDATION.md`; these controls do not resolve source
data gaps or certify arbitrary-period financial totals.

## Windows save-path correction

A June-August Buick NER run for BBPG-BURVT, XBAL-BALMD, and XBOS-BOSMA
failed with `FileNotFoundError` even though its output directories existed. The
resolved paths were 273 characters, and a direct write reproduced the failure.
The reusable batch now removes per-scope/nested monthly folders and uses compact
filenames via the real PowerPoint save method. Monthly and fixed-batch defaults
retain their previous folder behavior. Regression tests now save and reopen real
PowerPoint files under the actual long workspace root, including duplicate names
and truncation cases. All 43 tests passed. The failed run's reports have not been
regenerated; restart the launcher and rerun the same selection.
