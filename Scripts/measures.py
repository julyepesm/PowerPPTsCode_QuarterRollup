
import math
import pandas as pd
def calculate_metrics(df):
    """Calculate derived metrics from raw data"""
    if df is None or df.empty:
        return df
        
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Helper to find column regardless of table prefix (uses shared utility)
    from utils import find_column as _find_column
    def find_col(name):
        return _find_column(df, name)

    # Normalization: Rename columns to remove table prefixes for easier access
    cols_to_normalize = [
        'Total Cost', 'Impressions', 'Video Completions', 'Video Plays', 
        'Clicks', 'Total Conversions', 'Audio Completes', 'Audio Starts',
        'Unique Viewable Impressions', 'Unique Measured Impressions',
        'Active View: Viewable Impressions', 'Active View: Measurable Impressions'
    ]
    
    rename_map = {}
    for col_name in cols_to_normalize:
        found = find_col(col_name)
        if found:
            rename_map[found] = f"[{col_name}]" # Standardize to bracketed version used in code
            
    if rename_map:
        df = df.rename(columns=rename_map)

    # VCR (Video Completion Rate)
    v_comp = '[Video Completions]'
    v_play = '[Video Plays]'
    if v_comp in df.columns and v_play in df.columns:
        df['VCR'] = df.apply(
            lambda row: row[v_comp] / row[v_play] 
            if row[v_play] > 0 else 0, 
            axis=1
        )
    
    # CPCV (Cost Per Completed View)
    cost = '[Total Cost]'
    if cost in df.columns and v_comp in df.columns:
        df['CPCV'] = df.apply(
            lambda row: row[cost] / row[v_comp] 
            if row[v_comp] > 0 else 0, 
            axis=1
        )
    
    # CPA (Cost Per Action) - using Total Conversions
    conv = '[Total Conversions]'
    if cost in df.columns and conv in df.columns:
        df['CPA'] = df.apply(
            lambda row: row[cost] / row[conv] 
            if row[conv] > 0 else 0, 
            axis=1
        )
    
    # CPC (Cost Per Click)
    clicks = '[Clicks]'
    if cost in df.columns and clicks in df.columns:
        df['CPC'] = df.apply(
            lambda row: row[cost] / row[clicks] 
            if row[clicks] > 0 else 0, 
            axis=1
        )
    
    # ACR (Audio Completion Rate)
    a_comp = '[Audio Completes]'
    a_start = '[Audio Starts]'
    if a_comp in df.columns:
        df['ACR'] = df.apply(
            lambda row: row[a_comp] / row.get(a_start, 1) 
            if row.get(a_start, 0) > 0 else 0, 
            axis=1
        )
    
    # Viewability
    u_view = '[Unique Viewable Impressions]'
    u_meas = '[Unique Measured Impressions]'
    if u_view in df.columns and u_meas in df.columns:
        df['Viewability'] = df.apply(
            lambda row: row[u_view] / row[u_meas]
            if row[u_meas] > 0 else None,
            axis=1
        )
    
    # YT Viewability
    yt_view = '[Active View: Viewable Impressions]'
    yt_meas = '[Active View: Measurable Impressions]'
    if yt_view in df.columns and yt_meas in df.columns:
        df['YT Viewability'] = df.apply(
            lambda row: row[yt_view] / row[yt_meas]
            if row[yt_meas] > 0 else None,
            axis=1
        )
    
    return df
def generate_data_label(brand_name, zone_lma_type, month_year):
    """
    Generate data label matching Power BI DAX logic
    
    Args:
        brand_name: Brand name (e.g., 'GMC', 'Chevrolet')
        zone_lma_type: Either 'ZONE' or 'LMA'
        month_year: Month and year string (e.g., 'August 2025')
    
    Returns:
        Formatted label string (e.g., 'Source: GMC LMA August 2025')
    """
    # Handle brand name
    if not brand_name or str(brand_name).strip() == "":
        brand_display = "No Brand Selected"
    else:
        brand_display = str(brand_name).upper()
    
    # Handle zone/LMA type
    if not zone_lma_type or str(zone_lma_type).strip() == "":
        tier_display = "ZONE"  # Default
    else:
        tier_clean = str(zone_lma_type).upper().strip()
        if "LMA" in tier_clean:
            tier_display = "LMA"
        elif "ZONE" in tier_clean:
            tier_display = "ZONE"
        else:
            tier_display = tier_clean
    
    # Handle month/year
    if not month_year or str(month_year).strip() == "":
        month_display = "No Date Selected"
    else:
        month_display = str(month_year)
    
    # Construct final label
    label = f"Source: {brand_display} {tier_display} {month_display}"
    
    return label
