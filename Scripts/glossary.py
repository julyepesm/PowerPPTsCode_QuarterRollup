"""
Glossary Slide Generator - Multi-Brand Support

Creates a standardized glossary slide with brand-specific styling.
Supports GMC, Cadillac, Buick, and Chevrolet with different table color schemes.
"""

from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor


# Brand-specific table color configurations
BRAND_TABLE_COLORS = {
    'gmc': {
        'header_color': (139, 0, 0),           # Dark red
        'row_color_1': (254, 161, 158),        # Light red
        'row_color_2': (254, 192, 191),        # Lighter red
        'text_color_header': (255, 255, 255),  # White
        'text_color_body': (0, 0, 0),          # Black
        'has_alternating_rows': True,
        'has_divider_line': False,
        'divider_color': None,
        'remove_grid_lines': True
    },
    'cadillac': {
        'header_color': (0, 0, 0),             # Black
        'row_color_1': (0, 0, 0),              # Black (no alternating)
        'row_color_2': (0, 0, 0),              # Black (no alternating)
        'text_color_header': (255, 255, 255),  # White
        'text_color_body': (255, 255, 255),    # White
        'has_alternating_rows': False,
        'has_divider_line': True,
        'divider_color': (255, 255, 255),      # White line
        'remove_grid_lines': True              # Remove all table borders
    },
    'buick': {
        'header_color': (255, 255, 255),       # White
        'row_color_1': (255, 255, 255),        # White
        'row_color_2': (238, 237, 237),        # Light gray
        'text_color_header': (0, 0, 0),        # Black (dark text)
        'text_color_body': (0, 0, 0),          # Black (dark text)
        'has_alternating_rows': True,
        'has_divider_line': True,
        'divider_color': (254, 80, 0),         # Orange #FE5000
        'remove_grid_lines': False
    },
    'chevrolet': {
        'header_color': (255, 255, 255),       # White
        'row_color_1': (255, 255, 255),        # White
        'row_color_2': (238, 237, 237),        # Light gray
        'text_color_header': (0, 0, 0),        # Black (dark text)
        'text_color_body': (0, 0, 0),          # Black (dark text)
        'has_alternating_rows': True,
        'has_divider_line': True,
        'divider_color': (0, 119, 217),        # Blue #0077D9
        'remove_grid_lines': False
    }
}


def create_glossary_slide(prs, brand_config, slide_templates):
    """
    Create a glossary slide with fixed content and brand-specific styling
    
    Args:
        prs: Presentation object
        brand_config: Brand configuration dictionary (must include 'brand_name')
        slide_templates: SlideTemplates object for accessing layouts
    
    Returns:
        slide: The created glossary slide
    """
    
    # Add blank slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    # Add background and standard elements
    slide_templates.layouts.add_data_background(slide, brand_config)
    slide_templates.layouts.add_data_brand_logo(slide, brand_config)
    slide_templates.layouts.add_data_logo_divider(slide, brand_config)
    slide_templates.layouts.add_mrg_logo(slide, position='data')
    slide_templates.layouts.add_gm_confidential(slide, brand_config, position='data')
    
    # Add title (custom, no market name bar)
    _add_glossary_title(slide, brand_config)
    
    # Get brand-specific table colors
    brand_name = brand_config.get('brand_name', 'gmc').lower()
    print(f"  DEBUG: Detected brand_name from config: '{brand_name}'")
    
    table_colors = BRAND_TABLE_COLORS.get(brand_name, BRAND_TABLE_COLORS['gmc'])
    print(f"  DEBUG: Using table colors for: '{brand_name}'")
    print(f"  DEBUG: Header color: {table_colors['header_color']}")
    print(f"  DEBUG: Row color 1: {table_colors['row_color_1']}")
    
    # Add tables with brand-specific styling
    _add_terms_table(slide, brand_config, table_colors)
    _add_kpi_table(slide, brand_config, table_colors)
    
    return slide


def _add_glossary_title(slide, brand_config):
    """Add 'Reporting Glossary' title to the slide"""
    
    # Get the brand's text color and font
    text_color_dark = brand_config.get('text_color_dark', (0, 0, 0))
    primary_font = brand_config.get('primary_font')
    
    # Title positioning - centered on slide
    slide_width = Inches(13.333)
    left = Inches(0)
    top = Inches(0.6)
    width = slide_width
    height = Inches(0.8)
    
    title_box = slide.shapes.add_textbox(left, top, width, height)
    text_frame = title_box.text_frame
    text_frame.word_wrap = False
    
    p = text_frame.paragraphs[0]
    p.text = "Reporting Glossary"
    p.alignment = PP_ALIGN.CENTER
    
    # Style the title
    p.font.name = primary_font
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = RGBColor(text_color_dark[0], text_color_dark[1], text_color_dark[2])


