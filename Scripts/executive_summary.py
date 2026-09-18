"""
Executive Summary Slide Generator - Refactored
Creates the multi-card executive summary slide with dynamic tactic columns

REFACTORED to use modular components:
- Uses slide_layouts for background, logos, branding (eliminates ~150 lines of duplicate code)
- Keeps only the unique executive summary card logic
"""
import math
import pandas as pd
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_VERTICAL_ANCHOR
from pptx.dml.color import RGBColor
import os
import traceback

from utils import find_column
from measures import (
    calculate_exec_summary_metrics,
    add_benchmarks_and_colors,
    format_kpi_for_display
)
from benchmarks import Benchmarks


def create_executive_summary_slide(prs, brand, market, month, df_raw, brand_configs, slide_templates, zone_lma_type, audience=None, preserve_all_tactics=False):
    """
    Create the executive summary multi-card slide
    
    Args:
        prs: PowerPoint presentation object
        brand: Brand name 
        market: Market name
        month: Month string
        df_raw: Raw dataframe from PBI semantic model query (filtered to one audience)
        brand_configs: BrandConfigurations object for styling
        slide_templates: SlideTemplates object (provides access to layouts module)
        zone_lma_type: Zone or LMA type
        audience: Audience segment (e.g., 'GEN', 'HIS')
    """
    
    # Debug: Print raw data
    print(f"  Debug - Raw data shape: {df_raw.shape}")
    print(f"  Debug - Raw data columns: {df_raw.columns.tolist()}")
    
    # 1. Filter data to this specific market/brand/month (Case-insensitive)
    df_filtered = df_raw[
        (df_raw['Brand'].str.strip().str.lower() == brand.lower()) &
        (df_raw['Market'].str.strip().str.lower() == market.lower())
    ].copy()
    
    print(f"  [DEBUG] Data after Brand/Market filter ({brand}/{market}): {len(df_filtered)} rows")
    
    if df_filtered.empty:
        print(f"  [!] No data for {brand} - {market} in query result - skipping exec summary")
        # Print available brands/markets for debugging
        if not df_raw.empty:
            print(f"    Available Brands: {df_raw['Brand'].unique().tolist()}")
            print(f"    Available Markets: {df_raw['Market'].unique().tolist()}")
        return None
    
    # 2. Apply spend at tactic-slide granularity, then aggregate by tactic.
    # This prevents a low-spend site omitted from its tactic slide from still
    # contributing impressions or KBAs to the Executive Summary card.
    from filters_manager import GeneralFiltersConfig
    site_grouping_rules = slide_templates.tactic_config.rules.get("site_grouping_rules", {})
    df_exec = calculate_exec_summary_metrics(
        df_filtered,
        min_tactic_spend=0 if preserve_all_tactics else GeneralFiltersConfig.min_tactic_spend,
        site_grouping_rules=site_grouping_rules
    )
    
    print(f"  Debug - Aggregated data shape: {df_exec.shape}")
    
    if df_exec.empty:
        print("  [!] No tactics after aggregation - skipping executive summary slide")
        return None

    # Identify key columns in the aggregated dataframe
    total_cost_column = find_column(df_exec, 'Total Cost')
    tactic_col = find_column(df_exec, 'Tactic (Reporting)')
    video_completions_column = find_column(df_exec, 'Video Completions')
    
    if not total_cost_column:
        print(f"  [!] WARNING: Total Cost column not found in aggregated data. Columns found: {df_exec.columns.tolist()}")

    # ========== FILTER OUT VIDEO TACTICS WITH 0 VIDEO COMPLETIONS ==========
    # For LMA: strict filter - FEP/YouTube must have video completions
    if zone_lma_type == "LMA" and not preserve_all_tactics:
        if video_completions_column and tactic_col:
            from filters_manager import GeneralFiltersConfig
            strict_video_tactics = GeneralFiltersConfig.lma_strict_video_tactics
            # Identify tactics that would be dropped
            dropped_tactics = df_exec[
                (df_exec[tactic_col].isin(strict_video_tactics)) & 
                (df_exec[video_completions_column] <= 0)
            ]
            
            if not dropped_tactics.empty:
                print(f"  [DEBUG] STRICT FILTER: Skipping {len(dropped_tactics)} video tactics due to 0 completions")
                for _, row in dropped_tactics.iterrows():
                    print(f"    - Dropped: {row.get(tactic_col)} (Total Cost: ${row.get(total_cost_column, 0):.2f})")
            
            df_exec = df_exec[
                (~df_exec[tactic_col].isin(strict_video_tactics)) |
                (df_exec[video_completions_column] > 0)
            ].copy()
            
            if df_exec.empty:
                print("  [!] All tactics filtered out by strict video rules - skipping slide")
                return None
    
    # 3. Add benchmarks and color coding
    benchmarks = Benchmarks()
    df_exec = add_benchmarks_and_colors(df_exec, benchmarks, audience=audience)
    
    # 4. Format KPIs for display
    df_exec['KPI_Formatted'] = df_exec.apply(format_kpi_for_display, axis=1)
    
    # 5. Get brand configuration
    brand_config = brand_configs.get_brand_config(brand)
    
    # 6. Determine zone/LMA type from data dynamically
    if df_filtered is not None and not df_filtered.empty and 'Zone/LMA' in df_filtered.columns:
        zone_lma_type = df_filtered['Zone/LMA'].iloc[0]
        print(f"  Extracted Zone/LMA type: {zone_lma_type}")
    else:
        zone_lma_type = "LMA"
        print(f"  Using default Zone/LMA type: {zone_lma_type}")
    
    # 7. Create the slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    # 8. Use slide_layouts module for all standard elements
    slide_templates.layouts.add_data_background(slide, brand_config)
    slide_templates.layouts.add_data_brand_logo(slide, brand_config)
    slide_templates.layouts.add_data_logo_divider(slide, brand_config)
    slide_templates.layouts.add_mrg_logo(slide, position='data')
    slide_templates.layouts.add_gm_confidential(slide, brand_config, position='data')
    
    # 9. Add custom title for executive summary with audience
    add_executive_summary_title(slide, month, market, brand_config, slide_templates, audience)
    
    # 10. Create the tactic cards
    create_tactic_cards(slide, df_exec, brand_config)
    
    # 11. Add source label using slide_layouts
    slide_templates.layouts.add_source_label(slide, brand_config, zone_lma_type, month)
    
    print(f"  [OK] Created executive summary slide for {brand} - {market} - {audience}")
    return slide