# ========== EXECUTIVE SUMMARY FUNCTIONS (NEW) ==========
def get_exec_summary_measures():
    """
    Return list of measures needed for executive summary cards
    """
    return [
        '[Impressions]',
        '[Total Cost]',
        '[Video Completions]',
        '[Video Plays]',
        '[Total Conversions]',
        '[Clicks]',
        '[Audio Completes]',
        '[Audio Starts]'
    ]
def calculate_exec_summary_metrics(df, min_tactic_spend=0, site_grouping_rules=None):
    """
    Filter spend at tactic-slide granularity, then aggregate metrics by
    effective tactic for the Executive Summary cards.
    """
    df = df.copy()

    tactic_col = '[Tactic (Reporting)]'
    group_cols = ['Brand', 'Market', tactic_col]
    metric_cols = [
        '[Impressions]', '[Total Cost]', '[Video Completions]', '[Video Plays]',
        '[Total Conversions]', '[Clicks]', '[Audio Completes]', '[Audio Starts]'
    ]

    # Ensure costs and metrics aggregate numerically even if the connector
    # returns numeric values as strings.
    for col in metric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    agg_dict = {col: 'sum' for col in metric_cols if col in df.columns}
    strategy_col = '[Strategy (groups)]' if '[Strategy (groups)]' in df.columns else None
    site_col = '[Site (Reporting)]' if '[Site (Reporting)]' in df.columns else None

    # Resolve tactics before spend filtering so Display variants use the same
    # effective tactic names as the individual tactic slides.
    try:
        from display_resolution import resolve_display_tactic
        if tactic_col in df.columns:
            df[tactic_col] = df.apply(
                lambda row: resolve_display_tactic(
                    row[tactic_col],
                    row[strategy_col] if strategy_col else None,
                    row[site_col] if site_col else None
                ),
                axis=1
            )
    except ImportError:
        print("  [WARN] display_resolution module not found. Exec summary may have combined Display cards.")

    try:
        minimum_spend = float(min_tactic_spend)
    except (TypeError, ValueError):
        minimum_spend = 0

    # Match tactic-slide filtering: aggregate spend by effective tactic,
    # grouped site, and audience first. Only surviving combinations contribute
    # impressions, KBAs, or other metrics to the final tactic card.
    if minimum_spend > 0 and '[Total Cost]' in df.columns:
        spend_group_cols = [col for col in ['Brand', 'Market'] if col in df.columns]
        spend_group_cols.append(tactic_col)

        if site_col:
            grouping_rules = site_grouping_rules or {}

            def normalize_spend_site(site):
                site_value = str(site).strip()
                site_upper = site_value.upper()
                for group_name, grouped_sites in grouping_rules.items():
                    group_upper = str(group_name).upper().strip()
                    normalized_sites = [str(item).upper().strip() for item in grouped_sites]
                    if site_upper in normalized_sites or group_upper in site_upper:
                        return group_upper
                if 'MSP' in site_upper:
                    if 'AMPERSAND' in site_upper:
                        return 'AMPERSAND'
                    return f'MSP {site_value}'.upper()
                return site_upper

            df['_Spend_Site_Group'] = df[site_col].apply(normalize_spend_site)
            spend_group_cols.append('_Spend_Site_Group')

        if 'Audience' in df.columns:
            spend_group_cols.append('Audience')

        spend_by_combination = df.groupby(
            spend_group_cols, dropna=False
        )['[Total Cost]'].transform('sum')
        keep_mask = spend_by_combination >= minimum_spend
        dropped_rows = int((~keep_mask).sum())
        dropped_combinations = int(
            df.loc[~keep_mask, spend_group_cols].drop_duplicates().shape[0]
        )
        df = df.loc[keep_mask].copy()
        if dropped_rows:
            print(
                f"  [FILTER] Dropped {dropped_combinations} Executive Summary "
                f"site combinations ({dropped_rows} rows) below spend threshold"
            )

    # Display variants remain separate cards while all surviving sites for the
    # same effective tactic are consolidated into one card.
    df_agg = df.groupby(group_cols).agg(agg_dict).reset_index()

    df_agg['VCR'] = df_agg.apply(
        lambda row: row.get('[Video Completions]', 0) / row.get('[Video Plays]', 1)
        if pd.notna(row.get('[Video Plays]')) and row.get('[Video Plays]', 0) > 0 else 0,
        axis=1
    )
    df_agg['CPCV'] = df_agg.apply(
        lambda row: row.get('[Total Cost]', 0) / row.get('[Video Completions]', 1)
        if pd.notna(row.get('[Video Completions]')) and row.get('[Video Completions]', 0) > 0 else 0,
        axis=1
    )
    df_agg['CPA'] = df_agg.apply(
        lambda row: row.get('[Total Cost]', 0) / row.get('[Total Conversions]', 1)
        if pd.notna(row.get('[Total Conversions]')) and row.get('[Total Conversions]', 0) > 0 else 0,
        axis=1
    )
    df_agg['CPC'] = df_agg.apply(
        lambda row: row.get('[Total Cost]', 0) / row.get('[Clicks]', 1)
        if pd.notna(row.get('[Clicks]')) and row.get('[Clicks]', 0) > 0 else 0,
        axis=1
    )
    df_agg['ACR'] = df_agg.apply(
        lambda row: row.get('[Audio Completes]', 0) / row.get('[Audio Starts]', 1)
        if pd.notna(row.get('[Audio Starts]')) and row.get('[Audio Starts]', 0) > 0 else 0,
        axis=1
    )

    df_agg['KPI_Value'] = df_agg.apply(select_kpi_value, axis=1)
    df_agg['KPI_Label'] = df_agg[tactic_col].map(get_kpi_label)
    df_agg['Total_KBAs'] = df_agg['[Total Conversions]']

    return df_agg
