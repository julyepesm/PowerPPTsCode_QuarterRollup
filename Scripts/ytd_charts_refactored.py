"""
YTD Charts Slide Generator - Multi-Brand Support
Creates TWO YTD slides:
1. YTD KBA breakdown by tactic (existing)
2. YTD Impressions by vehicle (new)

REFACTORED to use modular components:
- Uses slide_layouts for background, logos, branding
- Brand-specific color palettes for both tactics and vehicles
- Keeps only the unique chart visualization logic
"""
import os
import glob
import fnmatch
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from io import BytesIO
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import (
    XL_CHART_TYPE, XL_LEGEND_POSITION, XL_TICK_MARK, 
    XL_DATA_LABEL_POSITION
)
import settings


# ========== HELPER FUNCTIONS ==========

def _rgb_to_matplotlib(rgb_color):
    """Convert RGBColor to matplotlib format (0-1) — delegates to shared utils"""
    from utils import rgb_to_matplotlib
    return rgb_to_matplotlib(rgb_color)

# Global flag (obsolete, kept for backwards compatibility just in case)
_FONTS_REGISTERED = False

def _register_ytd_fonts(base_path):
    """Register brand fonts with matplotlib — delegates to shared utils"""
    from utils import register_brand_fonts
    register_brand_fonts(base_path)

def _get_safe_font(brand_config):
    """Get matplotlib-safe font family and weight — delegates to shared utils"""
    from utils import get_safe_font
    return get_safe_font(brand_config)

def _get_brand_font(brand_config):
    """Retrieve brand font from config (Legacy fallback)"""
    return brand_config.get('primary_font', 'Segoe UI')

def _to_rgb_color(color_spec):
    """Convert JSON list [R, G, B] to RGBColor object"""
    if isinstance(color_spec, list) and len(color_spec) == 3:
        return RGBColor(color_spec[0], color_spec[1], color_spec[2])
    return color_spec

def _get_brand_chart_colors(brand):
    """Get tactic colors for a brand from settings"""
    raw_colors = settings.get_tactic_colors(brand)
    default_palette = settings.get_default_palette(brand)
    
    colors = {k: _to_rgb_color(v) for k, v in raw_colors.items()}
    colors['default_palette'] = [_to_rgb_color(c) for c in default_palette]
    return colors

def _get_brand_vehicle_colors(brand):
    """Get vehicle colors for a brand from settings"""
    raw_colors = settings.get_vehicle_colors(brand)
    default_palette = settings.get_default_palette(brand)
    
    colors = {k: _to_rgb_color(v) for k, v in raw_colors.items()}
    colors['default_palette'] = [_to_rgb_color(c) for c in default_palette]
    return colors

# Colors are now loaded dynamically from settings.py via _get_brand_chart_colors and _get_brand_vehicle_colors


def create_ytd_kba_slide(prs, brand, market, month, df_raw, brand_configs, slide_templates, zone_lma_type):
    """
    Create YTD KBA breakdown slide with stacked column chart
    
    Args:
        prs: PowerPoint presentation object
        brand: Brand name
        market: Market name
        month: Month string
        df_raw: Raw dataframe from PBI semantic model query
        brand_configs: BrandConfigurations object for styling
        slide_templates: SlideTemplates object (provides access to layouts module)
        zone_lma_type: Zone or LMA type
    
    Returns:
        Slide object or None if no data
    """
    print(f"  Debug - Raw KBA data shape: {df_raw.shape}")
    
    df_filtered = df_raw.copy()
    
    if df_filtered.empty:
        print("  [WARN] No data after filtering - skipping YTD KBA slide")
        return None
    
    brand_config = brand_configs.get_brand_config(brand)
    
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    slide_templates.layouts.add_data_background(slide, brand_config)
    slide_templates.layouts.add_data_brand_logo(slide, brand_config)
    slide_templates.layouts.add_data_logo_divider(slide, brand_config)
    slide_templates.layouts.add_mrg_logo(slide, position='data')
    slide_templates.layouts.add_gm_confidential(slide, brand_config, position='data')
    
    _add_ytd_title(slide, month, market, "YTD KBA Breakdown", "KBA Breakdown", brand_config, slide_templates)
    
    add_kba_breakdown_chart(slide, df_filtered, brand_config, market, brand)
    
    slide_templates.layouts.add_source_label(slide, brand_config, zone_lma_type, month)
    
    print(f"  [OK] Created YTD KBA slide for {brand} - {market}")
    return slide