def _add_terms_table(slide, brand_config, table_colors):
    """Add the top table with term definitions (FEP, KBA, KPI)"""
    
    # Table positioning
    left_position = Inches(0.51)
    top_position = Inches(1.53)
    table_width = Inches(12.31)
    table_height = Inches(1.98)
    
    # Create table: 4 rows, 3 columns (header + 3 terms)
    rows = 4
    cols = 3
    shape = slide.shapes.add_table(rows, cols, left_position, top_position, table_width, table_height)
    table = shape.table
    
    # Calculate column widths ensuring they sum exactly to table width
    table_width_emu = Emu(table_width)
    col1_width = Inches(1.2)
    col2_width = Inches(3.5)
    col3_width = table_width_emu - Emu(col1_width) - Emu(col2_width)
    
    table.columns[0].width = col1_width
    table.columns[1].width = col2_width
    table.columns[2].width = col3_width
    
    # Remove grid lines if specified (for Cadillac)
    if table_colors.get('remove_grid_lines', False):
        _remove_table_borders(table)
    
    # Header row - use brand-specific header color
    headers = ["Term", "Name", "Description"]
    for col_idx, header_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        _style_cell(cell, header_text, table_colors, brand_config, is_header=True, bg_color=table_colors['header_color'])
    
    # Add divider line if needed (Buick/Chevrolet)
    if table_colors['has_divider_line']:
        _add_header_divider_line(slide, left_position, top_position, table_width, table, table_colors)
    
    # Data rows
    data = [
        ("FEP", "Full Episode Player", "Ads running within episodic content (i.e. Hulu, YouTube TV, ESPN)"),
        ("KBA", "Key Business Activity", "Refers to the 6 dealer site outcomes (Click to Call, Email Leads, Hours and Directions, Inventory Searches, VDP Views, Window Stickers)"),
        ("KPI", "Key Performance Indicator", "GM aligned goal for tactic performance")
    ]
    
    for row_idx, (term, name, description) in enumerate(data, start=1):
        # Determine row color based on brand settings
        if table_colors['has_alternating_rows']:
            row_color = table_colors['row_color_1'] if row_idx % 2 == 1 else table_colors['row_color_2']
        else:
            row_color = table_colors['row_color_1']
        
        _style_cell(table.cell(row_idx, 0), term, table_colors, brand_config, is_header=False, bg_color=row_color)
        _style_cell(table.cell(row_idx, 1), name, table_colors, brand_config, is_header=False, bg_color=row_color)
        _style_cell(table.cell(row_idx, 2), description, table_colors, brand_config, is_header=False, bg_color=row_color)


def _add_kpi_table(slide, brand_config, table_colors):
    """Add the bottom table with KPI details"""
    
    # Table positioning
    left_position = Inches(0.51)
    top_position = Inches(3.85)
    table_width = Inches(12.31)
    table_height = Inches(2.93)
    
    # Create table: 6 rows, 4 columns (header + 5 KPIs)
    rows = 6
    cols = 4
    shape = slide.shapes.add_table(rows, cols, left_position, top_position, table_width, table_height)
    table = shape.table
    
    # Calculate column widths ensuring they sum exactly to table width
    table_width_emu = Emu(table_width)
    col1_width = Inches(1.2)
    col2_width = Inches(3.5)
    col3_width = Inches(4.5)
    col4_width = table_width_emu - Emu(col1_width) - Emu(col2_width) - Emu(col3_width)
    
    table.columns[0].width = col1_width
    table.columns[1].width = col2_width
    table.columns[2].width = col3_width
    table.columns[3].width = col4_width
    
    # Remove grid lines if specified (for Cadillac)
    if table_colors.get('remove_grid_lines', False):
        _remove_table_borders(table)
    
    # Header row - use brand-specific header color
    headers = ["KPI", "Name", "Description", "Tactics"]
    for col_idx, header_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        _style_cell(cell, header_text, table_colors, brand_config, is_header=True, bg_color=table_colors['header_color'])
    
    # Add divider line if needed (Buick/Chevrolet)
    if table_colors['has_divider_line']:
        _add_header_divider_line(slide, left_position, top_position, table_width, table, table_colors)
    
    # Data rows
    data = [
        ("ACR", "Audio Completion Rate", "Rate at which an audio ad is listened to completion", "Streaming Audio"),
        ("CPA", "Cost Per Action", "Cost to get a Key Business Activity (KBA)", "Display, Social Display"),
        ("CPC", "Cost Per Click", "Cost to get a Click", "Search"),
        ("CPCV", "Cost Per Completed View", "Cost to get a Completed View", "YouTube, Social Video (TikTok)"),
        ("VCR", "Video Completion Rate", "Rate at which video ads are watched to completion", "FEP, Preroll, Social Video (Meta)")
    ]
    
    for row_idx, (kpi, name, description, tactics) in enumerate(data, start=1):
        # Determine row color based on brand settings
        if table_colors['has_alternating_rows']:
            row_color = table_colors['row_color_1'] if row_idx % 2 == 1 else table_colors['row_color_2']
        else:
            row_color = table_colors['row_color_1']
        
        _style_cell(table.cell(row_idx, 0), kpi, table_colors, brand_config, is_header=False, bg_color=row_color)
        _style_cell(table.cell(row_idx, 1), name, table_colors, brand_config, is_header=False, bg_color=row_color)
        _style_cell(table.cell(row_idx, 2), description, table_colors, brand_config, is_header=False, bg_color=row_color)
        _style_cell(table.cell(row_idx, 3), tactics, table_colors, brand_config, is_header=False, bg_color=row_color)