def select_kpi_value(row):
    """
    Select the appropriate KPI value based on tactic
    Mirrors your DAX "Exec Summary KPI" logic
    """
    tactic = row['[Tactic (Reporting)]']
    
    if tactic == 'YouTube':
        return row['CPCV']
    elif tactic == 'FEP':
        return row['VCR']
    elif tactic == 'PreRoll':
        return row['VCR']
    elif tactic in ['Display', 'BT Display', 'Retargeting Display', 'Consideration Display']:
        return row['CPA']
    elif tactic == 'Meta Display':
        return row['CPA']
    elif tactic == 'Pinterest Display':
        return row['CPA']
    elif tactic == 'Pinterest Video':
        return row['CPA']
    elif tactic == 'Meta Video':
        return row['VCR']
    elif tactic == 'Social Display':
        return row['CPA']
    elif tactic == 'Social Video':
        return row['VCR']
    elif tactic == 'Search':
        return row['CPC']
    elif tactic == 'Audio':
        return row['ACR']
    elif tactic == 'TikTok':
        return row['CPCV']
    else:
        return None
def get_kpi_label(tactic):
    """Map tactic to KPI label - matches your DAX"""
    mapping = {
        'YouTube': 'CPCV',
        'FEP': 'VCR',
        'PreRoll': 'VCR',
        'Display': 'CPA',
        'BT Display': 'CPA',
        'Retargeting Display': 'CPA',
        'Consideration Display': 'CPA',
        'Meta Display': 'CPA',
        'Pinterest Display': 'CPA',
        'Pinterest Video': 'CPA',
        'Meta Video': 'VCR',
        'Social Display': 'CPA',
        'Social Video': 'VCR',
        'Search': 'CPC',
        'Audio': 'ACR',
        'TikTok': 'CPCV'
    }
    return mapping.get(tactic, 'N/A')