def create_ytd_impressions_slide(prs, brand, market, month, df_raw, brand_configs, slide_templates, zone_lma_type):
    """
    Create YTD Impressions by vehicle slide with stacked column chart
    
    Args:
        prs: PowerPoint presentation object
        brand: Brand name
        market: Market name
        month: Month string
        df_raw: Raw dataframe from PBI semantic model query (must include Vehicle column)
        brand_configs: BrandConfigurations object for styling
        slide_templates: SlideTemplates object
        zone_lma_type: Zone or LMA type
    
    Returns:
        Slide object or None if no data
    """
    print(f"  Debug - Raw impressions data shape: {df_raw.shape}")
    
    df_filtered = df_raw.copy()
    
    if df_filtered.empty:
        print("  [WARN] No data after filtering - skipping YTD Impressions slide")
        return None
    
    brand_config = brand_configs.get_brand_config(brand)
    
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    slide_templates.layouts.add_data_background(slide, brand_config)
    slide_templates.layouts.add_data_brand_logo(slide, brand_config)
    slide_templates.layouts.add_data_logo_divider(slide, brand_config)
    slide_templates.layouts.add_mrg_logo(slide, position='data')
    slide_templates.layouts.add_gm_confidential(slide, brand_config, position='data')
    
    _add_ytd_title(slide, month, market, "YTD Impressions", "By Vehicle", brand_config, slide_templates)
    
    add_impressions_by_vehicle_chart(slide, df_filtered, brand_config, market, brand)
    
    slide_templates.layouts.add_source_label(slide, brand_config, zone_lma_type, month)
    
    print(f"  [OK] Created YTD Impressions slide for {brand} - {market}")
    return slide


def _add_ytd_title(slide, month, market, title_text, subtitle_text, brand_config, slide_templates):
    """
    Add YTD slide title with optional subtitle
    
    Args:
        slide: Slide object
        month: Month string
        market: Market name
        title_text: Main title (e.g., "YTD KBA Breakdown" or "YTD Impressions")
        subtitle_text: Optional subtitle (e.g., "By Vehicle" or None)
        brand_config: Brand configuration dictionary
        slide_templates: SlideTemplates object
    """
    pixels_to_inches = slide_templates.pixels_to_inches
    
    # Add market title at top (centered)
    market_box = slide.shapes.add_textbox(
        pixels_to_inches(0),
        pixels_to_inches(32),
        pixels_to_inches(1280),
        pixels_to_inches(50)
    )
    market_frame = market_box.text_frame
    market_frame.text = market
    
    market_para = market_frame.paragraphs[0]
    market_para.alignment = PP_ALIGN.CENTER
    market_para.font.size = Pt(32)
    market_para.font.bold = False
    market_para.font.name = brand_config.get('primary_font', 'Segoe UI')
    market_para.font.color.rgb = brand_config.get('text_color_dark', RGBColor(0, 0, 0))
    
    # Add horizontal line under market
    line_shape = slide.shapes.add_connector(
        1,
        pixels_to_inches(485),
        pixels_to_inches(88),
        pixels_to_inches(799),
        pixels_to_inches(88)
    )
    line_shape.line.color.rgb = brand_config.get('line_color', RGBColor(192, 0, 0))
    line_shape.line.width = pixels_to_inches(2)
    line_shape.shadow.inherit = False
    
    # Add main title
    title_box = slide.shapes.add_textbox(
        pixels_to_inches(0),
        pixels_to_inches(95),
        pixels_to_inches(1280),
        pixels_to_inches(50)
    )
    title_frame = title_box.text_frame
    title_frame.text = title_text
    
    title_para = title_frame.paragraphs[0]
    title_para.alignment = PP_ALIGN.CENTER
    title_para.font.size = Pt(40)
    title_para.font.bold = True
    title_para.font.name = brand_config.get('primary_font', 'Segoe UI')
    title_para.font.color.rgb = brand_config.get('text_color_dark', RGBColor(0, 0, 0))
    
    # Add "All Tactics" label for KBA slides
    all_tactics_box = slide.shapes.add_textbox(
        pixels_to_inches(0),
        pixels_to_inches(155),
        pixels_to_inches(1280),
        pixels_to_inches(25)
    )
    all_tactics_frame = all_tactics_box.text_frame
    all_tactics_frame.text = "All Tactics"
    
    all_tactics_para = all_tactics_frame.paragraphs[0]
    all_tactics_para.alignment = PP_ALIGN.CENTER
    all_tactics_para.font.size = Pt(14)
    all_tactics_para.font.italic = True
    all_tactics_para.font.name = brand_config.get('primary_font', 'Segoe UI')
    all_tactics_para.font.color.rgb = brand_config.get('text_color_dark', RGBColor(0, 0, 0))
    
    # Add subtitle if provided (e.g., "KBA Breakdown" or "By Vehicle")
    if subtitle_text:
        subtitle_box = slide.shapes.add_textbox(
            pixels_to_inches(0),
            pixels_to_inches(178),
            pixels_to_inches(1280),
            pixels_to_inches(30)
        )
        subtitle_frame = subtitle_box.text_frame
        subtitle_frame.text = subtitle_text
        
        subtitle_para = subtitle_frame.paragraphs[0]
        subtitle_para.alignment = PP_ALIGN.CENTER
        subtitle_para.font.size = Pt(16)
        subtitle_para.font.bold = True
        subtitle_para.font.name = brand_config.get('primary_font', 'Segoe UI')
        subtitle_para.font.color.rgb = brand_config.get('text_color_dark', RGBColor(0, 0, 0))


