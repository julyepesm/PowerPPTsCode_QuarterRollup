"""
Shared Utility Functions

Centralized helpers used across multiple modules to avoid duplication.
Contains: column lookup, color conversion, font management, and unit conversion.
"""

import os
import fnmatch
from pptx.util import Inches
from pptx.dml.color import RGBColor


# ========== COLUMN LOOKUP ==========

def find_column(df_or_row, name):
    """
    Find a column by name, handling Power BI table prefixes and brackets.
    
    Searches for:
      1. Exact match: 'Total Cost'
      2. Bracketed:   '[Total Cost]'
      3. Prefixed:    'PoP Master Table[Total Cost]'
    
    Args:
        df_or_row: DataFrame, Series, or any object with .columns or .index
        name: Column name to search for (without brackets or prefix)
    
    Returns:
        The actual column name found, or None
    """
    if df_or_row is None:
        return None
    
    # Get column names from DataFrame or Series
    if hasattr(df_or_row, 'columns'):
        cols = df_or_row.columns
    elif hasattr(df_or_row, 'index'):
        cols = df_or_row.index
    else:
        return None
    
    # 1. Exact match
    if name in cols:
        return name
    
    # 2. Bracketed version
    bracketed = f"[{name}]"
    if bracketed in cols:
        return bracketed
    
    # 3. Table-prefixed version
    for col in cols:
        if str(col).endswith(f"[{name}]") or str(col).endswith(name):
            return col
    
    return None


# ========== COLOR CONVERSION ==========

def rgb_to_matplotlib(rgb_color):
    """
    Convert RGBColor or (r, g, b) tuple to matplotlib format (0-1 range).
    
    Args:
        rgb_color: RGBColor object, or (r, g, b) tuple with 0-255 values
    
    Returns:
        Tuple of (r, g, b) floats in 0.0-1.0 range
    """
    try:
        if isinstance(rgb_color, RGBColor):
            try:
                r, g, b = rgb_color.r, rgb_color.g, rgb_color.b
            except AttributeError:
                hex_color = str(rgb_color)
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
            return (r / 255.0, g / 255.0, b / 255.0)
        elif isinstance(rgb_color, tuple) and len(rgb_color) == 3:
            return (rgb_color[0] / 255.0, rgb_color[1] / 255.0, rgb_color[2] / 255.0)
        else:
            return (0, 0, 0)
    except Exception as e:
        print(f"  [WARN] Color conversion error: {e}")
        return (0, 0, 0)


# ========== FONT MANAGEMENT ==========

# Global flag to prevent re-registering fonts multiple times
_FONTS_REGISTERED = False

# Font name → (matplotlib family, weight) mapping
FONT_MAPPING = {
    'StratumGMC Light': ('StratumGMC', 'normal'),
    'StratumGMC-Medium': ('StratumGMC', 'normal'),
    'Buick Text Light': ('Buick Text', 'normal'),
    'Buick Text-Rg': ('Buick Text', 'normal'),
    'Chevy Sans Light': ('Chevy Sans', 'normal'),
    'Chevy Sans-Regular': ('Chevy Sans', 'normal'),
    'Cadillac Gothic Narrow': ('Cadillac Gothic', 'normal'),
}


def register_brand_fonts(base_path, verbose=False):
    """
    Register brand fonts with matplotlib. Safe to call multiple times 
    (only registers once).
    
    Args:
        base_path: Root project path (parent of Scripts/)
        verbose: If True, print detailed font registration info
    """
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    
    import matplotlib.font_manager as fm
    
    font_base_dir = os.path.join(base_path, 'Design', 'Fonts')
    
    if not os.path.exists(font_base_dir):
        if verbose:
            print(f"  [WARN] Font directory not found: {font_base_dir}")
        return
    
    if verbose:
        print(f"  Searching for fonts in: {font_base_dir}")
    
    # Search recursively for all font files
    font_files = []
    for root, dirs, files in os.walk(font_base_dir):
        for ext in ['*.ttf', '*.otf', '*.TTF', '*.OTF']:
            for filename in fnmatch.filter(files, ext):
                font_files.append(os.path.join(root, filename))
    
    if not font_files:
        if verbose:
            print(f"  [WARN] No font files found in {font_base_dir}")
        return
    
    if verbose:
        print(f"  Found {len(font_files)} font files")
    
    # Register each font
    registered_count = 0
    for font_file in font_files:
        try:
            fm.fontManager.addfont(font_file)
            if verbose:
                print(f"  [OK] Registered: {os.path.basename(font_file)}")
            registered_count += 1
        except Exception as e:
            if verbose:
                print(f"  [!] Could not register {os.path.basename(font_file)}: {e}")
    
    if registered_count > 0:
        fm._load_fontmanager(try_read_cache=False)
        _FONTS_REGISTERED = True
        print(f"  [OK] Brand fonts registered ({registered_count} files)")
    
    if verbose:
        # DEBUG: Show available brand fonts
        print("\n=== DEBUG: Available brand fonts ===")
        brand_keywords = ['GMC', 'Stratum', 'Buick', 'Cadillac', 'Chevy']
        for font in fm.fontManager.ttflist:
            if any(keyword.lower() in font.name.lower() for keyword in brand_keywords):
                print(f"  Font name: '{font.name}' (from file: {os.path.basename(font.fname)})")
        print("=== END DEBUG ===\n")


def get_safe_font(font_name):
    """
    Get matplotlib-safe font family and weight for a brand font name.
    
    Args:
        font_name: Font name string (e.g., 'StratumGMC Light') or brand_config dict
    
    Returns:
        Tuple of (family, weight) for matplotlib
    """
    # Handle being called with a brand_config dict (backward compat)
    if isinstance(font_name, dict):
        font_name = font_name.get('primary_font', 'Segoe UI')
    
    if font_name in FONT_MAPPING:
        return FONT_MAPPING[font_name]
    
    # Fallback by brand keyword
    if 'Stratum' in font_name: return ('StratumGMC', 'normal')
    if 'Buick' in font_name: return ('Buick Text', 'normal')
    if 'Chevy' in font_name: return ('Chevy Sans', 'normal')
    if 'Cadillac' in font_name: return ('Cadillac Gothic', 'normal')
    
    return ('Arial', 'normal')


# ========== UNIT CONVERSION ==========

def pixels_to_inches(pixels):
    """Convert pixels to PowerPoint inches (96 DPI standard)"""
    return Inches(pixels / 96.0)
