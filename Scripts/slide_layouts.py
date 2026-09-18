"""
Slide Layouts Module

This module handles all slide structure and positioning elements:
- Background images and colors
- Brand logos and MRG logos
- Headers, titles, and dividers
- GM Confidential text
- Source labels
- Basic shape positioning utilities

No data visualization - just the "canvas" for slides.
"""

import os
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR


class SlideLayouts:
    """Manages slide layouts, backgrounds, and structural elements"""
    
    def __init__(self, brand_configs):
        """
        Initialize with brand configurations
        
        Args:
            brand_configs: BrandConfigurations instance with brand-specific settings
        """
        self.brand_configs = brand_configs
    
    # ========== UTILITY METHODS ==========
    
    def pixels_to_inches(self, pixels):
        """Convert pixels to inches for PowerPoint positioning"""
        return Inches(pixels / 96.0)  # 96 DPI standard
    
    def _determine_title_text(self, market_name, zone_lma_type):
        """Determine whether to show 'ZONE DIGITAL MONTHLY' or 'LMA DIGITAL MONTHLY'"""
        if zone_lma_type:
            zone_lma_clean = str(zone_lma_type).upper().strip()
            if "ZONE" in zone_lma_clean:
                return "ZONE DIGITAL\nMONTHLY"
            elif "LMA" in zone_lma_clean:
                return "LMA DIGITAL\nMONTHLY"

        if market_name is None or str(market_name).strip() == "":
            return "ZONE DIGITAL\nMONTHLY"

        if isinstance(market_name, str) and market_name.strip():
            return "LMA DIGITAL\nMONTHLY"

        return "ZONE DIGITAL\nMONTHLY"
    
    # ========== TITLE SLIDE ELEMENTS ==========
    
    def add_title_background(self, slide, brand_name, brand_config):
        """Add background for title slides"""
        if brand_name.lower() == 'cadillac':
            # Cadillac uses solid black background
            background_shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(0), Inches(0),
                width=Inches(13.33), height=Inches(7.5)
            )
            background_shape.fill.solid()
            background_shape.fill.fore_color.rgb = RGBColor(0, 0, 0)  # Black
            background_shape.line.fill.background()  # Remove border
            print(f"Added {brand_config['name']} solid black background")
            
        elif brand_name.lower() in ['chevrolet', 'chevy']:
            # Chevrolet uses solid white background
            background_shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(0), Inches(0),
                width=Inches(13.33), height=Inches(7.5)
            )
            background_shape.fill.solid()
            background_shape.fill.fore_color.rgb = RGBColor(255, 255, 255)  # White
            background_shape.line.fill.background()  # Remove border
            print(f"Added {brand_config['name']} solid white background")
            
        elif 'background_image' in brand_config:
            # Buick and GMC use background images
            try:
                if os.path.exists(brand_config['background_image']):
                    slide.shapes.add_picture(
                        brand_config['background_image'], 
                        Inches(0), Inches(0),
                        width=Inches(13.33), height=Inches(7.5)
                    )
                    print(f"Added {brand_config['name']} background image")
                else:
                    print(f"Background image not found: {brand_config['background_image']}")
            except Exception as e:
                print(f"Background image error: {e}")
    
    def add_title_brand_logo(self, slide, brand_config):
        """Add brand logo for title slides"""
        try:
            if os.path.exists(brand_config['logo_path']):
                logo_picture = slide.shapes.add_picture(
                    brand_config['logo_path'],
                    self.pixels_to_inches(brand_config['logo_position']['x']),
                    self.pixels_to_inches(brand_config['logo_position']['y']),
                    height=self.pixels_to_inches(brand_config['logo_size']['height'])
                )
                
                actual_width_inches = logo_picture.width
                actual_width_pixels = int(actual_width_inches.inches * 96)
                
                print(f"Added {brand_config['name']} logo at position ({brand_config['logo_position']['x']}, {brand_config['logo_position']['y']}) with height {brand_config['logo_size']['height']}px (width auto-calculated: {actual_width_pixels}px)")
            else:
                print(f"{brand_config['name']} logo not found: {brand_config['logo_path']}")
        except Exception as e:
            print(f"{brand_config['name']} logo error: {e}")
    
    def add_mrg_logo(self, slide, position='title'):
        """
        Add MRG logo
        
        Args:
            slide: PowerPoint slide object
            position (str): 'title' for title slide position, 'data' for data slide position
        """
        try:
            mrg_logo_path = self.brand_configs.get_mrg_logo_path()
            if not os.path.exists(mrg_logo_path):
                print(f"MRG logo not found: {mrg_logo_path}")
                return
            
            if position == 'title':
                # Title slide positioning
                slide.shapes.add_picture(
                    mrg_logo_path,
                    self.pixels_to_inches(1039),
                    self.pixels_to_inches(645),
                    width=self.pixels_to_inches(240),
                    height=self.pixels_to_inches(73)
                )
                print("Added MRG logo (title position)")
                
            elif position == 'data':
                # Data slide positioning (top next to brand logo)
                slide.shapes.add_picture(
                    mrg_logo_path,
                    self.pixels_to_inches(109.44),
                    self.pixels_to_inches(0),
                    width=self.pixels_to_inches(148.8),
                    height=self.pixels_to_inches(38.4)
                )
                print("Added MRG logo (data position)")
                
        except Exception as e:
            print(f"MRG logo error: {e}")
    
    def add_gm_confidential(self, slide, brand_config, position='title'):
        """
        Add GM Confidential text
        
        Args:
            slide: PowerPoint slide object
            brand_config: Brand configuration dictionary
            position (str): 'title' or 'data' for different positioning
        """
        if position == 'title':
            x, y = self.pixels_to_inches(1113), self.pixels_to_inches(17)
        else:  # data slide
            x, y = self.pixels_to_inches(1113), self.pixels_to_inches(17)
        
        gm_conf_textbox = slide.shapes.add_textbox(
            x, y,
            self.pixels_to_inches(166),
            self.pixels_to_inches(38)
        )
        
        gm_conf_frame = gm_conf_textbox.text_frame
        gm_conf_frame.clear()
        gm_conf_paragraph = gm_conf_frame.paragraphs[0]
        gm_conf_paragraph.text = "GM CONFIDENTIAL"
        gm_conf_paragraph.alignment = PP_ALIGN.LEFT
        
        gm_conf_run = gm_conf_paragraph.runs[0]
        gm_conf_run.font.name = "Segoe UI"
        gm_conf_run.font.size = Pt(12)
        gm_conf_run.font.color.rgb = brand_config['gm_confidential_color']
        print(f"Added GM Confidential text with {brand_config['name']}-specific color")
    
    def add_title_text(self, slide, brand_config, market_name, zone_lma_type):
        """Add title text for title slides"""
        title_textbox = slide.shapes.add_textbox(
            self.pixels_to_inches(72),
            self.pixels_to_inches(168),
            self.pixels_to_inches(669),
            self.pixels_to_inches(215)
        )
        
        title_frame = title_textbox.text_frame
        title_frame.clear()
        title_paragraph = title_frame.paragraphs[0]
        title_run = title_paragraph.add_run()

        # Dynamic title based on zone/LMA type
        dynamic_title = self._determine_title_text(market_name, zone_lma_type)
        title_run.text = dynamic_title
        
        title_run = title_paragraph.runs[0]
        title_run.font.name = brand_config['primary_font']
        title_run.font.size = Pt(60)
        title_run.font.bold = True
        title_run.font.color.rgb = brand_config['text_color_dark']
        print(f"Added title text with {brand_config['name']} font: '{dynamic_title.replace(chr(10), ' / ')}'")
    
    def add_title_line(self, slide, brand_config):
        """Add brand color horizontal line for title slides"""
        line_shape = slide.shapes.add_connector(
            1,  # Straight line
            self.pixels_to_inches(72),
            self.pixels_to_inches(394),
            self.pixels_to_inches(891),
            self.pixels_to_inches(394)
        )
        
        line_shape.line.color.rgb = brand_config['line_color']
        line_shape.line.width = Pt(brand_config['line_width'])
        line_shape.shadow.inherit = False
        
        print(f"Added {brand_config['name']} accent line")
    
    def add_market_info(self, slide, brand_config, market_name, month_year):
        """Add market name and month information for title slides"""
        market_textbox = slide.shapes.add_textbox(
            self.pixels_to_inches(57),
            self.pixels_to_inches(424),
            self.pixels_to_inches(1222),
            self.pixels_to_inches(172)
        )
        
        market_frame = market_textbox.text_frame
        market_frame.clear()
        market_frame.word_wrap = True
        
        # First line: Market name
        market_paragraph1 = market_frame.paragraphs[0]
        market_paragraph1.text = market_name.upper() if market_name else "MARKET NAME"
        market_run1 = market_paragraph1.runs[0]
        market_run1.font.name = brand_config['accent_font']
        market_run1.font.size = Pt(34)
        market_run1.font.bold = True
        market_run1.font.color.rgb = brand_config['text_color_darker']
        
        # Second line: Month year
        market_paragraph2 = market_frame.add_paragraph()
        market_paragraph2.text = month_year
        market_run2 = market_paragraph2.runs[0]
        market_run2.font.name = brand_config['accent_font']
        market_run2.font.size = Pt(34)
        market_run2.font.bold = True
        market_run2.font.color.rgb = brand_config['text_color_darker']
        
        print(f"Added market name and month with {brand_config['name']} styling")
    
    # ========== DATA SLIDE ELEMENTS ==========
    
    def add_data_background(self, slide, brand_config):
        """Add background image for data slides with brand-specific rules"""
        
        brand_name = brand_config['name'].lower()
        
        # Define data slide background paths and transparency rules
        if brand_name == 'buick':
            data_background_path = os.path.join(self.brand_configs.base_path, "Design", "Background Images", "Buick background 2025.jpg")
            transparency = 0.0  # No transparency for Buick
        elif brand_name == 'gmc':
            data_background_path = os.path.join(self.brand_configs.base_path, "Design", "Background Images", "GMC background 2025_transparency.png")
            transparency = 0.3  # 30% transparency for GMC
        elif brand_name in ['chevrolet', 'cadillac']:
            # Use same background as title slides for Chevy and Cadillac
            data_background_path = brand_config.get('background_image', None)
            transparency = 0.0  # No transparency
        else:
            # Fallback to title slide background
            data_background_path = brand_config.get('background_image', None)
            transparency = 0.0
        
        # Handle Chevy and Cadillac special cases (solid colors instead of images)
        if brand_name == 'chevrolet':
            # Chevrolet uses solid white background (same as title)
            background_shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(0), Inches(0),
                width=Inches(13.33), height=Inches(7.5)
            )
            background_shape.fill.solid()
            background_shape.fill.fore_color.rgb = RGBColor(255, 255, 255)  # White
            background_shape.line.fill.background()
            print(f"Added {brand_config['name']} solid white background for data slide")
            return
            
        elif brand_name == 'cadillac':
            # Cadillac uses solid black background (same as title)
            background_shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(0), Inches(0),
                width=Inches(13.33), height=Inches(7.5)
            )
            background_shape.fill.solid()
            background_shape.fill.fore_color.rgb = RGBColor(0, 0, 0)  # Black
            background_shape.line.fill.background()
            print(f"Added {brand_config['name']} solid black background for data slide")
            return
        
        # Add image background for Buick and GMC
        try:
            if data_background_path and os.path.exists(data_background_path):
                background_pic = slide.shapes.add_picture(
                    data_background_path,
                    Inches(0), Inches(0),
                    width=Inches(13.33), height=Inches(7.5)
                )
                
                # Apply transparency if specified
                if transparency > 0:
                    try:
                        pic_element = background_pic._element
                        blip_fill = pic_element.blipFill
                        if blip_fill is not None:
                            blip_fill.alpha = int((1 - transparency) * 100000)
                            print(f"Added {brand_config['name']} data background with {int(transparency*100)}% transparency")
                    except AttributeError:
                        print(f"Added {brand_config['name']} data background (transparency not supported for this image type)")
                else:
                    print(f"Added {brand_config['name']} data background with no transparency")
            else:
                print(f"Data background image not found: {data_background_path}")
            
        except Exception as e:
            print(f"Error adding data background for {brand_config['name']}: {e}")
    
    def add_data_brand_logo(self, slide, brand_config):
        """Add brand logo for data slides (top left position)"""
        try:
            if brand_config.get('logo_path') and os.path.exists(brand_config['logo_path']):
                if brand_config['name'].lower() == 'cadillac':
                    # Cadillac logo maintain aspect ratio, final position adjustment
                    brand_logo = slide.shapes.add_picture(
                        brand_config['logo_path'],
                        self.pixels_to_inches(25),
                        self.pixels_to_inches(-4),      
                        height=self.pixels_to_inches(50)
                    )
                else:
                    brand_logo = slide.shapes.add_picture(
                        brand_config['logo_path'],
                        self.pixels_to_inches(1.92),
                        self.pixels_to_inches(0),      
                        width=self.pixels_to_inches(97.92),
                        height=self.pixels_to_inches(38.4)
                    )
                print(f"Added data slide brand logo")
            else:
                print(f"Brand logo not found: {brand_config.get('logo_path')}")
        except Exception as e:
            print(f"Error adding brand logo: {e}")
        
    def add_data_logo_divider(self, slide, brand_config):
        """Add vertical divider line between brand and MRG logos"""
        try:
            divider_line = slide.shapes.add_connector(
                1,  # Straight line
                self.pixels_to_inches(104.64), 
                self.pixels_to_inches(5.76),
                self.pixels_to_inches(104.64),
                self.pixels_to_inches(33.6)
            )
            
            # Use white for Cadillac, default gray for other brands
            if brand_config.get('name', '').lower() == 'cadillac':
                divider_line.line.color.rgb = RGBColor(255, 255, 255)  # #FFFFFF - White
            else:
                divider_line.line.color.rgb = RGBColor(85, 86, 90)  # #55565A - Gray
            
            divider_line.line.width = self.pixels_to_inches(2)
            divider_line.shadow.inherit = False
            print("Added divider line between logos")
        except Exception as e:
            print(f"Error adding divider line: {e}")
    
    def add_data_slide_title(self, slide, market_name, subtitle, brand_config):
        """Add title section to data slides (market name + subtitle)"""
        # Add Market Name Header (centered)
        market_header = slide.shapes.add_textbox(
            self.pixels_to_inches(0),
            self.pixels_to_inches(32),
            self.pixels_to_inches(1280),
            self.pixels_to_inches(64)
        )
        market_frame = market_header.text_frame
        market_frame.text = market_name
        p = market_frame.paragraphs[0]
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.name = brand_config['primary_font']
        p.font.color.rgb = brand_config['text_color_dark']
        p.alignment = PP_ALIGN.CENTER
        
        # Add horizontal line under market name
        line_shape = slide.shapes.add_connector(
            1,
            self.pixels_to_inches(485),
            self.pixels_to_inches(88),
            self.pixels_to_inches(799),
            self.pixels_to_inches(88)
        )
        line_shape.line.color.rgb = brand_config['line_color']
        line_shape.line.width = self.pixels_to_inches(2)
        line_shape.shadow.inherit = False
        
        # Add subtitle (e.g., "YTD KBA Breakdown" or tactic name)
        subtitle_box = slide.shapes.add_textbox(
            self.pixels_to_inches(13),
            self.pixels_to_inches(94),
            self.pixels_to_inches(1255),
            self.pixels_to_inches(75)
        )
        subtitle_frame = subtitle_box.text_frame

        # NEW: Rename Display tactics just for the slide title as requested
        display_title_overrides = {
            "Consideration Display": "Consideration/HPA Display",
            "BT Display": "InMarket Display"
        }
        subtitle_display = display_title_overrides.get(subtitle, subtitle)
        
        subtitle_frame.text = subtitle_display
        p = subtitle_frame.paragraphs[0]
        p.font.size = Pt(40)
        p.font.bold = True
        p.alignment = PP_ALIGN.CENTER
        p.font.name = brand_config['primary_font']
        p.font.color.rgb = brand_config['text_color_dark']
        
        print(f"Added data slide title: {market_name} - {subtitle}")
    
    def add_audience_label(self, slide, audience_label, brand_config):
        """Add audience label for data slides"""
        audience_box = slide.shapes.add_textbox(
            self.pixels_to_inches(555),
            self.pixels_to_inches(160),
            self.pixels_to_inches(169),
            self.pixels_to_inches(38)
        )
        audience_frame = audience_box.text_frame
        audience_frame.text = audience_label
        p = audience_frame.paragraphs[0]
        p.font.size = Pt(18)
        p.alignment = PP_ALIGN.CENTER
        p.font.name = brand_config['primary_font']
        p.font.color.rgb = brand_config['text_color_dark']
        
        print(f"Added audience label: '{audience_label}'")
    
    def add_source_label(self, slide, brand_config, zone_lma_type, month_year):
        """
        Add source label in bottom left corner with consistent formatting
        
        Args:
            slide: PowerPoint slide object
            brand_config: Brand configuration dictionary
            zone_lma_type: Zone/LMA type (e.g., 'Zone', 'LMA', or full value like 'Zone Digital')
            month_year: Month and year (e.g., 'August 2025' or datetime object)
        """
        import pandas as pd
        
        # Normalize month_year to consistent format
        if isinstance(month_year, str):
            # Check if it's already in the right format (e.g., "August 2025")
            try:
                # Try to parse as datetime in case it's a date string
                month_dt = pd.to_datetime(month_year)
                formatted_month = month_dt.strftime('%B %Y')
            except:
                # If parsing fails, assume it's already formatted correctly
                formatted_month = month_year
        elif hasattr(month_year, 'strftime'):
            # It's a datetime object
            formatted_month = month_year.strftime('%B %Y')
        else:
            # Fallback
            formatted_month = str(month_year)
        
        # Normalize zone_lma_type to just "ZONE" or "LMA"
        if zone_lma_type and isinstance(zone_lma_type, str):
            zone_lma_upper = str(zone_lma_type).upper().strip()
            if "ZONE" in zone_lma_upper:
                zone_lma_clean = "ZONE"
            elif "LMA" in zone_lma_upper:
                zone_lma_clean = "LMA"
            else:
                zone_lma_clean = "LMA"  # Default fallback
        else:
            zone_lma_clean = "LMA"  # Default fallback
        
        # Build consistent label: "Source: {Brand} {ZONE/LMA} {Month Year}"
        brand_name = brand_config['name']
        label_text = f"Source: {brand_name} {zone_lma_clean} {formatted_month}"
        
        # Add label textbox in bottom left corner
        label_box = slide.shapes.add_textbox(
            self.pixels_to_inches(0),
            self.pixels_to_inches(686),
            self.pixels_to_inches(250),
            self.pixels_to_inches(26)
        )
        
        label_frame = label_box.text_frame
        label_frame.text = label_text
        label_frame.word_wrap = False
        
        p = label_frame.paragraphs[0]
        p.font.size = Pt(10)
        p.font.name = brand_config.get('accent_font', 'Segoe UI')
        p.font.color.rgb = brand_config['text_color_dark']
        p.alignment = PP_ALIGN.LEFT
        
        print(f"Added source label: '{label_text}'")
    
    # ========== COMPLETE SLIDE ASSEMBLY ==========
    
    def build_title_slide(self, slide, brand_name, market_name, month_year, zone_lma_type=None):
        """
        Build complete title slide layout
        
        Args:
            slide: PowerPoint slide object
            brand_name: Name of the brand
            market_name: Market/LMA name
            month_year: Month and year string
            zone_lma_type: Optional zone/LMA type indicator
        """
        brand_config = self.brand_configs.get_brand_config(brand_name)
        
        # Add all title slide elements
        self.add_title_background(slide, brand_name, brand_config)
        self.add_title_brand_logo(slide, brand_config)
        self.add_mrg_logo(slide, position='title')
        self.add_gm_confidential(slide, brand_config, position='title')
        self.add_title_text(slide, brand_config, market_name, zone_lma_type)
        self.add_title_line(slide, brand_config)
        self.add_market_info(slide, brand_config, market_name, month_year)
        
        print(f"Built complete title slide for {brand_name}")
    
    def build_data_slide_structure(self, slide, brand_name, market_name, month_year, 
                                   tactic, audience_label, zone_lma_type=None):
        """
        Build complete data slide structure (without data visualizations)
        
        Args:
            slide: PowerPoint slide object
            brand_name: Name of the brand
            market_name: Market/LMA name
            month_year: Month and year string
            tactic: Tactic name for subtitle
            audience_label: Audience segment label
            zone_lma_type: Optional zone/LMA type indicator
        """
        brand_config = self.brand_configs.get_brand_config(brand_name, tactic=tactic)
        
        # Add all structural elements
        self.add_data_background(slide, brand_config)
        self.add_data_brand_logo(slide, brand_config)
        self.add_data_logo_divider(slide, brand_config)
        self.add_mrg_logo(slide, position='data')
        self.add_gm_confidential(slide, brand_config, position='data')
        self.add_data_slide_title(slide, market_name, tactic, brand_config)
        self.add_audience_label(slide, audience_label, brand_config)
        self.add_source_label(slide, brand_config, zone_lma_type, month_year)
        
        print(f"Built complete data slide structure for {brand_name} - {tactic}")