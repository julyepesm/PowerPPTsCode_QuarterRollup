# 📊 PowerPPTs: GM Automation Tool

For the current rollup requirements, all changes, setup, tests, and remaining
work, start with [CURRENT_HANDOFF.md](CURRENT_HANDOFF.md).

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)

**PowerPPTs** is a state-of-the-art automation suite designed to transform Power BI data into professional, presentation-ready PowerPoint reports. With a sleek user interface and a robust backend, it streamlines the monthly reporting workflow for GM brands.

---

## ✨ Key Features

*   **🚀 One-Click Generation:** Generate full metric decks or individual slides with a single click.
*   **📂 Batch Processing:** Process multiple markets, brands, and regions in parallel.
*   **📊 Dynamic Charts:** Automated YTD KBA and Impression breakdown charts.
*   **🎨 Brand-Specific Styling:** Automatic applying of Buick, GMC, Cadillac, and Chevrolet themes.
*   **🔍 Centralized Configuration:** Easily manage credentials, benchmarks, and colors from a single source.
*   **🛡️ Error Handling:** Integrated anomaly detection and error summary slides.
*   **🔒 Slide Flattening:** Optional UI toggle to flatten slides to non-editable images for smaller file sizes and content protection.

---

## 🛠️ Getting Started

### 1. Prerequisites
Ensure you have **Python 3.10** or higher installed on your system.

### 2. Installation
Clone the repository and install the required libraries:

```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Launching the App
Run the Streamlit interface from the root directory:

```bash
# Start the application
python -m streamlit run Scripts/app_ui.py
```

Open your browser at [http://localhost:8501](http://localhost:8501).

### 4. Reusable Executive Summary rollup

Run `Button_Rollup.bat` and open `http://localhost:8502`, or run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run Scripts/rollup_ui.py
```

1. Choose **Month range** or **Quarter** (Q1-Q4 plus year).
2. Choose **Brand** (Buick, GMC, Cadillac, or Chevrolet) and **Tier** (LMA/ZONE).
3. Click **Load markets**. Complete Microsoft device-code sign-in using the
   link and code shown on the page if prompted.
4. Choose a **Region**, or **All regions**.
5. Select specific **Markets**, or click **Select all**. Click **Generate rollup decks**.

Executive Summaries cover the selected months. YTD slides always start in
January of the selected end year and run through the end month. Market discovery
covers the whole selected period, including activity in its first month only.
Changing the dates, brand, or tier requires loading the matching catalog again.

Buick XTPC stays combined. GMC XTPC-PANFL and XTPC-TALFL remain separate.
The UI lists available market scopes for the selected period, so its deck count
is determined by the markets you choose rather than a fixed 23-deck target.

See [REUSABLE_ROLLUP.md](REUSABLE_ROLLUP.md) for scope rules, logs, and testing.
The original fixed June-August 23-scope batch is still available separately:

```powershell
.\.venv\Scripts\python.exe Scripts/main_slide_generator.py --quarter-rollup
```

---

## ⚙️ Configuration & Maintenance

The project uses a **Centralized Configuration System** to ensure consistency and ease of use.

### 📍 Settings (`Scripts/settings.py`)
This is the "Brain" of the application. Use it to configure:
*   **Power BI IDs:** Workspace, Dataset, and Client IDs.
*   **Brand Themes:** Color palettes and typography.
*   **Asset Paths:** Where slides are saved and logos are stored.

### 📂 External Configuration Files (`Scripts/config/`)
All dynamically loaded data structures are stored in JSON format within the `Scripts/config` directory so they can be modified without altering Python code.

*   **`benchmarks.json`**: Modify this file to update the performance targets for each tactic and audience segment.
*   **`vehicle_colors.json`**: Managed color palettes for both specific **vehicle models** and **tactics** (FEP, Meta, etc.) across all GM brands.
*   **`vehicle_images.json`**: Canonical vehicle taxonomy, Power BI aliases, generation/exclusion policy, and image paths used by vehicle Insights/Summary slides. Approved models without an image render `NO IMAGE CAR`; excluded or unknown values are reported as anomalies.
*   **`normalization_rules.json`**: Regular expressions and mapping rules used to clean and standardize raw data text.
*   **`discovery_log.json`**: Auto-generated log file tracking dynamic data discoveries across runs.


---

## 🏗️ Architecture Overview

| Component | Responsibility |
| :--- | :--- |
| **`app_ui.py`** | The Streamlit-based graphical user interface. |
| **`main_slide_generator.py`** | The Orchestrator that coordinates data and templates. |
| **`powerbi_connector.py`** | Handles MSAL Authentication and DAX query execution. |
| **`slide_templates_refactored.py`** | Logic for building and styling PowerPoint slides. |

---

## 🤝 Contribution Guidelines

To keep the codebase clean, please follow these rules:

1.  **Branching:** Always create a new branch for changes.
2.  **Commit Tags:**
    *   `[Cosmetic/Visual Change]` for UI/CSS/Text updates.
    *   `[Logic/Calculation Change]` for Backend/DAX/Power BI logic.
3.  **Context:** Always explain **why** a change was made in the commit message.

---

*Developed for GM's Digital Marketing Automation.*
