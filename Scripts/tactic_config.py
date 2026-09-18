import os
import json
from benchmarks import Benchmarks

class TacticConfig:
    """Manages tactic-specific configurations and business rules"""
    
    def __init__(self):
        """Initialize tactic configuration mappings"""
        print("DEBUG: Initializing TacticConfig...")
        self.config_path = os.path.join(os.path.dirname(__file__), 'config', 'normalization_rules.json')
        self.discovery_path = os.path.join(os.path.dirname(__file__), 'config', 'discovery_log.json')
        self.rules = self._load_rules()
        
        self._metric_definitions = self._build_metric_definitions()
        self._chart_configurations = self._build_chart_configurations()
        self.benchmarks = Benchmarks()
        print("DEBUG: TacticConfig initialized with benchmarks")

    def _load_rules(self):
        """Load normalization rules from JSON and normalize for case-insensitivity"""
        rules = {
            "tactic_mappings": {}, 
            "site_grouping_rules": {},
            "video_tactics": [],
            "four_box_tactics": [],
            "sorting_ranks": {}
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    raw_rules = json.load(f)
                    
                    # Normalize tactic mappings (UPPERCASE KEYS)
                    if "tactic_mappings" in raw_rules:
                        rules["tactic_mappings"] = {k.upper().strip(): v for k, v in raw_rules["tactic_mappings"].items()}
                    
                    # Normalize site groupings (UPPERCASE VALUE LISTS and KEYS)
                    if "site_grouping_rules" in raw_rules:
                        for group, sites in raw_rules["site_grouping_rules"].items():
                            rules["site_grouping_rules"][group.upper()] = [s.upper().strip() for s in sites]
                    
                    # Load video tactics list
                    if "video_tactics" in raw_rules:
                        rules["video_tactics"] = raw_rules["video_tactics"]
                    
                    # Load four-box tactics list
                    if "four_box_tactics" in raw_rules:
                        rules["four_box_tactics"] = raw_rules["four_box_tactics"]
                    
                    # Load sorting ranks
                    if "sorting_ranks" in raw_rules:
                        rules["sorting_ranks"] = raw_rules["sorting_ranks"]
                        
            except Exception as e:
                print(f"  [ERROR] Failed to load normalization rules: {e}")
        return rules

    def _discover_tactic(self, tactic):
        """Log unknown tactics for later review"""
        if not tactic or tactic == "Unknown": return
        
        discovery = {}
        if os.path.exists(self.discovery_path):
            try:
                with open(self.discovery_path, 'r') as f:
                    discovery = json.load(f)
            except: pass
        
        if tactic not in discovery and tactic not in self.rules.get("tactic_mappings", {}):
            discovery[tactic] = "PENDING"
            try:
                with open(self.discovery_path, 'w') as f:
                    json.dump(discovery, f, indent=2)
            except: pass
    
    def get_tactic_benchmarks(self, tactic, strategy=None, brand=None, audience=None):
        """Get benchmark definitions for a tactic with brand-specific values"""
        
        # Validate required parameters
        if brand is None:
            raise ValueError("brand parameter is required for get_tactic_benchmarks")
        if audience is None:
            raise ValueError("audience parameter is required for get_tactic_benchmarks")
        
        effective_tactic = self._resolve_display_tactic(tactic, strategy)
        benchmark_structure = self._get_benchmark_structure(effective_tactic)
        
        if not benchmark_structure:
            return []
        
        result = []
        for item in benchmark_structure:
            metric = item['metric']
            position_index = item['position_index']
            
            benchmark_value = self._get_formatted_benchmark(
                brand, effective_tactic, audience, metric
            )
            
            # === CHANGE THIS SECTION ===
            # Only add benchmarks that have actual values (not None/N/A)
            if benchmark_value:  # This will be None for N/A benchmarks
                result.append({
                    'metric': metric,
                    'benchmark': benchmark_value,
                    'position_index': position_index
                })
            # === END CHANGE ===
        
        return result
        
    def _get_benchmark_structure(self, tactic):
        """
        Get the structure of benchmarks (which metrics, positions) without values
        
        Returns:
            list of dicts with 'metric' and 'position_index'
        """
        structures = {
            'FEP': [
                {'metric': 'VCR', 'position_index': 2}
            ],
            'PreRoll': [
                {'metric': 'VCR', 'position_index': 2},
                {'metric': 'Viewability', 'position_index': 3}
            ],
            'YouTube': [
                {'metric': 'CPCV', 'position_index': 2},
                {'metric': 'YT Viewability', 'position_index': 3}
            ],
            'BT Display': [
                {'metric': 'CPA', 'position_index': 2},
                {'metric': 'Viewability', 'position_index': 3}
            ],
            'Consideration Display': [  # <--- NUEVO
                {'metric': 'CPA', 'position_index': 2},
                {'metric': 'Viewability', 'position_index': 3}
            ],
            'Retargeting Display': [
                {'metric': 'CPA', 'position_index': 2},
                {'metric': 'Viewability', 'position_index': 3}
            ],
            'Meta Display': [
                {'metric': 'CPA', 'position_index': 2}
            ],
            'Meta Video': [
                {'metric': 'VCR', 'position_index': 2}
            ],
            'Pinterest Display': [
                {'metric': 'CPA', 'position_index': 2}
            ],
            'TikTok': [
                {'metric': 'CPCV', 'position_index': 2}
            ],
            'Audio': [
                {'metric': 'ACR', 'position_index': 2}
            ]
        }
        return structures.get(tactic, [])
    
    def _get_formatted_benchmark(self, brand, tactic, audience, metric):
        """
        Get brand-specific benchmark value and format it properly
        """
        # Map display metric names to benchmark metric names
        metric_map = {
            'VCR': 'VCR',
            'CPCV': 'CPCV',
            'CPA': 'CPA',
            'ACR': 'ACR',
            'Viewability': None,  # Viewability always 70%
            'YT Viewability': None  # YT Viewability always 90%
        }
        
        # Handle special cases
        if metric == 'Viewability':
            return '>70%'
        if metric == 'YT Viewability':
            return '>90%'
        
        benchmark_metric = metric_map.get(metric)
        if not benchmark_metric:
            return None
        
        # Get value from Benchmarks class
        value = self.benchmarks.get_benchmark(brand, tactic, audience, benchmark_metric)
        
        if value is None or value == 'N/A':
            return None
        
        # Handle set benchmarks - extract single value
        if isinstance(value, set):
            print(f"  WARNING: Benchmark for {tactic}/{metric} is a set: {value}")
            if len(value) > 0:
                value = list(value)[0]
                print(f"  Using first value: {value}")
            else:
                return None
        
        # === ADD THIS CHECK ===
        # Check if value is 'N/A' string after extracting from set
        if value == 'N/A' or (isinstance(value, str) and value.upper() == 'N/A'):
            return None
        
        # Convert to float for formatting
        try:
            # If value is "TBD", return it directly
            if isinstance(value, str) and value.upper() == 'TBD':
                return 'TBD'
            value = float(value)
        except (TypeError, ValueError):
            print(f"  WARNING: Cannot convert benchmark value to float: {value}")
            return None
        # === END NEW CHECK ===
        
        # Format the value
        if benchmark_metric == 'VCR' or benchmark_metric == 'ACR':
            return f">{int(value * 100)}%"
        elif benchmark_metric in ['CPA', 'CPCV', 'CPC']:
            # User wants more precision (e.g. 0.025)
            # Use .3f to capture 0.025, but maybe strip trailing zeros if possible?
            # Or just strictly .3f
            formatted = f"{value:.3f}"
            if formatted.endswith('0'): formatted = formatted[:-1] # 0.030 -> 0.03
            return f"<${formatted}"
        else:
            return str(value)
        

    def get_tactic_metrics(self, tactic, strategy=None):
        """
        Define which metrics to display for each tactic
        
        Args:
            tactic (str): The tactic name (e.g., 'FEP', 'Display', 'YouTube')
            strategy (str, optional): Strategy context for Display tactic splitting
        
        Returns:
            list of tuples: [(display_label, metric_key), ...]
        
        Examples:
            >>> config = TacticConfig()
            >>> config.get_tactic_metrics('FEP')
            [('Impressions', 'impressions'), ('Video Completes', 'video_completions'), ('VCR', 'vcr')]
            
            >>> config.get_tactic_metrics('Display', strategy='BT')
            [('Impressions', 'impressions'), ('Total KBAs', 'total_conversions'), ('CPO', 'cpa'), ...]
        """
        # Handle Display tactic split based on Strategy
        effective_tactic = self._resolve_display_tactic(tactic, strategy)
        
        # Return metric configuration or fallback to generic
        if effective_tactic not in self._metric_definitions:
            print(f"WARNING: Tactic '{effective_tactic}' not defined in metric mapping. Using generic metrics.")
            return self._get_generic_metrics()
        
        return self._metric_definitions[effective_tactic]
    
    def get_tactic_chart_config(self, tactic, strategy=None):
        """
        Get chart configuration for a tactic
        
        Args:
            tactic (str): The tactic name
            strategy (str, optional): Strategy context for Display tactic
        
        Returns:
            dict or None: {
                'title': 'Video Completes and VCR',
                'bar_metric': 'video_completions',
                'bar_label': 'Video Completions',
                'line_metric': 'vcr',
                'line_label': 'VCR'
            }
        """
        effective_tactic = self._resolve_display_tactic(tactic, strategy)
        return self._chart_configurations.get(effective_tactic, None)
    
    def uses_four_metric_boxes(self, tactic, strategy=None):
        """
        Determine if tactic uses 4 metric boxes (vs standard 3)
        
        Args:
            tactic (str): The tactic name
            strategy (str, optional): Strategy context
        
        Returns:
            bool: True if tactic uses 4 boxes, False for 3 boxes
        """
        effective_tactic = self._resolve_display_tactic(tactic, strategy)
        
        # Get from JSON: four_box_tactics is a SEPARATE list from video_tactics
        # FEP is a video tactic but only has 3 boxes, not 4
        four_box_tactics = self.rules.get("four_box_tactics", [])
        if not four_box_tactics:
            four_box_tactics = ['PreRoll', 'YouTube', 'BT Display', 'Retargeting Display', 'Consideration Display']
            
        return effective_tactic in four_box_tactics
    
    # ========== PRIVATE METHODS ==========
    
    def _resolve_display_tactic(self, tactic, strategy, site=None):
        """
        Handle Display tactic split based on Strategy field
        Also handle Social naming variations (Social -> Meta)
        """
        # 1. Apply JSON normalization rules first (CASE-INSENSITIVE)
        t_upper = str(tactic).upper().strip()
        tactic_mappings = self.rules.get("tactic_mappings", {})
        
        if t_upper in tactic_mappings:
            tactic = tactic_mappings[t_upper]
        
        # 2. Discover unknown tactics (if not already defined and not a standard resolved name)
        # Standard resolved names are already in _metric_definitions
        if tactic not in self._metric_definitions and t_upper not in self._metric_definitions:
            self._discover_tactic(tactic)

        from display_resolution import resolve_display_tactic
        return resolve_display_tactic(tactic, strategy, site)
    
    def _build_metric_definitions(self):
        """
        Build the complete metric definitions mapping
        
        Returns:
            dict: Tactic -> [(label, metric_key), ...]
        """
        return {
            'FEP': [
                ('Impressions', 'impressions'),
                ('Video Completes', 'video_completions'),
                ('VCR', 'vcr')
            ],
            'PreRoll': [
                ('Impressions', 'impressions'),
                ('Video Completes', 'video_completions'),
                ('VCR', 'vcr'),
                ('Viewability', 'viewability')
            ],
            'YouTube': [
                ('Impressions', 'impressions'),
                ('Video Completes', 'video_completions'),
                ('CPCV', 'cpcv'),
                ('YT Viewability', 'yt_viewability')
            ],
            'BT Display': [
                ('Impressions', 'impressions'),
                ('Total KBAs', 'total_conversions'),
                ('CPA', 'cpa'),
                ('Viewability', 'viewability')
            ],
            'Consideration Display': [  # <--- NUEVO
                ('Impressions', 'impressions'),
                ('Total KBAs', 'total_conversions'),
                ('CPA', 'cpa'),
                ('Viewability', 'viewability')
            ],
            'Retargeting Display': [
                ('Impressions', 'impressions'),
                ('Total KBAs', 'total_conversions'),
                ('CPA', 'cpa'),
                ('Viewability', 'viewability')
            ],
            'Meta Display': [
                ('Impressions', 'impressions'),
                ('Total KBAs', 'total_conversions'),
                ('CPA', 'cpa')
            ],
            'Meta Video': [
                ('Impressions', 'impressions'),
                ('Video Completes', 'video_completions'),
                ('VCR', 'vcr')
            ],
            'Pinterest Display': [
                ('Impressions', 'impressions'),
                ('Total KBAs', 'total_conversions'),
                ('CPA', 'cpa')
            ],
            'Pinterest Video': [
                ('Impressions', 'impressions'),
                ('Total KBAs', 'total_conversions'),
                ('CPA', 'cpa')
            ],
            'TikTok': [
                ('Impressions', 'impressions'),
                ('Video Completes', 'video_completions'),
                ('CPCV', 'cpcv'),
            ],
            'Search': [
                ('Impressions', 'impressions'),
                ('Clicks', 'clicks'),
                ('CPC', 'cpc'),
            ],
            'Audio': [
                ('Impressions', 'impressions'),
                ('Audio Completes', 'audio_completes'),
                ('ACR', 'acr'),
            ],
        }
    
    def _build_benchmark_definitions(self):
        """
        Build the complete benchmark definitions mapping
        
        Returns:
            dict: Tactic -> [{'metric': str, 'benchmark': str, 'position_index': int}, ...]
        """
        return {
            'FEP': [
                {'metric': 'VCR', 'benchmark': '>90%', 'position_index': 2}
            ],
            'PreRoll': [
                {'metric': 'VCR', 'benchmark': '>66%', 'position_index': 2},
                {'metric': 'Viewability', 'benchmark': '>70%', 'position_index': 3}
            ],
            'YouTube': [
                {'metric': 'CPCV', 'benchmark': '<$0.025', 'position_index': 2},
                {'metric': 'YT Viewability', 'benchmark': '>90%', 'position_index': 3}
            ],
            'BT Display': [
                {'metric': 'CPA', 'benchmark': '<$0.17', 'position_index': 2},
                {'metric': 'Viewability', 'benchmark': '>70%', 'position_index': 3}
            ],
            'Consideration Display': [  # <--- NUEVO
                {'metric': 'CPA', 'benchmark': '<$0.17', 'position_index': 2},
                {'metric': 'Viewability', 'benchmark': '>70%', 'position_index': 3}
            ],
            'Retargeting Display': [
                {'metric': 'CPA', 'benchmark': '<$0.09', 'position_index': 2},
                {'metric': 'Viewability', 'benchmark': '>70%', 'position_index': 3}
            ],
            'Meta Display': [
                {'metric': 'CPA', 'benchmark': '<$0.67', 'position_index': 2}
            ],
            'Meta Video': [
                {'metric': 'VCR', 'benchmark': '>53%', 'position_index': 2}
            ],
            'Pinterest Display': [
                {'metric': 'CPA', 'benchmark': '<$0.12', 'position_index': 2}
            ],
            'TikTok': [
                {'metric': 'CPCV', 'benchmark': '<$0.32', 'position_index': 2}
            ],
            'Search': [
                {'metric': 'CPC', 'position_index': 2}
            ]
        }
    
    def _build_chart_configurations(self):
        """
        Build the complete chart configurations mapping
        
        Returns:
            dict: Tactic -> {
                'title': str,
                'bar_metric': str,
                'bar_label': str,
                'line_metric': str,
                'line_label': str
            }
        """
        return {
            'FEP': {
                'title': 'Video Completes and VCR',
                'bar_metric': 'video_completions',
                'bar_label': 'Video Completions',
                'line_metric': 'vcr',
                'line_label': 'VCR'
            },
            'PreRoll': {
                'title': 'Video Completes and VCR',
                'bar_metric': 'video_completions',
                'bar_label': 'Video Completions',
                'line_metric': 'vcr',
                'line_label': 'VCR'
            },
            'YouTube': {
                'title': 'Video Completes and CPCV',
                'bar_metric': 'video_completions',
                'bar_label': 'Video Completions',
                'line_metric': 'cpcv',
                'line_label': 'CPCV'
            },
            'Meta Video': {
                'title': 'Video Completes and VCR',
                'bar_metric': 'video_completions',
                'bar_label': 'Video Completions',
                'line_metric': 'vcr',
                'line_label': 'VCR'
            },
            'TikTok': {
                'title': 'Video Completes and CPCV',
                'bar_metric': 'video_completions',
                'bar_label': 'Video Completions',
                'line_metric': 'cpcv',
                'line_label': 'CPCV'
            },
            'Display': {
                'title': 'Key Business Activities with CPA',
                'bar_metric': 'total_conversions',
                'bar_label': 'Total Conversions',
                'line_metric': 'cpa',
                'line_label': 'CPA'
            },
            'BT Display': {
                'title': 'Key Business Activities with CPA',
                'bar_metric': 'total_conversions',
                'bar_label': 'Total Conversions',
                'line_metric': 'cpa',
                'line_label': 'CPA'
            },
            'Consideration Display': {  # <--- NUEVO
                'title': 'Key Business Activities with CPA',
                'bar_metric': 'total_conversions',
                'bar_label': 'Total Conversions',
                'line_metric': 'cpa',
                'line_label': 'CPA'
            },
            'Retargeting Display': {
                'title': 'Key Business Activities with CPA',
                'bar_metric': 'total_conversions',
                'bar_label': 'Total Conversions',
                'line_metric': 'cpa',
                'line_label': 'CPA'
            },
            'Meta Display': {
                'title': 'Key Business Activities with CPA',
                'bar_metric': 'total_conversions',
                'bar_label': 'Total Conversions',
                'line_metric': 'cpa',
                'line_label': 'CPA'
            },
            'Pinterest Video': {
                'title': 'Key Business Activities with CPA',
                'bar_metric': 'total_conversions',
                'bar_label': 'Total Conversions',
                'line_metric': 'cpa',
                'line_label': 'CPA'
            },
            'Pinterest Display': {
                'title': 'Key Business Activities with CPA',
                'bar_metric': 'total_conversions',
                'bar_label': 'Total KBAs',
                'line_metric': 'cpa',
                'line_label': 'CPA'
            },
            'Search': {
                'title': 'Clicks and CPC',
                'bar_metric': 'clicks',
                'bar_label': 'Clicks',
                'line_metric': 'cpc',
                'line_label': 'CPC'
            },
            'Audio': {
                'title': 'Audio Completes and ACR',
                'bar_metric': 'audio_completes',
                'bar_label': 'Audio Completes',
                'line_metric': 'acr',
                'line_label': 'ACR'
            }
        }
    
    def _get_generic_metrics(self):
        """Fallback generic metrics when tactic is not defined"""
        return [
            ('Impressions', 'impressions'),
            ('Total Conversions', 'total_conversions'),
            ('Metric 3', 'metric_3')
        ]


# ========== UTILITY FUNCTIONS ==========

def get_metric_column_mapping():
    """
    Map metric keys to actual Power BI column names
    
    Returns:
        dict: metric_key -> column_name
    
    Usage:
        This is used when extracting data from DataFrames to translate
        between the simplified metric keys and the actual column names
        from Power BI (which include brackets)
    """
    return {
        'impressions': '[Impressions]',
        'clicks': '[Clicks]',
        'video_completions': '[Video Completions]',
        'audio_completes': '[Audio Completes]',
        'total_conversions': '[Total Conversions]',
        'vcr': 'VCR',
        'viewability': 'Viewability',
        'yt_viewability': 'YT Viewability',
        'cpa': 'CPA',
        'cpc': 'CPC',
        'cpcv': 'CPCV',
        'acr': 'ACR',
        'ctr': 'CTR',
        'cpm': 'CPM'
    }


# ========== CONVENIENCE SINGLETON ==========

# Create a singleton instance for easy importing
_default_config = TacticConfig()

# Convenience functions that use the singleton
def get_tactic_metrics(tactic, strategy=None):
    """Convenience function using default config instance"""
    return _default_config.get_tactic_metrics(tactic, strategy)

def get_tactic_benchmarks(tactic, strategy=None, brand=None, audience=None):
    """Convenience function using default config instance"""
    return _default_config.get_tactic_benchmarks(tactic, strategy, brand, audience)

def get_tactic_chart_config(tactic, strategy=None):
    """Convenience function using default config instance"""
    return _default_config.get_tactic_chart_config(tactic, strategy)

def uses_four_metric_boxes(tactic, strategy=None):
    """Convenience function using default config instance"""
    return _default_config.uses_four_metric_boxes(tactic, strategy)