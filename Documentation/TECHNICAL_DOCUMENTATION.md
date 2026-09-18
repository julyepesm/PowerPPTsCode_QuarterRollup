# Ã°Å¸â€œâ€“ Technical Documentation Ã¢â‚¬â€œ April 2026 Version
**GM Automated Slide Generator**

## 1. Summary Table

| Script Name | Short Description | Main Role |
| :--- | :--- | :--- |
| `app_ui.py` | Main User Interface. | The window you see in the browser to run reports. |
| `main_slide_generator.py` | Core orchestrator and engine. | Coordinates all steps to create the PPTX deck. |
| `powerbi_connector.py` | Power BI API bridge. | Connects and authenticates with the Power BI Service. |
| `data_queries.py` | DAX Query builder. | Creates the code to ask Power BI for specific metrics. |
| `brand_configurations.py` | Visual asset manager. | Handles logos and colors for each brand. |
| `tactic_config.py` | Name mapping rules. | Translates internal database names to reporting names. |
| `measures.py` | KPI Calculator. | Calculates totals, CTR, CPC, and conversion rates. |
| `benchmarks.py` | Goal data loader. | Manages target/benchmark values for the charts. |
| `slide_templates_refactored.py` | Slide layout logic. | Decides the content of every slide in the final deck. |
| `slide_components.py` | Low-level drawing tool. | Draws tables, donut charts, and lines on the PPTX. |
| `slide_layouts.py` | Position coordinates. | Defines where every icon and text box is placed. |
| `executive_summary.py` | Summary slide logic. | Handles the complex logic for the 1st dashboard slide. |
| `ytd_charts_refactored.py` | Year-Trend chart logic. | Builds historical trend charts (KBA & Impressions). |
| `vehicle_catalog.py` | Vehicle taxonomy loader. | Resolves JSON aliases to canonical models and configured image paths. |
| `vehicle_insights_summary.py` | Vehicle dashboard logic. | Filters active models, resolves model images, and builds Insights/Summary slide pairs. |
| `error_collector.py` | Anomaly tracker. | Records data errors for the final report. |
| `flatten_pptx.py` | PPTX Optimizer. | Converts slides to static images (non-editable). |
| `display_resolution.py` | Sizing helper. | Adjusts text and box sizes for optimal display. |
| `glossary.py` | Glossary generator. | Adds the definition slide at the end of the deck. |
| `settings.py` | Environment config. | Stores Workspace IDs and API credentials. |
| `utils.py` | Helper functions. | General tools used by almost every script. |

---

## 2. External Configuration Files (`Scripts/config/`)

All dynamically loaded data structures are stored in JSON format within the `Scripts/config` directory so they can be modified without altering Python code.

*   **`benchmarks.json`**: Modify this file to update the performance targets for each tactic and audience segment.
*   **`vehicle_colors.json`**: Managed color palettes for both specific **vehicle models** and **tactics** (FEP, Meta, etc.) across all GM brands.
*   **`vehicle_images.json`**: Single source of vehicle canonical names, Power BI aliases, taxonomy policy, and Insights/Exec image paths. Aliases are grouped before spend filtering. `generate_slides: false` entries and unmapped values are excluded with an anomaly; approved entries with null/missing images render `NO IMAGE CAR`.
*   **`normalization_rules.json`**: Regular expressions and mapping rules used to clean and standardize raw data text.
*   **`discovery_log.json`**: Auto-generated log file tracking dynamic data discoveries across runs.
*   **`general_filters.json`**: Centralizes runtime filter values such as YTD thresholds, historical window size, spend-threshold behavior, video-completions rules, and the minimum aggregated spend threshold.

---

## 3. Script Details

### `app_ui.py`
1. **Description & Purpose:** It is the primary interface. It creates the sidebar and buttons you use to select the brand, month, and markets.
2. **When to Edit or Run:** Run this script to start the tool. Edit it if you need to add new user filters or change the look of the sidebar.
3. **Connections & Dependencies:** It sends user selections and commands to `main_slide_generator.py`.
4. **Filter UI Notes:** The sidebar now includes a configurable `Minimum Aggregated Spend (USD)` field so users can set a minimum aggregated spend threshold before a tactic is included in slides or executive summary output.

### `main_slide_generator.py`
1. **Description & Purpose:** It is the 'Engine' of the project. It coordinates the entire workflow: logging into Power BI and calling builders.
2. **When to Edit or Run:** Edit this file if you want to change the order of the slides or the logic for selecting valid tactics.
3. **Connections & Dependencies:** It connects to `powerbi_connector.py`, `data_queries.py`, and all slide components.
4. **Filtering Logic:** Applies the current-month spend threshold, the optional historical spend-threshold filter, the video-completion skip rule, and YTD metric thresholds. Current tactic slides below the spend threshold are kept only when they have performance, in which case an anomaly is recorded.

### `powerbi_connector.py`
1. **Description & Purpose:** This script handles all communication with Power BI. It uses 'Service Principal' authentication.
2. **When to Edit or Run:** Edit it only if your authentication method changes or if the Power BI API URL is updated.
3. **Connections & Dependencies:** Used by `app_ui.py` and `main_slide_generator.py` to fetch the raw data.