def add_kba_breakdown_chart(slide, historical_data, brand_config, market_name, brand):
    """Add stacked column chart showing YTD KBA Breakdown by tactic"""
    if historical_data is None or historical_data.empty:
        print("  [WARN] No historical data available for KBA breakdown chart")
        return

    brand_key = brand.lower()
    brand_colors = _get_brand_chart_colors(brand_key)
    
    # Exclude metadata columns, keep only numeric tactic columns
    exclude_columns = ['Month', 'Brand', 'Market', 'Zone/LMA', 'Date', 'Year', 'MonthNum']
    all_columns = historical_data.columns.tolist()
    tactic_columns = [col for col in all_columns if col not in exclude_columns and pd.api.types.is_numeric_dtype(historical_data[col])]
    
    tactic_colors = {}
    color_index = 0
    default_palette = brand_colors['default_palette']

    for tactic in tactic_columns:
        if tactic in brand_colors:
            tactic_colors[tactic] = brand_colors[tactic]
        else:
            tactic_colors[tactic] = default_palette[color_index % len(default_palette)]
            color_index += 1
    
    # Prepare data for plotting
    months = historical_data['Month'].tolist()
    tactics_to_plot = []
    series_data = {}
    
    for tactic in tactic_columns:
        if tactic in historical_data.columns:
            values = historical_data[tactic].fillna(0).tolist()
            if any(v > 0 for v in values):
                series_data[tactic] = values
                tactics_to_plot.append(tactic)
    
    if not tactics_to_plot:
        print("  [WARN] No tactics with non-zero values found")
        return

    # Create Matplotlib Chart
    img_stream = _create_ytd_matplotlib_chart(
        months, series_data, tactics_to_plot, tactic_colors, 
        "YTD KBA Breakdown", brand_config
    )
    
    # Add image to slide
    left = Inches(0.5)
    top = Inches(2.26)
    width = Inches(12.27) 
    height = Inches(4.54)
    slide.shapes.add_picture(img_stream, left, top, width=width, height=height)
    
    print(f"  [OK] Added Matplotlib KBA breakdown chart for {market_name}")


def add_impressions_by_vehicle_chart(slide, historical_data, brand_config, market_name, brand):
    """Add stacked column chart showing YTD Impressions by vehicle"""
    if historical_data is None or historical_data.empty:
        print("  [WARN] No historical data available for impressions by vehicle chart")
        return

    brand_key = brand.lower()
    brand_colors = _get_brand_vehicle_colors(brand_key)
    
    # Exclude metadata columns, keep only numeric vehicle columns
    exclude_columns = ['Month', 'Brand', 'Market', 'Zone/LMA', 'Date', 'Year', 'MonthNum']
    all_columns = historical_data.columns.tolist()
    vehicle_columns = [col for col in all_columns if col not in exclude_columns and pd.api.types.is_numeric_dtype(historical_data[col])]
    
    vehicle_colors = {}
    color_index = 0
    default_palette = brand_colors['default_palette']

    for vehicle in vehicle_columns:
        if vehicle in brand_colors:
            vehicle_colors[vehicle] = brand_colors[vehicle]
        else:
            vehicle_colors[vehicle] = default_palette[color_index % len(default_palette)]
            color_index += 1
    
    # Prepare data for plotting
    months = historical_data['Month'].tolist()
    vehicles_to_plot = []
    series_data = {}
    
    for vehicle in vehicle_columns:
        if vehicle in historical_data.columns:
            values = historical_data[vehicle].fillna(0).tolist()
            if any(v > 0 for v in values):
                series_data[vehicle] = values
                vehicles_to_plot.append(vehicle)
    
    if not vehicles_to_plot:
        print("  [WARN] No vehicles with non-zero values found")
        return

    # Create Matplotlib Chart
    img_stream = _create_ytd_matplotlib_chart(
        months, series_data, vehicles_to_plot, vehicle_colors, 
        "YTD Impressions by Vehicle", brand_config
    )
    
    # Add image to slide
    left = Inches(0.5)
    top = Inches(2.26)
    width = Inches(12.27)
    height = Inches(4.54)
    slide.shapes.add_picture(img_stream, left, top, width=width, height=height)
    
    print(f"  [OK] Added Matplotlib impressions by vehicle chart for {market_name}")


