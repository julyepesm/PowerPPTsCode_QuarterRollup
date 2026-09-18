import os

# Power BI Connection Settings
POWERBI_WORKSPACE_ID = "82479c32-8d45-4aef-9120-93f31c710d2d"
POWERBI_DATASET_ID = "f4174371-9ea0-42e6-b84c-c4c3e0f9193c"
POWERBI_CLIENT_ID = "ea0616ba-638b-4df5-95b9-636659ae5121"

# Authentication Settings
AUTHORITY = "https://login.microsoftonline.com/organizations"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
BASE_URL = "https://api.powerbi.com/v1.0/myorg"

# Asset Paths
DEFAULT_BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED_SLIDES_FOLDER = "Generated_Slides"

# GM Brands Configuration
GM_BRANDS = ["Buick", "GMC", "Cadillac", "Chevrolet"]

import json

def load_color_config():
    """Load vehicle and tactic colors from external JSON"""
    # Use direct path relative to this file
    config_path = os.path.join(os.path.dirname(__file__), "config", "vehicle_colors.json")
    if not os.path.exists(config_path):
        # Fallback to local path if directory structure differs
        config_path = os.path.join("Scripts", "config", "vehicle_colors.json")
        
    if not os.path.exists(config_path):
        print(f"  [WARN] Color config not found at: {config_path}")
        return {}
        
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to load color config: {e}")
        return {}

# Global configuration object
COLOR_CONFIG = load_color_config()

def get_vehicle_colors(brand):
    """Returns color mapping for a brand's vehicles"""
    brand_data = COLOR_CONFIG.get(brand.lower(), {})
    return brand_data.get("vehicles", {})

def get_brand_for_vehicle(vehicle_name):
    """
    Returns the brand that 'owns' this vehicle in the config.
    Returns None if the vehicle is not found in any brand.
    Matches vehicle names case-insensitively.
    """
    search_name = vehicle_name.lower().strip()
    for brand, data in COLOR_CONFIG.items():
        if "vehicles" in data:
            # Create a lowercase mapping for the vehicles in this brand
            brand_vehicles = {v.lower().strip(): v for v in data["vehicles"].keys()}
            if search_name in brand_vehicles:
                return brand.capitalize()
    return None

def get_tactic_colors(brand):
    """Returns color mapping for a brand's tactics"""
    brand_data = COLOR_CONFIG.get(brand.lower(), {})
    return brand_data.get("tactics", {})

def get_default_palette(brand):
    """Returns the default color palette for a brand"""
    brand_data = COLOR_CONFIG.get(brand.lower(), {})
    return brand_data.get("default_palette", [])

def load_benchmark_config():
    """Load benchmark values from external JSON"""
    config_path = os.path.join(os.path.dirname(__file__), "config", "benchmarks.json")
    if not os.path.exists(config_path):
        config_path = os.path.join("Scripts", "config", "benchmarks.json")
        
    if not os.path.exists(config_path):
        print(f"  [WARN] Benchmark config not found at: {config_path}")
        return {}
        
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to load benchmark config: {e}")
        return {}

# Global benchmark object
BENCHMARK_CONFIG = load_benchmark_config()

def get_benchmarks():
    """Returns the complete benchmark configuration"""
    return BENCHMARK_CONFIG
