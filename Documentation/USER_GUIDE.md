# 📘 User Guide & Configuration for PowerPPTs

This guide is designed for both **new users/developers** looking to run the tool via terminal or IDE, and **AI/IDE Agents** needing to understand the repository's context and development guidelines to collaborate autonomously.

---

## 🎯 What is PowerPPTs?

**PowerPPTs** is a Python-based automation suite designed to transform **Power BI** marketing data into professional, client-ready **PowerPoint (.pptx)** presentations for General Motors (GM: Buick, GMC, Cadillac, and Chevrolet).

---

## 💻 1. Installation and Setup Instructions

Follow these steps to configure the project locally on your system (Windows is the default OS for the project):

### Step 1: Clone the Repository & Open in IDE

You can get the project files on your local machine using either Git terminal, Visual Studio Code (VS Code), or Visual Studio:

#### Option A: Using Git Terminal
```bash
# Clone the repository using Git
git clone https://github.com/sebasluque/PowerPPTsCode_FrontEnd.git

# Navigate into the project folder
cd PowerPPTsCode_FrontEnd
```

#### Option B: Using Visual Studio Code (VS Code)
1. Open **VS Code**.
2. Press `Ctrl + Shift + P` (or `Cmd + Shift + P` on Mac) to open the Command Palette.
3. Type `Git: Clone` and select it.
4. Paste the repository URL: `https://github.com/sebasluque/PowerPPTsCode_FrontEnd.git` and press **Enter**.
5. Choose a local folder where you want to save the project.
6. When prompted, click **Open** (or **Open in new window**) to open the project workspace.

#### Option C: Using Visual Studio
1. Open **Visual Studio**.
2. On the start window, select **Clone a repository**.
3. Enter the Repository URL: `https://github.com/sebasluque/PowerPPTsCode_FrontEnd.git`.
4. Define your local path and click **Clone**.

*Alternatively, you can download the repository as a ZIP from the [GitHub Repository Page](https://github.com/sebasluque/PowerPPTsCode_FrontEnd) and extract it locally.*

---

### Step 2: Prerequisites
Ensure **Python 3.10 or higher** is installed on your system. You can verify this by running:
```bash
python --version
```

### Step 3: Create and Activate a Virtual Environment (Recommended)
It is best practice to isolate dependencies using a virtual environment.

On **Windows (PowerShell/CMD)**:
```powershell
# Create virtual environment named 'venv'
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate
```

On **macOS/Linux**:
```bash
# Create virtual environment named 'venv'
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

---

### Step 4: Install Dependencies
With the virtual environment active, install all required packages:
```bash
pip install -r requirements.txt
```
*Core dependencies installed include: `streamlit`, `pandas`, `numpy`, `python-pptx`, `msal`, and `requests`.*

---

### Step 5: Configure Credentials & IDs
Before running the application for the first time, open the configuration file `Scripts/settings.py` and check that the Power BI identifiers are configured correctly:
- `POWERBI_WORKSPACE_ID`
- `POWERBI_DATASET_ID`
- `POWERBI_CLIENT_ID`

---

### Step 6: Start the Streamlit Application
Run the Streamlit local server from the **root directory** of the repository:
```bash
python -m streamlit run Scripts/app_ui.py
```
Open your browser at the address provided in your terminal (typically [http://localhost:8501](http://localhost:8501)).

> [!NOTE]
> **Power BI Authentication:** The first time you generate a deck, `powerbi_connector.py` uses MSAL interactive authentication. A browser window will prompt you to log in with your GM/Microsoft corporate credentials. Subsequent runs will attempt to reuse the acquired token silently.

---

## 🤖 2. Guidelines for AI/IDE Agents (Gemini, Antigravity, etc.)

If you are an **AI Agent** tasked with modifying, extending, or debugging this codebase, please adhere to the following design specifications and constraints to maintain stability:

### 🏗️ Architecture Blueprint
Understand the role of each script before making edits:

*   **User Interface (UI):** `Scripts/app_ui.py`. Manages parameters, sidebar options, and browser experience.
*   **Orchestration Engine:** `Scripts/main_slide_generator.py`. Coordinates the slide generation workflow (Auth -> Query -> Process -> Render).
*   **Power BI Bridge:** `Scripts/powerbi_connector.py`. Manages OIDC tokens and handles DAX query executions with exponential backoff retries.
*   **Layouts & Design Elements:** `Scripts/slide_components.py` and `Scripts/slide_templates_refactored.py`. Logic for drawing PPTX shapes, tables, donut charts, and positioning objects.
*   **Calculations & KPIs:** `Scripts/measures.py`. Calculates CTR, VCR, CPC, CPA, and determines benchmark styling colors.

### ⚠️ Critical Constraints & Gotchas

1. **No Emojis or Non-ASCII Characters in Logs/Prints (Windows Compatibility):**
   > [!WARNING]
   > Windows terminals run on `cp1252` encoding by default. Writing emojis or extended Unicode characters (e.g., `⚠`, `✓`) inside `print()` statements throws a `UnicodeEncodeError`. Because slide generation loops catch exceptions globally and `continue` to the next step, a console encoding error will cause the generator to **silently skip generating slides**, outputting incomplete decks without clear crash tracebacks.
   > **Rule:** Always use standard ASCII tags for terminal logging, such as `[WARN]`, `[SUCCESS]`, `[OK]`, `[ERROR]`.

2. **Centralized Configuration:**
   Do not hardcode KPI targets, thresholds, or brand palettes directly in Python scripts.
   - Update target performance values in `Scripts/config/benchmarks.json`. If a tactic has an unknown target, use `"TBD"` to color the text black and prevent misleading performance colors.
   - Update brand vehicle and tactic colors in `Scripts/config/vehicle_colors.json`.

3. **Tactic Mapping:**
   When adding a new tactic, you must map the technical DB/Power BI tactic name to a customer-friendly name in `Scripts/tactic_config.py`. The generator will skip tactics that are not recognized in this mapping.

4. **Git Commit Tags:**
   Prefix your commit messages using the following tags to keep a clear history:
   - `[Cosmetic/Visual Change]`: For UI changes, slide design adjustments, assets, or markdown text updates.
   - `[Logic/Calculation Change]`: For query updates, backend engine modifications, mathematical KPI calculations, or settings tweaks.
