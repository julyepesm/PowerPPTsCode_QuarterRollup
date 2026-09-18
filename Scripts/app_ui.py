import streamlit as st
import datetime
import pandas as pd

# Import the orchestrator and the generator function from the long backend
from main_slide_generator import (
    SlideGenerationOrchestrator,
    process_batch_generation,
    process_buick_gmc_quarter_rollup,
)
from filters_manager import GeneralFiltersConfig

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="GM Automation Tool", layout="wide")

# --- CUSTOM CSS (Executive Minimalist & Wide Sidebar) ---
st.markdown("""
    <style>
    /* Panel lateral ligeramente más delgado (350px en lugar de 450px) */
    section[data-testid="stSidebar"] {
        width: 350px !important;
    }
    .stButton>button { 
        background-color: #0078D4; 
        color: white; 
        border-radius: 4px; 
        height: 3em; 
        width: 100%; 
        font-weight: 600;
        border: none;
    }
    div[data-testid="stStatusWidget"] { 
        border: 1px solid #e0e0e0; 
        border-radius: 5px; 
        padding: 10px;
        background-color: #f9f9f9;
    }
    .connection-box {
        font-size: 0.8em;
        color: #555;
        padding: 10px;
        background-color: #f0f2f6;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .field-caption {
        font-size: 0.75rem;
        color: #666;
        margin-top: -15px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- SHARED ORCHESTRATOR (avoids re-authentication on every filter change) ---
def _get_orchestrator():
    """Return a shared SlideGenerationOrchestrator cached in session_state.
    This keeps the MSAL token cache alive across Streamlit reruns so that
    acquire_token_silent succeeds and no new browser tab is opened."""
    if "orchestrator" not in st.session_state:
        st.session_state["orchestrator"] = SlideGenerationOrchestrator(flatten_slides=False)
    return st.session_state["orchestrator"]

# --- DATA LOADER ---
@st.cache_data(ttl=3600, show_spinner="Loading market catalog from Power BI...")
def load_market_catalog():
    gen = _get_orchestrator()
    if not gen.authenticate(): 
        return pd.DataFrame(), None, None
    
    workspace_id = getattr(gen.powerbi, 'workspace_id', "Unknown / Not exposed")
    dataset_id = getattr(gen.powerbi, 'dataset_id', "Unknown / Not exposed")

    query = '''
    EVALUATE
    SELECTCOLUMNS(
        SUMMARIZECOLUMNS(
            'PoP Master Table'[Brand (Reporting)],
            'PoP Master Table'[Zone/LMA],
            'PoP Master Table'[Region],
            'PoP Master Table'[Market Name],
            'PoP Master Table'[Market Code],
            'PoP Master Table'[Client Code]
        ),
        "Brand", 'PoP Master Table'[Brand (Reporting)],
        "Type", 'PoP Master Table'[Zone/LMA],
        "Region", 'PoP Master Table'[Region],
        "MarketName", 'PoP Master Table'[Market Name],
        "MarketCode", 'PoP Master Table'[Market Code],
        "ClientCode", 'PoP Master Table'[Client Code]
    )
    ORDER BY [MarketName]
    '''
    try:
        df = gen.powerbi.execute_dax_query(query)
        if df is not None and not df.empty:
            col_map = {}
            for col in df.columns:
                if "MarketCode" in col: col_map['Code'] = col
                elif "ClientCode" in col: col_map['Client'] = col
                elif "MarketName" in col: col_map['Name'] = col
                elif "Brand" in col: col_map['Brand'] = col
                elif "Type" in col: col_map['Type'] = col
                elif "Region" in col: col_map['Region'] = col
            
            clean_df = pd.DataFrame()
            clean_df['Brand'] = df[col_map['Brand']].fillna("").astype(str).str.strip()
            clean_df['Type'] = df[col_map['Type']].fillna("").astype(str).str.strip()
            clean_df['Region'] = df[col_map['Region']].fillna("").astype(str).str.strip()
            clean_df['MarketName'] = df[col_map['Name']].fillna("").astype(str).str.strip()
            clean_df['MarketCode'] = df[col_map['Code']].fillna("").astype(str).str.strip()
            clean_df['ClientCode'] = df[col_map['Client']].fillna("").astype(str).str.strip() if 'Client' in col_map else ""

            # DEDUPLICATE: One entry per (ClientCode + MarketCode + Brand + Type)
            # This prevents seeing "Augusta" and "Augusta, GA" as two separate selectable markets
            # if they share the same codes.
            clean_df = clean_df.drop_duplicates(subset=['Brand', 'Type', 'MarketCode', 'ClientCode'])

            clean_df = clean_df[
                (clean_df['Brand'] != "") & (clean_df['Brand'].str.lower() != "nan") & 
                (clean_df['Type'] != "") & (clean_df['Type'].str.lower() != "nan")
            ]
            return clean_df, workspace_id, dataset_id
        return pd.DataFrame(), workspace_id, dataset_id
    except Exception as e: 
        st.error(f"Query Error: {e}")
        return pd.DataFrame(), None, None


@st.cache_data(ttl=3600, show_spinner="Filtering markets for selected period...")
def load_markets_for_period(brand, zone_lma, date_iso):
    """
    Load market-client combinations that have actual data for the selected Brand+ZoneLMA+Month.
    Unlike load_market_catalog (which loads all history), this is filtered by date so only
    valid options appear in the market selection list.
    """
    clean_date = date_iso.split("T")[0]
    gen = _get_orchestrator()
    if not gen.authenticate():
        return pd.DataFrame()

    query = f"""
    EVALUATE
    CALCULATETABLE(
        SUMMARIZE(
            'PoP Master Table',
            'PoP Master Table'[Region],
            'PoP Master Table'[Market Name],
            'PoP Master Table'[Market Code],
            'PoP Master Table'[Client Code]
        ),
        'PoP Master Table'[Brand (Reporting)] = "{brand}",
        'PoP Master Table'[Zone/LMA] = "{zone_lma}",
        'Master Date Table'[Month Year] = DATEVALUE("{clean_date}")
    )
    ORDER BY 'PoP Master Table'[Market Name]
    """
    try:
        df = gen.powerbi.execute_dax_query(query)
        if df is not None and not df.empty:
            clean_df = pd.DataFrame()
            for col in df.columns:
                c = col.lower()
                if "region" in c:        clean_df['Region']     = df[col].astype(str).str.strip()
                elif "market name" in c: clean_df['MarketName'] = df[col].astype(str).str.strip()
                elif "market code" in c: clean_df['MarketCode'] = df[col].astype(str).str.strip()
                elif "client code" in c: clean_df['ClientCode'] = df[col].fillna("").astype(str).str.strip()
            if 'MarketCode' in clean_df.columns:
                clean_df = clean_df[
                    (clean_df['MarketCode'] != "") &
                    (clean_df['MarketCode'].str.lower() != "nan")
                ]
            return clean_df
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Could not load markets for selected period: {e}")
        return pd.DataFrame()

# ==============================================================================
#  USER INTERFACE
# ==============================================================================

st.title("GM Automated Slide Generator")

# 1. INITIAL LOAD
catalog, w_id, d_id = load_market_catalog()

if catalog.empty:
    st.error("Connection failed or catalog is empty. Please verify your Power BI access.")
    if st.button("Retry Connection"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

# 2. SIDEBAR
with st.sidebar:
    if st.button("🔄 Reload Power BI Data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"""
        <div class="connection-box">
            <strong>🟢 CONNECTED TO POWER BI</strong><br>
            <b>Workspace:</b><br><code>{w_id}</code><br>
            <b>Dataset:</b><br><code>{d_id}</code><br>
            <i>*To view last refresh time, check Power BI Service.</i>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    brands = sorted(catalog['Brand'].dropna().unique(), key=str)
    sel_brand = st.selectbox("Brand", brands)
    
    available_types = sorted(
        catalog[catalog['Brand'] == sel_brand]['Type'].dropna().unique(),
        key=str
    )
    sel_type = st.selectbox("Tier Type (Zone/LMA)", available_types)
    
    available_regions = sorted(
        catalog[(catalog['Brand'] == sel_brand) & (catalog['Type'] == sel_type)]['Region'].dropna().unique(),
        key=str
    )
    region_options = ["All Regions"] + available_regions
    sel_region = st.selectbox("Region", region_options)

    # Default to the first day of the previous month
    today = datetime.date.today()
    first_of_current = today.replace(day=1)
    last_of_prev = first_of_current - datetime.timedelta(days=1)
    default_report_date = last_of_prev.replace(day=1)

    sel_date = st.date_input("Report Month", default_report_date)
    target_date_iso = sel_date.strftime("%Y-%m-%dT00:00:00")
    
    st.markdown("---")
    summary_only = st.checkbox("Executive Summary Only", value=False)

    st.markdown("#### Vehicle Section")
    include_vehicle_slides = st.checkbox(
        "Include Vehicle Summaries, Insights, and Images",
        value=True,
        help="Uncheck this option to exclude the final vehicle-related slides from the report."
    )
    st.caption(
        "Controls whether vehicle summaries, insights, and images are included in the generated report."
    )

    flatten_slides = st.checkbox("Flatten Slides (Non-editable version)", value=False)
    
    # Centralized Filter Settings Expander
    with st.expander("Filter Settings"):
        st.markdown("#### YTD Thresholds")
        st.caption("Thresholds used only for YTD trend slides.")
        ytd_enabled = st.checkbox(
            "Apply YTD Threshold Filter",
            value=GeneralFiltersConfig.ytd_filter_enabled,
            help="Filter out months below the minimum outcomes or impressions in YTD trend slides."
        )
        col1, col2 = st.columns(2)
        with col1:
            ytd_outcomes = st.number_input(
                "Min YTD Outcomes",
                value=GeneralFiltersConfig.ytd_min_outcomes,
                min_value=0,
                step=10,
                disabled=not ytd_enabled
            )
        with col2:
            ytd_impressions = st.number_input(
                "Min YTD Impressions",
                value=GeneralFiltersConfig.ytd_min_impressions,
                min_value=0,
                step=100,
                disabled=not ytd_enabled
            )

        st.markdown("---")
        st.markdown("#### Historical Settings")
        rolling_months = st.number_input(
            "Historical Window (Months)",
            value=GeneralFiltersConfig.rolling_window_months,
            min_value=1,
            max_value=12,
            step=1,
            help="Number of historical months shown in tactic charts and KBA tables."
        )

        exclude_zero_cost = st.checkbox(
            "Exclude Months Below Spend Threshold",
            value=GeneralFiltersConfig.exclude_zero_cost_months,
            help="If checked, historical months below the configured spend threshold are removed from tactic charts and KBA tables."
        )

        skip_zero_completes = st.checkbox(
            "Skip Video Tactics w/ 0 Completions",
            value=GeneralFiltersConfig.skip_video_tactics_with_zero_completions,
            help="If checked, video tactics with 0 completions and no other activity are skipped (LMA only)."
        )

        st.markdown("---")
        st.markdown("#### Spend Threshold")
        st.caption("Replaces the former zero-cost rule with a configurable minimum.")
        min_tactic_spend = st.number_input(
            "Minimum Aggregated Spend (USD)",
            value=GeneralFiltersConfig.min_tactic_spend,
            min_value=0.0,
            step=10.0,
            format="%.2f",
            help="Applied after aggregating each Tactic + Site + Audience combination. Below-threshold combinations are excluded from Summary and enabled historical filtering; current tactic slides are retained only when performance exists and are logged as anomalies. The threshold value itself is included."
        )
    st.markdown("---")
    st.subheader("Market Selection")

    # Load only markets that have data for the selected Brand + Type + Date
    period_df = load_markets_for_period(sel_brand, sel_type, target_date_iso)
    if sel_region != "All Regions" and not period_df.empty:
        period_df = period_df[period_df['Region'] == sel_region]
    filtered_df = period_df
    if not filtered_df.empty:
        # ====== TYPE-AWARE DEDUPLICATION ======
        if sel_type == "ZONE":
            # ZONE: One entry per MarketCode (merge all client codes)
            deduped_df = filtered_df.drop_duplicates(subset=['MarketCode']).sort_values(by='MarketName')
            raw_options = deduped_df.apply(lambda row: f"{row['MarketCode']} | {row['MarketName']}", axis=1).tolist()
        else:
            # LMA: One entry per ClientCode, unless a client has multiple MarketCodes
            client_market_counts = filtered_df.groupby('ClientCode')['MarketCode'].nunique()
            multi_market_clients = set(client_market_counts[client_market_counts > 1].index)
            
            raw_options = []
            seen_keys = set()
            for _, row in filtered_df.sort_values(by='MarketName').iterrows():
                c = row['ClientCode']
                m = row['MarketCode']
                if c in multi_market_clients:
                    key = (c, m)
                    label = f"{c} | {m} | {row['MarketName']}"
                else:
                    key = (c,)
                    label = f"{c} | {m} | {row['MarketName']}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    raw_options.append(label)
        
        market_options = list(dict.fromkeys(raw_options))
    else:
        market_options = []
    
    mode = st.radio("Selection Mode:", ["Manual Selection", "All Markets"])
    final_selection = []
    
    if mode == "Manual Selection": 
        final_selection = st.multiselect("Select markets to process", market_options)
        final_selection = list(dict.fromkeys(final_selection))
        if sel_type == "ZONE":
            st.caption("`MARKET CODE | MARKET NAME`")
        else:
            st.caption("`CLIENT CODE | MARKET CODE | MARKET NAME`")
    else:
        if market_options: 
            st.info(f"Processing {len(market_options)} markets from the selected region.")
            final_selection = market_options

# 3. MAIN AREA
st.subheader("June-August 2026 Rollup")
st.caption("Generates 22 Executive Summary decks: 11 markets for Buick and GMC.")
if st.button("GENERATE 22 ROLLUP DECKS", type="secondary"):
    with st.spinner("Generating Buick and GMC June-August rollups..."):
        rollup_result = process_buick_gmc_quarter_rollup(
            flatten_slides=flatten_slides
        )
    if rollup_result.get("errors", 1) == 0:
        st.success(
            f"Generated {rollup_result['successful_decks']} decks in "
            f"`{rollup_result['output_folder']}`"
        )
    else:
        st.warning(
            f"Generated {rollup_result.get('successful_decks', 0)} of "
            f"{rollup_result.get('expected_decks', 22)} decks."
        )
        st.dataframe(pd.DataFrame(rollup_result.get("details", [])))

st.info(f"**Ready to generate:** {sel_brand} | {sel_type} | {len(final_selection)} Markets Selected")

if st.button("GENERATE REPORTS", type="primary"):
    if not final_selection:
        st.warning("Please select at least one market before continuing.")
    else:
        codes_data = []
        display_map = {} 
        
        # Pre-detect duplicated client codes to avoid filename collisions
        if sel_type != "ZONE":
            _cc_counts = {}
            for x in final_selection:
                parts = x.split(" | ")
                if len(parts) >= 3:
                    _cc_counts[parts[0].strip()] = _cc_counts.get(parts[0].strip(), 0) + 1
        else:
            _cc_counts = {}
        
        for x in final_selection:
            parts = x.split(" | ")
            
            if sel_type == "ZONE":
                # Format: "MARKET_CODE | MARKET_NAME"
                if len(parts) >= 2:
                    m_code = parts[0].strip()
                    m_name = parts[1].strip()
                else:
                    continue
                # Collect client codes active for this market code in the selected period
                market_rows = filtered_df[filtered_df['MarketCode'] == m_code]
                all_clients = market_rows['ClientCode'].dropna().unique().tolist()
                all_clients = [c for c in all_clients if c and c.lower() != 'nan']
                c_code = all_clients if len(all_clients) > 1 else (all_clients[0] if all_clients else "")
                prefix = m_code
            else:
                # Format: "CLIENT_CODE | MARKET_CODE | MARKET_NAME"
                if len(parts) >= 3:
                    c_code = parts[0].strip()
                    m_code = parts[1].strip()
                    m_name = parts[2].strip()
                else:
                    continue
                prefix = f"{c_code}-{m_code}" if _cc_counts.get(c_code, 1) > 1 else c_code
                
            codes_data.append({"client": c_code, "market": m_code, "name": m_name, "prefix": prefix})
            # Use composite key (m_code, c_code) so markets sharing the same market_code
            # each get their own display label. ZONE type uses m_code alone (bundles all clients).
            if sel_type == "ZONE":
                display_map[m_code] = x
            else:
                display_map[(m_code, c_code)] = x
        

        progress_bar = st.progress(0)
        status_text = st.empty()
        log_expander = st.expander("Processing Log", expanded=True)
        log_container = log_expander.container()
        
        try:
            generator = process_batch_generation(
                target_date_iso, sel_brand, sel_type, codes_data, summary_only, flatten_slides,
                is_ytd=ytd_enabled,
                ytd_min_outcomes=ytd_outcomes,
                ytd_min_impressions=ytd_impressions,
                rolling_window_months=rolling_months,
                exclude_zero_cost_months=exclude_zero_cost,
                skip_video_tactics_with_zero_completions=skip_zero_completes,
                min_tactic_spend=min_tactic_spend,
                include_vehicle_slides=include_vehicle_slides
            )
            
            for update in generator:
                msg_type = update.get("type")
                
                # Extraemos la cadena visual completa (Si no la encuentra, usa el código por defecto)
                m_code = update.get("code")
                c_code = update.get("client", "")
                # Convert list to tuple so it can be used as a dict key (ZONE markets may have multiple client codes)
                c_code_key = tuple(c_code) if isinstance(c_code, list) else c_code
                # Composite key for LMA (market+client), simple key for ZONE
                display_str = display_map.get((m_code, c_code_key), display_map.get(m_code, m_code)) if m_code else "Unknown"
                
                if msg_type == "start":
                    status_text.markdown("**Status:** Initializing connection and validating data...")
                elif msg_type == "step_start":
                    progress = update["index"] / len(codes_data)
                    progress_bar.progress(progress)
                    # Usamos la triada completa aquí
                    status_text.markdown(f"Processing: **{display_str}** ({update['index'] + 1}/{len(codes_data)})")
                elif msg_type == "step_success":
                    # Y también la usamos en el log de éxito
                    log_container.write(f"✅ **{display_str}** - Completed successfully")
                elif msg_type == "step_fail":
                    # Y en el log de fallo
                    log_container.write(f"❌ **{display_str}** - Failed: {update['reason']}")
                elif msg_type == "complete":
                    progress_bar.progress(100)
                    status_text.success("Batch completed!")
                    
                    if update["errors"] > 0:
                        st.warning(f"Process finished with {update['errors']} errors. Check the table below.")
                        st.dataframe(pd.DataFrame(update["details"]))
                    else:
                        st.success(f"Full success! All reports were saved in the folder: `{update['output_folder']}`")

        except Exception as e:
            st.error(f"Critical Error during execution: {e}")
