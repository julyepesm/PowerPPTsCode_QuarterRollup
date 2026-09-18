# Current handoff: Buick/GMC rollup

Updated September 18, 2026. Start here when continuing this project.
This supersedes the requirements and blocker in `MICKEY_HANDOFF.md`, which is
retained as the original investigation history.

## Current outcome and approved reporting rules

The application now generates reports from the live Power BI dataset. The
zero-match catalog error and a subsequent YTD slide-generation error are fixed.
The current test batch contains **20 of 23 expected decks**. Three Buick scopes
remain unresolved because the expected source data was not returned.

- Cover and Executive Summary: June-August 2026, inclusive.
- YTD KBA and impressions slides: January-August 2026, not June-August alone.
- Expected output: 11 Buick decks and 12 GMC decks.
- Buick XTPC is one combined Tallahassee/Panama City deck.
- GMC XTPC is two separate decks: XTPC-PANFL and XTPC-TALFL. Apply both Client
  Code XTPC and the respective Market Code to every discovery, summary, and
  YTD query. Do not combine these GMC markets again.
- Keep tactics active in any selected month, including low-volume activity.
- Preserve the existing branded layout and audience-specific summaries. The
  tested decks contain five or six slides: cover, one or two audience summaries,
  YTD KBA, YTD impressions, and glossary.

Client Codes: XALY, XATL, XAUG, XBIR, XCHN, XCLM, XHUN, XMAC, XMON, XMOB, XTPC.
The X codes are **Client Codes**, not the dataset's DMA Market Codes.

## Changes made

| File | Change and reason |
| --- | --- |
| `Scripts/main_slide_generator.py` | Match catalog rows by brand and Client Code, fixing zero matches when searching DMA codes such as ALBGA/ATLGA for XALY/XATL. Legacy market-code matching remains available to existing callers. |
| `Scripts/main_slide_generator.py` | Add `get_rollup_targets()` as the explicit list of 23 report scopes; split GMC XTPC by exact DMA and keep Buick XTPC combined. Use readable blueprint market names and distinct report-code filename prefixes. |
| `Scripts/main_slide_generator.py` | Normalize the already-scoped rollup data to its display name before Executive Summary rendering so a second name filter cannot discard one DMA. |
| `Scripts/main_slide_generator.py` | Query and label YTD as January through the selected end month. Fix chart calls to accept the single returned Slide rather than unpacking a tuple. |
| `Scripts/main_slide_generator.py` | Require the cover, an Executive Summary, and both YTD slides before saving. Catch individual report failures, continue the batch, and include every expected scope in the results. |
| `Scripts/main_slide_generator.py` | Add report identity, file path, and failure details to batch CSV/JSON logs. Use date/time-to-seconds batch folder names. Extend the read-only catalog diagnostic to save a local CSV and show where X codes occur. |
| `Scripts/main_slide_generator.py` | Add optional YTD filtering control; the rollup bypasses spend/volume thresholds so low-volume months contribute. Monthly callers retain their default filtering. |
| `Scripts/executive_summary.py` | Add `preserve_all_tactics`; rollups bypass minimum-spend and strict video-completion exclusions while monthly callers retain defaults. |
| `Scripts/rollup_ui.py` | Show the 23-deck target and brand-specific XTPC rule, explain the separate summary/YTD windows, use the dynamic expected count, and replace deprecated button width syntax. |
| `Scripts/test_rollup_catalog.py` | Add coverage for Client Code matching, multi-DMA rows, exact GMC DMA query filters, combined Buick behavior, missing/failed report scopes, YTD return values, separate time windows, and low-volume January retention. |
| `Button_Rollup.bat` | Launch from the repository root and prefer `.venv/Scripts/python.exe`, falling back to system Python. This also makes generated output paths consistent. |
| `.gitignore` | Exclude the local `.venv`. Existing ignores keep generated decks/logs out of Git. |
| `Documentation/README.md` | Document corrected YTD dates, Client Code selection, 23 expected decks, split GMC XTPC, result logs, and launcher behavior. |
| `Documentation/MICKEY_HANDOFF.md` | Mark the original handoff as historical and point to current documentation. |
| `Documentation/ROLLUP_VALIDATION.md` | Record the investigation, live results, limitations, and local evidence paths. |