def add_executive_summary_title(slide, month, market, brand_config, slide_templates, audience=None):
    """
    Add title section to executive summary slide with optional audience
    """
    pixels_to_inches = slide_templates.pixels_to_inches
    
    # Add month title (centered)
    title_box = slide.shapes.add_textbox(
        pixels_to_inches(0),
        pixels_to_inches(32),
        pixels_to_inches(1280),
        pixels_to_inches(50)
    )
    title_frame = title_box.text_frame
    title_frame.text = month
    
    title_para = title_frame.paragraphs[0]
    title_para.alignment = PP_ALIGN.CENTER
    title_para.font.size = Pt(32)
    title_para.font.bold = False
    title_para.font.name = brand_config.get('primary_font', 'Segoe UI')
    title_para.font.color.rgb = brand_config.get('text_color_dark', RGBColor(0, 0, 0))
    
    # Add horizontal line
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
    
    # Add market title with audience
    market_box = slide.shapes.add_textbox(
        pixels_to_inches(0),
        pixels_to_inches(95),
        pixels_to_inches(1280),
        pixels_to_inches(50)
    )
    market_frame = market_box.text_frame
    
    # Include audience in title if provided
    if audience:
        market_frame.text = f"{market} - {audience}"
    else:
        market_frame.text = market
    
    market_para = market_frame.paragraphs[0]
    market_para.alignment = PP_ALIGN.CENTER
    market_para.font.size = Pt(32)
    market_para.font.bold = False
    market_para.font.name = brand_config.get('primary_font', 'Segoe UI')
    market_para.font.color.rgb = brand_config.get('text_color_dark', RGBColor(0, 0, 0))
    
    print(f"  Added executive summary title: {month} - {market}" + (f" - {audience}" if audience else ""))