### `data_queries.py`
1. **Description & Purpose:** It is the 'Query Book'. It contains the logic to write DAX queries for Power BI.
2. **When to Edit or Run:** Edit this file if you need to fetch a new column or change the logic of the Market Metadata query.
3. **Connections & Dependencies:** It is called by `main_slide_generator.py` whenever the machine needs data.

### `brand_configurations.py`
1. **Description & Purpose:** It manages the visual identity. Colors, fonts, and the locations of PNG logos are stored here.
2. **When to Edit or Run:** Edit this file if a brand changes its corporate colors or if you get a new logo file.
3. **Connections & Dependencies:** Used by any script that needs to 'paint' something (like `slide_templates_refactored.py`).

### `measures.py`
1. **Description & Purpose:** It is the 'Calculator'. It calculates percentages and dollar values like Cost per Click (CPC) or VCR.
2. **When to Edit or Run:** Edit this script if the client changes the definition of a metric calculation.
3. **Connections & Dependencies:** It processes the data frames returned by `data_queries.py`.

### `tactic_config.py`
1. **Description & Purpose:** It handles Name Translation. It tells the app to write 'Meta Display' instead of 'Social_FB'.
2. **When to Edit or Run:** Edit this file whenever a new tactic is created in the source data that the app doesn't recognize.
3. **Connections & Dependencies:** Essential for `main_slide_generator.py` and `executive_summary.py`.

### `benchmarks.py`
1. **Description & Purpose:** This script loads the target values (benchmarks) from a JSON file.
2. **When to Edit or Run:** Edit this if you add new KPIs that need a goal or benchmark comparison in the charts.
3. **Connections & Dependencies:** It provides data to `executive_summary.py` and `slide_components.py`.

### `slide_templates_refactored.py`
1. **Description & Purpose:** This script holds the 'Design Blueprints' for every slide in the presentation.
2. **When to Edit or Run:** Edit this if you want to add a new slide type or change the general arrangement of a slide.
3. **Connections & Dependencies:** Highly dependent on `slide_components.py` for drawing.

### `slide_components.py`
1. **Description & Purpose:** These are the low-level 'Building Blocks'. It has code to draw tables, donut charts, and text boxes.
2. **When to Edit or Run:** Edit this if you want to change the visual theme (e.g. font size or chart colors).
3. **Connections & Dependencies:** Imported by `slide_templates_refactored.py` and `executive_summary.py`.

### `slide_layouts.py`
1. **Description & Purpose:** This is the 'Coordinate Map'. It stores the exact X, Y positions for every element on a slide.
2. **When to Edit or Run:** Edit this if you need to move a chart to the left or resize a title box.
3. **Connections & Dependencies:** Used by `slide_components.py` to place drawings on the page.

### `executive_summary.py`
1. **Description & Purpose:** This specialized script builds the Dashboard (the first data slide).
2. **When to Edit or Run:** Modify this if you want to change which KPIs are shown on the dashboard cards.
3. **Connections & Dependencies:** Called by `main_slide_generator.py` during the generation loop.
4. **Filtering Logic:** Applies the same spend threshold used in tactic slides to the executive summary. Tactics below the minimum are removed and logged as anomalies to keep the summary consistent with the slide generation rules.

### `ytd_charts_refactored.py`
1. **Description & Purpose:** It handles the historical trend charts (Year-to-Date) for KBA and Impressions.
2. **When to Edit or Run:** Edit this if the YTD charts are showing the wrong dates or colors.
3. **Connections & Dependencies:** Works with `data_queries.py` to get historical data.

### `error_collector.py`
1. **Description & Purpose:** It tracks anomalies during generation (e.g. $0 cost tactics with impressions, or tactics below the configured spend threshold).
2. **When to Edit or Run:** Edit this if you want the generator to detect and report on a new type of data problem.
3. **Connections & Dependencies:** It shares an 'Error List' with `main_slide_generator.py`.

### `flatten_pptx.py`
1. **Description & Purpose:** An optional tool that converts editable charts into static images for security.
2. **When to Edit or Run:** Enable this in the UI if the client requests non-editable reports.
3. **Connections & Dependencies:** This is a post-generation step.

### `display_resolution.py`
1. **Description & Purpose:** It calculates text sizes to prevent names from bleeding out of boxes on different screens.
2. **When to Edit or Run:** Edit this if text on the slides looks too crowded or overlapping.
3. **Connections & Dependencies:** Used inside `slide_components.py`.

### `glossary.py`
1. **Description & Purpose:** It automatically creates the definition slide at the end of the deck.
2. **When to Edit or Run:** Edit this if you add a new KPI to the reports that needs a definition.
3. **Connections & Dependencies:** Used at the very end of the process.

### `settings.py`
1. **Description & Purpose:** Storage room for Workspace IDs, Dataset IDs, and API credentials.
2. **When to Edit or Run:** Edit this first before running the app for the first time or if IDs change.
3. **Connections & Dependencies:** Imported by almost every script to get configuration.