The existing `DataQueries` builders already supported Client Code plus optional
Market Code and full-year YTD dates. Those builders did not need changes in this
session. The shared YTD return-value fix also benefits the monthly caller.

## Setup and commands

Run these from the repository root in PowerShell. On a new machine:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r Documentation\requirements.txt
.\.venv\Scripts\python.exe -m streamlit run Scripts\rollup_ui.py
```

Alternatively, double-click `Button_Rollup.bat` after installing dependencies.
The local test environment used Python 3.14 and Streamlit 1.60.0. It was created
with `--system-site-packages` to reuse installed packages; a new checkout can
use a self-contained venv as shown above. Dependencies are not version-pinned.

```powershell
# Regression suite
.\.venv\Scripts\python.exe -m unittest discover -s Scripts -p 'test_*.py' -v

# Read-only live catalog diagnostic; may prompt for Microsoft sign-in
.\.venv\Scripts\python.exe Scripts\main_slide_generator.py --diagnose-rollup-catalog

# Generate the default June-August batch, with January-August YTD
.\.venv\Scripts\python.exe Scripts\main_slide_generator.py --quarter-rollup
```

Connection identifiers remain in `Scripts/settings.py`. Live calls require an
authorized Power BI account and query the existing dataset; no dataset refresh
or SharePoint refresh was performed. A partial batch returns a nonzero CLI exit
status; check the saved results rather than assuming it crashed.

## Tests and evidence

- Full regression suite: **32 tests passed** after the GMC split.
- Streamlit AppTest: startup and partial-result display passed before the final
  count/caption update; the final split was tested through backend generation.
- Original blocker reproduced: live catalog returned rows but zero X-code
  matches in Market Code. Checking Client Code found 21 of 22 brand/client pairs.
- Final local batch: `Generated_Slides/Buick_GMC_Rollup_2026-09-18_11-00-05`.
  It contains 8 Buick and 12 GMC decks. Buick output was retained when replacing
  the combined GMC XTPC deck with two separately generated decks.
- Both GMC XTPC replacements passed saved-slide name and date-label checks.
  Eight captured live queries verified the client and DMA predicates.
- Structural/date-label inspection passed for 19 current decks. Buick Atlanta
  could not be reopened because another process held the file; its saved output
  has not passed that final inspection. No user application was closed.
- Run results: `rollup_results.csv` and `rollup_results.json` in the batch folder.
- Checks: `deck_validation.json` and `xtpc_query_validation.json` in that folder.
- Logs and catalog snapshot: `Generated_Slides/diagnostics/`, including
  `tests_xtpc_final.log`, `xtpc_rebuild.log`, and `rollup_catalog.csv`.
- Superseded combined GMC XTPC deck: `Generated_Slides/diagnostics/superseded/`.
  Earlier trial batches were removed.

Generated decks, snapshots, logs, and the local venv are **not included in the
Git push**. They remain on the originating workstation; another checkout must
regenerate outputs after authentication. A one-off regeneration helper inside
the ignored `.venv` is not part of the supported application.

## Remaining work and next steps

1. Resolve three Buick gaps with the data/report owner: XALY (Albany) and XCLM
   (Columbus) returned no June-August tactic rows; XMAC (Macon) had no Buick
   brand/client catalog entry. Confirm whether these mean no activity or a
   source/mapping issue. Do not invent client codes or fabricate empty decks.
2. Reconcile June-August summaries against the monthly Proof of Performance
   reports and January-August YTD totals against source totals. The monthly
   reports were not supplied, so full numerical reconciliation is outstanding.
3. Review rendered slides visually; structural checks do not prove visual layout.
   Recheck the locked Buick Atlanta deck when it becomes available.
4. Keep the known dates when reproducing this batch. The UI accepts other dates,
   but this session validated the June-August 2026/default YTD case.

Current development branch: `fix/rollup-catalog`. Implementation commit:
`e6c1de3` (`[Logic/Calculation Change] Fix client-scoped rollups, full YTD, and GMC XTPC split`).
This handoff is added in a following documentation commit. Nothing has been
merged into `main` as part of this work.
