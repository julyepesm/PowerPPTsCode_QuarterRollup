import os
import json
import pandas as pd

class GeneralFiltersConfig:
    """Centralized manager for general and YTD report filters"""
    
    # Class-level defaults (will be overwritten by load_config)
    ytd_filter_enabled = True
    ytd_min_outcomes = 100
    ytd_min_impressions = 1000
    rolling_window_months = 6
    exclude_zero_cost_months = True
    skip_video_tactics_with_zero_completions = True
    lma_strict_video_tactics = ["FEP", "YouTube"]
    min_tactic_spend = 50
    
    @classmethod
    def load_config(cls):
        """Load configuration values from external JSON file"""
        config_path = os.path.join(os.path.dirname(__file__), "config", "general_filters.json")
        if not os.path.exists(config_path):
            config_path = os.path.join("Scripts", "config", "general_filters.json")
            
        if not os.path.exists(config_path):
            print(f"  [WARN] General filters config not found at: {config_path}. Using hardcoded defaults.")
            return
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cls.update_batch(data)
                print(f"  [SUCCESS] Loaded general filters from: {config_path}")
        except Exception as e:
            print(f"  [ERROR] Failed to load general filters config: {e}. Using defaults.")

    @classmethod
    def to_dict(cls):
        """Convert current runtime configuration to dictionary"""
        return {
            'ytd_filter_enabled': cls.ytd_filter_enabled,
            'ytd_min_outcomes': cls.ytd_min_outcomes,
            'ytd_min_impressions': cls.ytd_min_impressions,
            'rolling_window_months': cls.rolling_window_months,
            'exclude_zero_cost_months': cls.exclude_zero_cost_months,
            'skip_video_tactics_with_zero_completions': cls.skip_video_tactics_with_zero_completions,
            'lma_strict_video_tactics': cls.lma_strict_video_tactics,
            'min_tactic_spend': cls.min_tactic_spend
        }

    @classmethod
    def update_batch(cls, settings_dict):
        """Update multiple configurations in one batch"""
        if not settings_dict:
            return
            
        if 'ytd_filter_enabled' in settings_dict:
            cls.ytd_filter_enabled = bool(settings_dict['ytd_filter_enabled'])
        if 'ytd_min_outcomes' in settings_dict:
            cls.ytd_min_outcomes = int(settings_dict['ytd_min_outcomes'])
        if 'ytd_min_impressions' in settings_dict:
            cls.ytd_min_impressions = int(settings_dict['ytd_min_impressions'])
        if 'rolling_window_months' in settings_dict:
            cls.rolling_window_months = int(settings_dict['rolling_window_months'])
        if 'exclude_zero_cost_months' in settings_dict:
            cls.exclude_zero_cost_months = bool(settings_dict['exclude_zero_cost_months'])

        if 'skip_video_tactics_with_zero_completions' in settings_dict:
            cls.skip_video_tactics_with_zero_completions = bool(settings_dict['skip_video_tactics_with_zero_completions'])
        if 'lma_strict_video_tactics' in settings_dict:
            if isinstance(settings_dict['lma_strict_video_tactics'], list):
                cls.lma_strict_video_tactics = settings_dict['lma_strict_video_tactics']
        if 'min_tactic_spend' in settings_dict:
            cls.min_tactic_spend = float(settings_dict['min_tactic_spend'])


def should_include_tactic_by_spend(total_spend, minimum_spend):
    """Return True when a tactic's aggregated spend meets the configured threshold."""
    try:
        total_spend_value = float(total_spend)
    except (TypeError, ValueError):
        return False

    try:
        minimum_spend_value = float(minimum_spend)
    except (TypeError, ValueError):
        minimum_spend_value = 0

    return total_spend_value >= minimum_spend_value

TACTIC_METRIC_COLUMNS = (
    'Total Cost', 'Impressions', 'Video Completions', 'Video Plays',
    'Clicks', 'Total Conversions', 'Click to Calls', 'Email Leads',
    'Hours & Directions', 'Inventory Searches', 'VDP Views',
    'Window Stickers', 'Audio Completes', 'Audio Starts',
    'Unique Viewable Impressions', 'Unique Measured Impressions',
    'Active View: Viewable Impressions',
    'Active View: Measurable Impressions'
)

def aggregate_tactic_metric_rows(metric_rows):
    if metric_rows is None or metric_rows.empty:
        return metric_rows
    aggregated = metric_rows.iloc[:1].copy()
    for metric_name in TACTIC_METRIC_COLUMNS:
        matching_column = next(
            (column for column in metric_rows.columns
             if str(column).split('[')[-1].rstrip(']') == metric_name),
            None
        )
        if matching_column is None:
            continue
        numeric_values = pd.to_numeric(
            metric_rows[matching_column], errors='coerce'
        ).fillna(0)
        aggregated.loc[aggregated.index[0], matching_column] = numeric_values.sum()
    return aggregated.reset_index(drop=True)

# Automatically load config on module import
GeneralFiltersConfig.load_config()