def _remove_table_borders(table):
    """Remove all grid lines from table (for Cadillac)"""
    from pptx.oxml import parse_xml
    from pptx.util import Pt
    
    # Iterate through all cells and remove borders
    for row in table.rows:
        for cell in row.cells:
            # Access the cell's table cell properties
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            
            # Create border elements with no line
            for border_name in ['a:lnL', 'a:lnR', 'a:lnT', 'a:lnB']:
                # Remove existing border if present
                for existing in tcPr.findall('.//' + border_name, namespaces={'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}):
                    tcPr.remove(existing)
                
                # Add new border with no fill
                border_xml = f'<{border_name} xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:noFill/></{border_name}>'
                border_element = parse_xml(border_xml)
                tcPr.append(border_element)


def _add_header_divider_line(slide, table_left, table_top, table_width, table, table_colors):
    """Add a colored divider line below the header row (for Buick/Chevrolet/Cadillac)"""
    
    # Get the height of the first row (header)
    header_height = table.rows[0].height
    
    # Position line just below the header row
    line_left = table_left
    line_top = table_top + header_height - Pt(10)
    line_width = table_width
    line_height = Pt(3) # 3 px
    
    # Add the line as a shape
    from pptx.enum.shapes import MSO_SHAPE
    line_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        line_left,
        line_top,
        line_width,
        line_height
    )
    
    # Style the line - solid fill, no border, no shadow
    line_shape.fill.solid()
    divider_color = table_colors['divider_color']
    line_shape.fill.fore_color.rgb = RGBColor(divider_color[0], divider_color[1], divider_color[2])
    
    # Remove border
    line_shape.line.fill.background()
    
    # Remove shadow
    line_shape.shadow.inherit = False


def _style_cell(cell, text, table_colors, brand_config, is_header=False, bg_color=None):
    """
    Style a table cell with text, background color, and formatting
    
    Args:
        cell: Table cell object
        text: Text content
        table_colors: Brand-specific table color configuration
        brand_config: Brand configuration dictionary
        is_header: Boolean indicating if this is a header cell
        bg_color: Optional background color override (for data rows)
    """
    # Determine background color
    if bg_color is None:
        bg_color = table_colors['header_color']
    
    # Set background color
    fill = cell.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(bg_color[0], bg_color[1], bg_color[2])
    
    # Set text
    text_frame = cell.text_frame
    text_frame.clear()
    text_frame.word_wrap = True
    
    p = text_frame.paragraphs[0]
    p.text = text
    p.alignment = PP_ALIGN.LEFT
    
    # Determine text color
    if is_header:
        text_color = table_colors['text_color_header']
    else:
        text_color = table_colors['text_color_body']
    
    # Font styling
    font = p.font
    font.name = brand_config.get('primary_font')
    font.size = Pt(18) if is_header else Pt(16)
    font.bold = is_header
    font.color.rgb = RGBColor(text_color[0], text_color[1], text_color[2])
    
    # Cell margins
    text_frame.margin_left = Inches(0.1)
    text_frame.margin_right = Inches(0.1)
    text_frame.margin_top = Inches(0.08)
    text_frame.margin_bottom = Inches(0.08)
    
    # Vertical alignment
    text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE


# ========== INTEGRATION HELPER ==========

def add_glossary_to_deck(prs, brand_config, slide_templates):
    """
    Convenience function to add glossary slide to existing presentation
    
    Args:
        prs: Presentation object
        brand_config: Brand configuration dictionary (must include 'brand_name')
        slide_templates: SlideTemplates object
    
    Returns:
        slide: The created glossary slide
    """
    return create_glossary_slide(prs, brand_config, slide_templates)