### `utils.py`
1. **Description & Purpose:** A library of helper tools for filenames, column search, and date formatting.
2. **When to Edit or Run:** Edit it to add a generic function that will be useful in multiple other scripts.
3. **Connections & Dependencies:** The glue of the project; used everywhere.

---

## 4. Hardcoded Logic Audit (April 2026)

While the `Scripts/config/` directory aims to centralize dynamic data structures, several hardcoded rules and mappings still exist directly within the Python scripts. Ideally, these should be reviewed for migration to external JSON files for maximum maintainability.

### 1. `tactic_config.py`
*   **Metric & Structure Definitions:** Dictionaries inside `_get_benchmark_structure`, `_build_metric_definitions`, and `_build_chart_configurations` map each tactic to its KPIs and component charts directly in-code.
*   **Static Values:** The `_get_formatted_benchmark` function enforces hardcoded text rules (e.g., forcing `Viewability` strings to return `">70%"` and `YT Viewability` to `">90%"`).

### 2. `main_slide_generator.py` & `executive_summary.py`
*   **Sorting & Sub-sorting:** If sorting ranks aren't found in `normalization_rules.json`, the engine defaults to a hardcoded dict (`{'FEP': 10, 'PreRoll': 30, ...}`). Furthermore, `FEP` sub-sorting for sites like `EMRGE` and `MSP` is exclusively hardcoded inside the `get_tactic_rank` logic.
*   **Strict Filtering:** Tactical exclusion rules for empty charts (`strict_video_tactics = ['FEP', 'YouTube']`) are hardcoded.

### 3. `slide_components.py`
*   **Visual Display Overrides:** In `create_tactic_cards`, the dictionary `display_title_overrides = {"BT Display": "InMarket Display"}` forcefully modifies the final slide title at render time.
*   **Brand Style Anchors:** Brand background layouts (like `BRAND_BACKGROUNDS` with specific RGB objects and transparency mappings) and header colors (`BRAND_HEADERS`) are hardcoded inside the component generator rather than being inherited exclusively from `brand_configurations.py`.
*   **Slide Alignment:** Pixel positioning grids and specific column widths depending on 3-box or 4-box designs are hardcoded (e.g., `x_positions`, `box_width`).

### 4. `measures.py` & `benchmarks.py`
*   **KPI Switching:** Functions like `get_kpi_label` and `select_kpi_value` use static mappings (switch/dictionary blocks) instead of parsing centralized KPI structures.
*   **KPI Direction:** The directional determination of metrics (e.g., lower-is-better for `CPA`, `CPCV` versus higher-is-better for `VCR`, `ACR`) is deeply embedded within Python blocks.

---

## 5. Known Issues & Troubleshooting

### Windows Console Unicode Encoding
**Issue:** If the generator inexplicably stops working and skips slides (outputting only the Title and Executive Summary without any crash traceback), it may be due to a hidden `UnicodeEncodeError` escaping the slide generation loop `try/except` blocks.

**Cause:** By default, Windows standard terminals run on the `cp1252` encoding (charmap) which does not support emojis or complex Unicode symbols. If any Python `print()` statement contains characters like `Ã¢Å¡Â ` (`\u26a0`) or `Ã¢Å“â€œ` (`\u2713`), Python will throw an unhandled `UnicodeEncodeError` when emitting the logs. Since slide iterations are wrapped in `try` blocks that use `continue` on exception, this silent console error forcibly terminates the creation of that particular slide iteration.

**Prevention:** 
*   **Do not use emojis** or extended Unicode symbols in your logging or `print()` statements.
*   Always use safe, standard ASCII alternatives like `[WARN]`, `[OK]`, `[FAIL]`, and `[ERROR]`.
*   If running the app as a background service or through Streamlit UI, the standard output streams might inherit default shell encodings. Sticking to plain ASCII strings ensures ultimate compatibility and avoids silent generation failures.

---

## 6. Technical Debt & Future Improvements

### Global State Mutation in Concurrent Environments (Streamlit)
*   **Context:** In `main_slide_generator.py`, the batch processing function updates filters by calling `GeneralFiltersConfig.update_batch({...})`.
*   **Risk:** Since this configuration relies on static class-level variables (`cls.min_tactic_spend`), if the application is accessed by multiple concurrent users on the same server, configurations will collide, leading to unexpected or incorrect filtering behavior.
*   **Suggested Improvement:** Pass configuration variables through Streamlit's native `st.session_state`, or instantiate unique configuration objects passed by reference throughout the workflow to avoid static class-level global variables.

### Implicit Dependency on Relative Paths
*   **Context:** The `load_config` method in `filters_manager.py` searches for the configuration file using `os.path.join("Scripts", "config", "general_filters.json")`.
*   **Risk:** If the application (`app_ui.py`) is run from any directory other than the strict project root (e.g., if a user navigates to `Scripts` before running the app), the application will fail to find the JSON configuration file and will silently fall back to hardcoded default values.
*   **Suggested Improvement:** Anchor route resolution to the physical location of the module file using absolute paths: `BASE_DIR = os.path.dirname(os.path.abspath(__file__))`.