def add_benchmarks_and_colors(df, benchmarks, audience=None):
    """
    Add benchmark values and color coding to the dataframe
    Uses Display resolution to get correct benchmark for BT vs Retargeting
    
    Args:
        df: DataFrame with tactic metrics
        benchmarks: Benchmarks object
        audience: Audience segment (e.g., 'GEN', 'HIS', 'ASN') - if None, defaults to 'GEN'
    """
    # Import the resolution function
    try:
        from display_resolution import resolve_display_tactic
        has_resolution = True
    except ImportError:
        print("WARNING: display_resolution module not found. Display benchmarks may be incorrect.")
        has_resolution = False
    
    df = df.copy()
    
    # Default to GEN if no audience provided
    if not audience:
        audience = 'GEN'
        print(f"  [i] No audience provided, defaulting to 'GEN' for benchmarks")
    else:
        print(f"  [i] Using audience '{audience}' for benchmarks")
    
    def get_benchmark_for_row(row):
        brand = row['Brand']
        tactic = row['[Tactic (Reporting)]']
        metric = row['KPI_Label']
        # Use the passed-in audience instead of hardcoding 'GEN'
        audience_for_benchmark = audience
        
        # Handle Display tactic mapping for benchmark lookup
        if tactic == 'Display':
            tactic_lookup = 'BT Display'  # Default combined Display to BT benchmark
            print(f"  Mapping 'Display' -> 'BT Display' for benchmark lookup")
        else:
            # Not Display
            tactic_lookup = tactic
        
        # Try to find a date in the row for historical benchmark lookup
        row_date = row.get('Date') or row.get('parsed_date') or row.get('Master Date Table[Month Year]')
        
        # Get benchmark using resolved tactic AND the correct audience AND date
        benchmark = benchmarks.get_benchmark(brand, tactic_lookup, audience_for_benchmark, metric, date=row_date)
        
        # Override for Display tactic in Exec Summary (Combined card)
        if tactic == 'Display':
            return 'TBD'
        
        # If benchmark is "TBD" (from JSON), return it directly without processing
        if isinstance(benchmark, str) and benchmark.upper() == 'TBD':
            return 'TBD'
        
        # Handle set benchmarks - extract single value (sometimes DAX returns a set if there are multiple matches)
        if isinstance(benchmark, (set, list)):
            if len(benchmark) > 0:
                # If it's a set, try to find a numeric value or take the first one
                numeric_vals = [b for b in benchmark if isinstance(b, (int, float))]
                benchmark = numeric_vals[0] if numeric_vals else list(benchmark)[0]
            else:
                benchmark = None
        
        # If benchmark is still None/NaN and tactic is Display-related, try BT Display as fallback
        if (benchmark is None or pd.isna(benchmark)) and 'Display' in str(tactic_lookup):
            benchmark = benchmarks.get_benchmark(brand, 'BT Display', audience_for_benchmark, metric)
            # Re-check set for fallback
            if isinstance(benchmark, (set, list)) and len(benchmark) > 0:
                numeric_vals = [b for b in benchmark if isinstance(b, (int, float))]
                benchmark = numeric_vals[0] if numeric_vals else list(benchmark)[0]
    
        return benchmark
    
    df['Benchmark'] = df.apply(get_benchmark_for_row, axis=1)
    
    def determine_color(row):
        kpi_value = row['KPI_Value']
        benchmark = row['Benchmark']
        kpi_type = row['KPI_Label']
        
        # Handle TBD benchmarks (return black color for undefined benchmarks)
        if isinstance(benchmark, str) and benchmark.upper() == 'TBD':
            return 'black'
        
        # Handle N/A benchmarks (Cadillac)
        if benchmark is None or benchmark == 'N/A' or pd.isna(benchmark):
            return 'gray'
        
        if isinstance(benchmark, str) and benchmark.upper() == 'N/A':
            return 'gray'
        
        # Convert to float safely
        try:
            benchmark = float(benchmark)
            kpi_value = float(kpi_value)
        except (TypeError, ValueError):
            return 'gray'
        
        # Lower is better
        if kpi_type in ['CPA', 'CPCV', 'CPC']:
            return 'green' if kpi_value <= benchmark else 'red'
        
        # Higher is better
        elif kpi_type in ['VCR', 'ACR', 'CTR']:
            return 'green' if kpi_value >= benchmark else 'red'
        
        return 'gray'
    
    df['KPI_Color'] = df.apply(determine_color, axis=1)
    return df


def format_kpi_for_display(row):
    """
    Format KPI value for display (matches your DAX FORMAT logic)
    """
    kpi_type = row['KPI_Label']
    kpi_value = row['KPI_Value']
    
    if pd.isna(kpi_value):
        return 'N/A'
    
    if kpi_type in ['VCR', 'ACR']:
        # Format as percentage - use standard rounding (>=0.5 rounds up)
        rounded_pct = math.floor(kpi_value * 100 + 0.5)
        return f"{rounded_pct:.0f}%"
    elif kpi_type in ['CPA', 'CPC']:
        # Format as currency
        return f"${kpi_value:.2f}"
    elif kpi_type in ['CPCV']:
        # Format as currency with 3 decimals
        return f"${kpi_value:.3f}"
    
    return str(kpi_value)