def create_tactic_cards(slide, df_exec, brand_config):
    """
    Create dynamic tactic cards based on number of tactics
    Cards stretch full width and are centered
    
    Args:
        slide: PowerPoint slide object
        df_exec: Processed dataframe with tactic metrics
        brand_config: Brand configuration dictionary for colors
    """
    # Configuration
    num_tactics = len(df_exec)
    
    # Safety check
    if num_tactics == 0:
        print("  [!] No tactics to display")
        return
    
    print(f"  Creating {num_tactics} tactic cards")
    
    # Slide dimensions
    slide_width = Inches(13.33)
    
    # Card layout parameters - minimal margins for maximum stretch
    left_margin = Inches(0.15)
    right_margin = Inches(0.15)
    top_start = Inches(1.9) 
    card_spacing = Inches(0.12)  
    
    # Calculate card width
    available_width = slide_width - left_margin - right_margin
    total_spacing = card_spacing * (num_tactics - 1)
    card_width = (available_width - total_spacing) / num_tactics
    
    # Card row heights
    header_height = Inches(0.5)
    row_height = Inches(0.85)
    
    # Brand-specific backgrounds with transparency
    BRAND_BACKGROUNDS = {
        'GMC': {'color': RGBColor(179, 179, 179), 'transparency': 0.30},      # #B3B3B3, 30% transparency
        'Buick': {'color': RGBColor(239, 237, 234), 'transparency': 0},        # #EFEDEA, no transparency
        'Chevrolet': {'color': RGBColor(241, 241, 241), 'transparency': 0},    # #F1F1F1, no transparency
        'Cadillac': {'color': RGBColor(51, 51, 51), 'transparency': 0}          # #333333
    }

    # Brand-specific headers
    BRAND_HEADERS = {
        'GMC': RGBColor(170, 0, 0),        # Red (from line_color)
        'Buick': RGBColor(244, 181, 106),  # #F4B56A
        'Chevrolet': RGBColor(0, 119, 217), # #0077D9
        'Cadillac': RGBColor(26, 26, 26)   # #1A1A1A
    }

    brand_name = brand_config.get('name', 'GMC')
    gray_bg = BRAND_BACKGROUNDS.get(brand_name, {'color': RGBColor(192, 192, 192), 'transparency': 0})
    gray_bg_color = gray_bg['color']
    gray_bg_transparency = gray_bg['transparency']

    header_color = BRAND_HEADERS.get(brand_name, RGBColor(192, 0, 0))

    white_text = RGBColor(255, 255, 255)
    black_text = brand_config.get('text_color_dark', RGBColor(0, 0, 0))
    green_text = RGBColor(0, 176, 80)
    red_text = RGBColor(255, 0, 0)
        
    # Get font
    card_font = brand_config.get('primary_font', 'Segoe UI')
    
    # Create a card for each tactic
    for i, (idx, row) in enumerate(df_exec.iterrows()):
        tactic_name = row['[Tactic (Reporting)]']
        print(f"    Creating card {i+1}/{num_tactics}: {tactic_name}")

         # Visual display override for tactic names (only for display, not internal processing)
        display_title_overrides = {
            "BT Display": "InMarket Display"
        }
        tactic_display_name = display_title_overrides.get(tactic_name, tactic_name)
        
        # Calculate x position for this card (centered)
        x_pos = left_margin + (i * (card_width + card_spacing))
        y_pos = top_start
        
        # 1. Create header (tactic name)
        header = slide.shapes.add_shape(
            1,  # Rectangle
            x_pos,
            y_pos,
            card_width,
            header_height
        )
        header.fill.solid()
        header.fill.fore_color.rgb = header_color
        header.line.color.rgb = header_color

        header_text = header.text_frame
        header_text.text = tactic_display_name
        header_text.word_wrap = True
        header_text.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
        header_text.margin_top = Inches(0.02)
        header_text.margin_bottom = Inches(0.02)
        header_text.margin_left = Inches(0.03)
        header_text.margin_right = Inches(0.03)
        header_para = header_text.paragraphs[0]
        header_para.alignment = PP_ALIGN.CENTER
        header_para.font.size = Pt(14)
        header_para.font.bold = True
        header_para.font.name = card_font

        # Use white text for all brands except Buick (which uses text_color_dark)
        if brand_config['name'].lower() == 'buick':
            header_para.font.color.rgb = brand_config['text_color_dark']
        else:
            header_para.font.color.rgb = white_text

        y_pos += header_height
        
        # 2. Impressions row
        y_pos = add_metric_row(
            slide, x_pos, y_pos, card_width, row_height,
            "Impressions",
            f"{math.floor(row['[Impressions]'] + 0.5):,}",
            gray_bg_color, black_text, black_text, card_font
        )
        
        # 3. KPI row (with color coding)
        kpi_color = green_text if row['KPI_Color'] == 'green' else red_text if row['KPI_Color'] == 'red' else black_text
        y_pos = add_metric_row(
            slide, x_pos, y_pos, card_width, row_height,
            "KPI",
            row['KPI_Formatted'],
            gray_bg_color, black_text, kpi_color, card_font
        )
        
        # 4. KPI Type row
        y_pos = add_metric_row(
            slide, x_pos, y_pos, card_width, row_height,
            "KPI Type",
            row['KPI_Label'],
            gray_bg_color, black_text, black_text, card_font
        )
        
        # 5. Benchmark row
        benchmark_formatted = format_benchmark(row['Benchmark'], row['KPI_Label'])
        y_pos = add_metric_row(
            slide, x_pos, y_pos, card_width, row_height,
            "Benchmark",
            benchmark_formatted,
            gray_bg_color, black_text, black_text, card_font
        )
        
        # 6. Total KBAs row
        y_pos = add_metric_row(
            slide, x_pos, y_pos, card_width, row_height,
            "Total KBAs",
            f"{math.floor(row['Total_KBAs'] + 0.5):,}",
            gray_bg_color, black_text, black_text, card_font
        )