def _create_ytd_matplotlib_chart(categories, series_data, series_to_plot, series_colors, chart_title, brand_config, benchmark=None):
    """Generate a stacked bar chart using Matplotlib and return as BytesIO stream"""
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import FuncFormatter

    # Register fonts using the base_path from brand_config if possible
    base_path = brand_config.get('base_path', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _register_ytd_fonts(base_path)

    # Get mapped font family and weight
    font_family, font_weight = _get_safe_font(brand_config)
    
    # Get the brand-specific text color
    # For Cadillac (dark background), we use white. For others, we use the prominent dark color.
    brand_name = brand_config.get('name', '').lower()
    if 'cadillac' in brand_name:
        text_color = _rgb_to_matplotlib(brand_config.get('text_color_dark', RGBColor(255, 255, 255)))
    else:
        # Standardizing on absolute black for maximum readability on light backgrounds
        # Overriding any brand config grey
        text_color = _rgb_to_matplotlib(RGBColor(0, 0, 0))
    
    line_color = _rgb_to_matplotlib(brand_config.get('line_color', RGBColor(180, 180, 180)))
    
    # Increase DPI for high-quality PPTX output
    fig, ax = plt.subplots(figsize=(12, 4.5), dpi=120)
    fig.patch.set_alpha(0)  # Transparent background
    ax.patch.set_alpha(0)
    
    x = np.arange(len(categories))
    bottom = np.zeros(len(categories))
    
    # Determine bar width and x-axis limits based on number of categories
    num_cats = len(categories)
    if num_cats == 1:
        bar_width = 0.35
        ax.set_xlim(-1, 1)
    elif num_cats == 2:
        bar_width = 0.5
        ax.set_xlim(-0.8, 1.8)
    else:
        bar_width = 0.7
        ax.set_xlim(-0.5, num_cats - 0.5)
        
    # Plot each series
    for series_name in series_to_plot:
        values = np.array(series_data[series_name])
        color = _rgb_to_matplotlib(series_colors[series_name])
        
        ax.bar(x, values, bottom=bottom, label=series_name, color=color, width=bar_width)
        bottom += values
    
    # Add Total labels on top
    max_total = max(bottom) if len(bottom) > 0 else 0
    for i, total in enumerate(bottom):
        if total > 0:
            ax.text(i, total + (max_total * 0.02), f'{int(total):,}', 
                    ha='center', va='bottom', fontsize=11, fontweight='bold',
                    family=font_family, color=text_color)
    
    # Styling
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=0, ha='center', fontsize=11, 
                        family=font_family, fontweight=font_weight, color=text_color)
    
    # Y-axis scaling with headroom for labels
    ax.set_ylim(0, max_total * 1.20 if max_total > 0 else 1)
    
    # Remove ALL spines
    for spine_name in ['top', 'right', 'left', 'bottom']:
        ax.spines[spine_name].set_visible(False)
    
    # Configure Y-axis on the LEFT as a "dynamic scaling guide"
    ax.yaxis.set_visible(True)
    ax.yaxis.tick_left()
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax.tick_params(axis='y', which='both', length=0, pad=10) # Hide tick marks, add padding
    
    # Style Y-axis labels
    for label in ax.get_yticklabels():
        label.set_family(font_family)
        label.set_fontsize(10) # Increased from 9
        label.set_color(text_color)
        label.set_alpha(1.0) # Force full opacity (was 0.8)
    
    # Remove gridlines
    ax.yaxis.grid(False)
    ax.set_axisbelow(True)
    ax.tick_params(axis='x', which='both', bottom=False)
    
    # Legend at bottom with category label prefix
    if series_to_plot:
        # Determine legend title based on chart type
        if 'KBA' in chart_title:
            legend_title = 'Tactic'
        elif 'Impressions' in chart_title or 'Vehicle' in chart_title:
            legend_title = 'Vehicle'
        else:
            legend_title = None
            
        legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.08), 
                           ncol=min(len(series_to_plot), 6), frameon=False,
                           title=legend_title,
                           prop={'family': font_family, 'size': 11, 'weight': font_weight})
        
        # Style legend title
        if legend.get_title():
            legend.get_title().set_fontfamily(font_family)
            legend.get_title().set_fontsize(11) # Increased from 9
            legend.get_title().set_color(text_color)
            legend.get_title().set_alpha(1.0) # Ensure full opacity
        
        for text in legend.get_texts():
            text.set_color(text_color)
            text.set_alpha(1.0) # Ensure full opacity
    
    plt.tight_layout()
    
    # Save to stream
    img_stream = BytesIO()
    plt.savefig(img_stream, format='png', dpi=150, transparent=True, bbox_inches='tight')
    plt.close(fig)
    img_stream.seek(0)
    return img_stream
