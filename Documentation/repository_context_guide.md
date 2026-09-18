# 📘 Repository Context Guide: GM PowerPPTs Automation

This document serves as a quick-start guide for AI agents and developers to understand the **PowerPPTs** codebase, its architecture, and recent feature implementations.

## 🎯 Project Overview
**PowerPPTs** is a Python-based automation tool designed to generate professional PowerPoint reports for General Motors (GM) brands (Buick, GMC, Cadillac, Chevrolet) by fetching data from Power BI.

- **Primary Stack**: Python 3.10+, Streamlit (UI), `python-pptx`, MSAL (Authentication).
- **Data Source**: Power BI Service via DAX queries.

---

## 🏗️ Core Architecture & Components

| Component | File | Responsibility |
| :--- | :--- | :--- |
| **UI** | `app_ui.py` | Streamlit interface for user parameters (Brand, Market, Month). |
| **Orchestrator** | `main_slide_generator.py` | Coordinates the flow: Auth -> Query -> Process -> Render. |
| **Data Bridge** | `powerbi_connector.py` | Handles MSAL token acquisition and DAX execution. |
| **Query Engine** | `data_queries.py` | Generates DAX query strings for different report sections. |
| **Logic/Calc** | `measures.py` | Calculates KPIs (CTR, VCR, CPA, CPC) and handles benchmark color-coding. |
| **Layouts** | `slide_layouts.py` | Defines precise X, Y coordinates for all slide elements. |
| **Templates** | `slide_templates_refactored.py` | High-level blueprints for Title, Data, and Summary slides. |
| **Components** | `slide_components.py` | Low-level drawing functions for tables, donut charts, and shapes. |

---

## 🔄 Data Lifecycle
1. **Selection**: User selects Brand/Market/Month in `app_ui.py`.
2. **Authentication**: `powerbi_connector.py` acquires an OIDC token via Service Principal.
3. **Discovery**: `main_slide_generator.py` calls `data_queries.py` to find available tactics/sites.
4. **Iterative Generation**:
   - The engine loops through each tactic/audience combination.
   - For each combination, a detailed DAX query is executed.
   - `measures.py` processes raw data into displayable KPIs.
   - `slide_templates_refactored.py` dictates the slide structure.
5. **Finalization**: Error summary slide is added, and the `.pptx` is saved/flattened.

---

## 🚀 Recent Critical Features (April 2026)

### 1. Summary Splits by Audience
The Executive Summary now generates **multiple slides** instead of one, splitting data by Audience (e.g., GEN, HIS, ASN).
- **Location**: `main_slide_generator.py` inside `_add_executive_summary_slide`.
- **Logic**: Groups raw metrics by `Audience_Clean` and renders a dedicated summary dashboard for each non-empty group.

### 2. TBD Override Logic for Benchmarks
When a performance target is unknown for a new tactic/brand, the system supports a "TBD" mode.
- **Location**: `measures.py` within `add_benchmarks_and_colors` and `Benchmarks` class.
- **Behavior**: If the JSON benchmark file contains `"TBD"`, the UI displays "TBD" as the goal and applies **black** text coloring instead of Red/Green, preventing misleading performance indications.

### 3. Display Tactic Resolution
Shared logic in `display_resolution.py` (and mirrored in `tactic_config.py`) that separates generic "Display" into "BT Display", "Retargeting Display", or "Consideration Display" based on the `Strategy` column.

---

## 🛠️ Key Commands & Configuration
- **Run App**: `python -m streamlit run Scripts/app_ui.py`
- **Settings**: `Scripts/settings.py` (Tenant IDs, Dataset IDs, Brand Themes).
- **Dynamic Config**: `Scripts/config/*.json` (Manual overrides for colors, benchmarks, and naming rules).

---

## ⚠️ Important Gotchas
- **Unicode Encoding**: Windows console defaults to `cp1252`. Avoid printing Emojis (e.g., ⚠, ✓) as they cause `UnicodeEncodeError` which can silently crash the slide generation loop.
- **Tactic Mapping**: Always check `tactic_config.py` when adding new tactics. The name in the source data MUST be mapped to a reporting name for the generator to pick it up.
- **Coordinate System**: Layouts in `slide_layouts.py` are in Inches. Modification requires manual adjustment of these values.

---
*Created by Antigravity (Google DeepMind) on April 16, 2026.*