def add_metric_row(slide, x_pos, y_pos, card_width, row_height, label, value, bg_color, label_color, value_color, font_name):
    """
    Add a single metric row to a card
    
    Args:
        slide: PowerPoint slide object
        x_pos, y_pos: Position coordinates
        card_width, row_height: Dimensions
        label: Label text (e.g., "Impressions")
        value: Value text (e.g., "1,234,567")
        bg_color: Background color
        label_color: Label text color
        value_color: Value text color
        font_name: Font to use
    
    Returns:
        New y_pos after adding the row
    """
    # Create background shape
    bg_shape = slide.shapes.add_shape(
        1,  # Rectangle
        x_pos,
        y_pos,
        card_width,
        row_height
    )
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = bg_color
    bg_shape.line.color.rgb = bg_color
    
    # Add label text
    label_box = slide.shapes.add_textbox(
        x_pos,
        y_pos,
        card_width,
        row_height / 2
    )
    label_frame = label_box.text_frame
    label_frame.text = label
    label_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
    label_frame.margin_top = Inches(0)
    label_frame.margin_bottom = Inches(0)
    label_frame.margin_left = Inches(0.05)
    label_frame.margin_right = Inches(0.05)
    label_para = label_frame.paragraphs[0]
    label_para.alignment = PP_ALIGN.CENTER
    label_para.font.size = Pt(10)
    label_para.font.name = font_name
    label_para.font.color.rgb = label_color
    
    # Add value text
    value_box = slide.shapes.add_textbox(
        x_pos,
        y_pos + (row_height / 2),
        card_width,
        row_height / 2
    )
    value_frame = value_box.text_frame
    value_frame.text = value
    value_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
    value_frame.margin_top = Inches(0)
    value_frame.margin_bottom = Inches(0)
    value_frame.margin_left = Inches(0.05)
    value_frame.margin_right = Inches(0.05)
    value_para = value_frame.paragraphs[0]
    value_para.alignment = PP_ALIGN.CENTER
    
    # Conditional font size based on label
    if label == "KPI Type":
        value_para.font.size = Pt(16)  # Smaller for KPI Type
    else:
        value_para.font.size = Pt(24)  # Regular size for everything else
    
    value_para.font.bold = False
    value_para.font.name = font_name
    value_para.font.color.rgb = value_color
    
    return y_pos + row_height


def format_benchmark(benchmark, kpi_label):
    """
    Format benchmark value for display
    
    Args:
        benchmark: Benchmark value
        kpi_label: KPI label to determine formatting
    
    Returns:
        Formatted benchmark string
    """
    if benchmark is None or benchmark == 'N/A':
        return 'N/A'
    
    # If benchmark is already a string (like "TBD"), return it directly
    if isinstance(benchmark, str):
        return benchmark
    
    if kpi_label in ['VCR', 'ACR']:
        rounded_pct = math.floor(benchmark * 100 + 0.5)
        return f"{rounded_pct:.0f}%"
    elif kpi_label in ['CPA', 'CPC']:
        return f"${benchmark:.2f}"
    elif kpi_label in ['CPCV']:
        return f"${benchmark:.3f}"
    
    return str(benchmark)
