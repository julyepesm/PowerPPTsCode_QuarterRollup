"""
Slide Components Module

This module handles all data visualization components:
- Metric boxes (KPI displays)
- Tables (KBA breakdown)
- Charts (combination bar + line charts)
- Benchmark labels
- Data formatting utilities

These are reusable "widgets" that can be placed on any slide.
"""

import math
import pandas as pd
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_DATA_LABEL_POSITION
from lxml import etree
from pptx.oxml.ns import qn
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Not Graphs Window
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from io import BytesIO
import matplotlib.font_manager as fm
import os
import glob
from error_collector import ErrorCollector

class SlideComponents:
    """Manages data visualization components for PowerPoint slides"""
    
    def _register_brand_fonts(self):
        """Register brand fonts with matplotlib — delegates to shared utils"""
        from utils import register_brand_fonts
        register_brand_fonts(self.base_path)


    def _get_safe_font(self, font_name):
        """Get matplotlib-safe font family and weight — delegates to shared utils"""
        from utils import get_safe_font
        return get_safe_font(font_name)
    
    def _rgb_to_matplotlib(self, rgb_color):
        """Convert RGBColor to matplotlib format (0-1) — delegates to shared utils"""
        from utils import rgb_to_matplotlib
        return rgb_to_matplotlib(rgb_color)


    def _add_chart_image_to_slide(self, slide, img_stream):
        """Add matplotlib chart image to slide"""
        left = Inches(6.82)
        top = Inches(3.9)  # Moved down to accommodate increased title padding
        
        slide.shapes.add_picture(img_stream, left, top, 
                                width=Inches(6.3), 
                                height=Inches(3.42))


    def __init__(self, brand_configs, tactic_config, base_path=None):
        """
        Initialize with brand and tactic configurations
        
        Args:
            brand_configs: BrandConfigurations instance
            tactic_config: TacticConfig instance
            base_path: Base path for fonts and resources
        """
        self.brand_configs = brand_configs
        self.tactic_config = tactic_config
        
        # Set base_path - try to get from brand_configs first, otherwise use parameter or current directory
        if hasattr(brand_configs, 'base_path'):
            self.base_path = brand_configs.base_path
        elif base_path:
            self.base_path = base_path
        else:
            self.base_path = os.path.dirname(os.path.dirname(__file__))  # Go up one level from Scripts
        
        print(f"  Using base_path: {self.base_path}")
        
        self._register_brand_fonts()

        
    # ========== UTILITY METHODS ==========
    
    def pixels_to_inches(self, pixels):
        """Convert pixels to inches — delegates to shared utils"""
        from utils import pixels_to_inches
        return pixels_to_inches(pixels)
    
    def format_number(self, value):
        """Format numbers for display (e.g., 7575968 -> 7,575,968)"""
        if pd.isna(value) or value is None:
            return "N/A"
        try:
            return f"{math.floor(float(value) + 0.5):,}"
        except (ValueError, TypeError):
            return str(value)
    
    def format_percentage(self, value):
        """Format percentages (e.g., 0.98 -> 98%)"""
        if pd.isna(value) or value is None:
            return "N/A"
        try:
            # Handle both decimal (0.98) and percentage (98) formats
            if value <= 1.0:
                return f"{math.floor(value * 100 + 0.5)}%"
            else:
                return f"{math.floor(value + 0.5)}%"
        except (ValueError, TypeError):
            return str(value)
    
    def format_metric_value(self, value, metric_key):
        """
        Format metric value based on type
        
        Args:
            value: Raw metric value
            metric_key: Metric identifier (e.g., 'impressions', 'vcr', 'cpcv')
        
        Returns:
            Formatted string
        """
        # Handle None or empty values
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "0"
        
        # Convert to float if possible
        try:
            value = float(value)
        except (ValueError, TypeError):
            return str(value)
        
        # Format based on metric type
        if metric_key in ['vcr', 'ctr', 'viewability', 'acr', 'yt_viewability']:
            # Percentage metrics - multiply by 100 and add %
            return f"{math.floor(value * 100 + 0.5)}%"
        elif metric_key == 'cpcv':
             # User requested 3 decimal precision for CPCV (e.g. $0.014)
             return f"${value:.3f}"
        elif metric_key in ['cpm', 'cpv', 'cpc', 'cpa']:
            # Cost metrics - add $ and format to 2 decimals
            return f"${value:.2f}"
        else:
            # Count metrics - format with commas
            return f"{math.floor(value + 0.5):,}"
        
    def _format_chart_value(self, value, metric_key):
        """Format chart values based on metric type (for matplotlib)"""
        if metric_key in ['cpcv']:
            return f"${value:.3f}"
        elif metric_key in ['cpa', 'cpc', 'cpm']:
            return f"${value:.2f}"
        elif metric_key in ['vcr', 'ctr', 'viewability', 'acr', 'yt_viewability']:
            # Assume value is already in percentage form (0.XX) unless it's way larger (>10)
            # This handles the case where padding pushes a 1.0 (100%) value slightly higher (e.g. 1.05)
            # We treat anything <= 10.0 (1000%) as a ratio, not a raw percentage number
            if value <= 10.0:
                return f"{value:.1%}"  # Will show as XX.X%
            else:
                return f"{value:.1f}%"
        else:
            return f"{math.floor(value + 0.5):,}"
        
    # ========== METRIC BOXES ==========
    
    def add_metric_boxes(self, slide, current_metrics, brand_config, tactic, strategy=None, brand=None, audience=None):
        """
        Add top metrics row - dynamically based on tactic
        
        Args:
            slide: PowerPoint slide object
            current_metrics: DataFrame with current period metrics
            brand_config: Brand configuration dictionary
            tactic: Tactic name
            strategy: Optional strategy for Display tactic splitting
            brand: Brand name for benchmark lookup
            audience: Audience segment for benchmark lookup
        """
        metrics_config = self.tactic_config.get_tactic_metrics(tactic, strategy)
        
        # Get benchmarks to check for TBD overrides
        benchmarks = []
        if brand and audience:
            try:
                benchmarks = self.tactic_config.get_tactic_benchmarks(tactic, strategy, brand=brand, audience=audience)
            except Exception as e:
                print(f"  [WARN] Could not fetch benchmarks for TBD check: {e}")
        
        # Extract metric values from DataFrame
        metric_values = self._extract_metric_values(current_metrics)
        
        # Determine layout (3 or 4 boxes)
        uses_four_boxes = self.tactic_config.uses_four_metric_boxes(tactic, strategy)
        
        if uses_four_boxes:
            # Four metric boxes - evenly spaced
            # Tweaked to fit within margins with slight gaps
            box_width = Inches(3.0) 
            gap = Inches(0.2)
            start_x = Inches(0.21)
            
            x_positions = [
                start_x, 
                start_x + box_width + gap, 
                start_x + (box_width + gap) * 2, 
                start_x + (box_width + gap) * 3
            ]
            box_height = Inches(1.46)
        else:
            # Three metric boxes - Widened to occupy more horizontal space (User Request)
            # Increased width to 400px, reduced gap to 20px
            
            box_width = self.pixels_to_inches(400)
            gap = self.pixels_to_inches(20)
            start_x = self.pixels_to_inches(20.16)
            
            x_positions = [
                start_x,
                start_x + box_width + gap,
                start_x + (box_width + gap) * 2
            ]
            box_height = self.pixels_to_inches(140.16)
        
        # Create metric boxes
        for idx, (label, metric_key) in enumerate(metrics_config):
            if idx >= len(x_positions):
                break
                
            value = metric_values.get(metric_key, 0)
            x_pos = x_positions[idx]
            
            # Create metric box
            metric_box = slide.shapes.add_textbox(
                x_pos,
                self.pixels_to_inches(216),    
                box_width,  
                box_height    
            )
            
            # Add brand-specific styling
            self._style_metric_box(metric_box, brand_config)
            
            metric_frame = metric_box.text_frame
            metric_frame.word_wrap = True
            metric_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            
            # Format value based on metric type
            formatted_value = self.format_metric_value(value, metric_key)
            
            # Add label paragraph
            p_label = metric_frame.paragraphs[0]
            p_label.text = label
            p_label.font.size = Pt(20)
            p_label.font.name = brand_config['primary_font']
            p_label.alignment = PP_ALIGN.CENTER
            p_label.font.color.rgb = brand_config['text_color_dark']
            p_label.space_after = Pt(2) # Reduced to 2 to bring value closer to label
            
            # Add value paragraph
            p_value = metric_frame.add_paragraph()
            p_value.text = formatted_value
            p_value.font.size = Pt(35)
            p_value.font.bold = True
            p_value.font.name = brand_config['primary_font']
            p_value.alignment = PP_ALIGN.CENTER
            p_value.font.color.rgb = brand_config['text_color_dark']
        
        # Add divider lines between boxes
        self._add_metric_box_dividers(slide, brand_config, uses_four_boxes)
        
        print(f"Added {len(metrics_config)} metric boxes for {tactic}")

    def _style_metric_box(self, metric_box, brand_config):
        """
        Apply brand-specific styling to metric box
        
        Handles:
        - Fill color (brand-specific)
        - Border (Buick only)
        
        Args:
            metric_box: PowerPoint shape object
            brand_config: Brand configuration dictionary
        """
        from pptx.util import Pt
        from pptx.dml.color import RGBColor
        
        # Get metric box config with defaults
        metric_box_config = brand_config.get('metric_box', {
            'fill_color': RGBColor(235, 235, 235),  # Default gray
            'has_border': False
        })
        
        # Add solid fill
        metric_box.fill.solid()
        metric_box.fill.fore_color.rgb = metric_box_config['fill_color']
        
        # Handle border
        if metric_box_config.get('has_border', False):
            # Add border with specified color and width
            metric_box.line.color.rgb = metric_box_config['border_color']
            metric_box.line.width = Pt(metric_box_config.get('border_width', 1))
        else:
            # Remove border
            metric_box.line.fill.background()
        
        print(f"  Styled metric box: {brand_config['name']}")
    
    def _extract_metric_values(self, current_metrics):
        """Extract all possible metric values from DataFrame"""
        if current_metrics is None or current_metrics.empty:
            return {}
        
        try:
            row = current_metrics.iloc[0]
            
            # === HELPER FUNCTION ===
            def clean_value(value):
                """Clean value - handle sets and convert to proper type"""
                if isinstance(value, set):
                    print(f"  WARNING: Metric value is a set: {value}")
                    if len(value) > 0:
                        value = list(value)[0]
                    else:
                        return 0
                return value
            # === END HELPER ===
            
            # DEBUG: Print what columns are available
            print(f"  DEBUG: Available columns: {list(row.index)}")
            
            # Extract base metrics with cleaning
            impressions = clean_value(row.get('[Impressions]', 0))
            clicks = clean_value(row.get('[Clicks]', 0))
            video_completions = clean_value(row.get('[Video Completions]', 0))
            audio_completes = clean_value(row.get('[Audio Completes]', 0))
            total_conversions = clean_value(row.get('[Total Conversions]', 0))
            total_cost = clean_value(row.get('[Total Cost]', 0))
            
            print(f"  DEBUG: Total Conversions: {total_conversions}")
            print(f"  DEBUG: Total Cost: {total_cost}")
            
            # Get or calculate CPA
            cpa_from_df = row.get('CPA', None)
            print(f"  DEBUG: CPA from dataframe: {cpa_from_df}")
            
            cpa = clean_value(cpa_from_df)
            
            if cpa is None or pd.isna(cpa) or cpa == 0:
                # Calculate: CPA = Total Cost / Total Conversions
                if total_conversions > 0 and total_cost > 0:
                    cpa = total_cost / total_conversions
                    print(f"  [OK] Calculated CPA: ${cpa:.2f} (Cost: ${total_cost:.2f} / Conversions: {total_conversions})")
                else:
                    cpa = 0
                    print(f"  [WARN] CPA = 0 because Total Conversions = {total_conversions} or Total Cost = {total_cost}")
            else:
                print(f"  [OK] Using existing CPA from dataframe: ${cpa:.2f}")
            
            return {
                'impressions': impressions,
                'clicks': clicks,
                'video_completions': video_completions,
                'audio_completes': audio_completes,
                'total_conversions': total_conversions,
                'vcr': clean_value(row.get('VCR', 0)),
                'viewability': clean_value(row.get('Viewability', None)),
                'yt_viewability': clean_value(row.get('YT Viewability', None)),
                'cpa': cpa,
                'cpc': clean_value(row.get('CPC', 0)),
                'cpcv': clean_value(row.get('CPCV', 0)),
                'acr': clean_value(row.get('ACR', 0))
            }
        except (KeyError, IndexError, AttributeError) as e:
            print(f"  [X] Metric extraction error: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _add_metric_box_dividers(self, slide, brand_config, uses_four_boxes):
        """Add vertical divider lines between metric boxes"""
        if uses_four_boxes:
            # Four boxes - three divider lines
            # Recalculated to be perfectly centered in gaps:
            # Box1 Ends: 3.21", Box2 Starts: 3.41" -> Center: 3.31"
            # Box2 Ends: 6.41", Box3 Starts: 6.61" -> Center: 6.51"
            # Box3 Ends: 9.61", Box4 Starts: 9.81" -> Center: 9.71"
            positions = [
                (Inches(3.31), Inches(2.25), Inches(3.31), self.pixels_to_inches(356.16)),
                (Inches(6.51), Inches(2.25), Inches(6.51), self.pixels_to_inches(356.16)),
                (Inches(9.71), Inches(2.25), Inches(9.71), self.pixels_to_inches(356.16))
            ]
        else:
            # Three boxes - two divider lines
            # Updated to match new 400px width / 20px gap
            # Divider 1: Start (20.16) + width (400) + gap/2 (10) = 430.16
            # Divider 2: Start (20.16) + width (400) + gap (20) + width (400) + gap/2 (10) = 850.16
            
            positions = [
                (self.pixels_to_inches(430.16), self.pixels_to_inches(216), 
                 self.pixels_to_inches(430.16), self.pixels_to_inches(356.16)),
                (self.pixels_to_inches(850.16), self.pixels_to_inches(216), 
                 self.pixels_to_inches(850.16), self.pixels_to_inches(356.16))
            ]
        
        for x1, y1, x2, y2 in positions:
            line = slide.shapes.add_connector(1, x1, y1, x2, y2)
            line.line.color.rgb = brand_config['line_color']
            line.line.width = self.pixels_to_inches(2)
            line.shadow.inherit = False
    
    # ========== BENCHMARK LABELS ==========
    
    def add_benchmark_labels(self, slide, brand_config, tactic, strategy=None, brand='GMC', audience='GEN'):
        """Add benchmark labels below specific metric boxes based on tactic"""
        
        # Pass brand and audience to get brand-specific benchmarks
        benchmarks = self.tactic_config.get_tactic_benchmarks(tactic, strategy, brand=brand, audience=audience)
        
        if not benchmarks:
            print(f"No benchmarks defined for {brand} - {tactic}")
            return
    
        # Determine layout
        uses_four_boxes = self.tactic_config.uses_four_metric_boxes(tactic, strategy)
        
        if uses_four_boxes:
            # Match add_metric_boxes logic exactly
            box_width = Inches(3.0) 
            gap = Inches(0.2)
            start_x = Inches(0.21)
            
            x_positions = [
                start_x, 
                start_x + box_width + gap, 
                start_x + (box_width + gap) * 2, 
                start_x + (box_width + gap) * 3
            ]
        else:
            # Match add_metric_boxes logic exactly for 3 boxes
            box_width = self.pixels_to_inches(360)
            gap = self.pixels_to_inches(65)
            start_x = self.pixels_to_inches(20.16)
            
            x_positions = [
                start_x,
                start_x + box_width + gap,
                start_x + (box_width + gap) * 2
            ]
        
        # Y position: within metric boxes
        benchmark_y = self.pixels_to_inches(325)
        benchmark_height = self.pixels_to_inches(25)
        
        for benchmark_info in benchmarks:
            position_index = benchmark_info['position_index']
            
            if position_index >= len(x_positions):
                print(f"Warning: Invalid position index {position_index}")
                continue
            
            x_pos = x_positions[position_index]
            
            # Create benchmark text box
            benchmark_box = slide.shapes.add_textbox(
                x_pos, benchmark_y, box_width, benchmark_height
            )
            
            benchmark_frame = benchmark_box.text_frame
            benchmark_frame.text = f"{benchmark_info['benchmark']} Benchmark"
            benchmark_frame.word_wrap = False
            
            p = benchmark_frame.paragraphs[0]
            p.font.size = Pt(12)
            p.font.name = brand_config['primary_font']
            p.font.color.rgb = brand_config['text_color_dark']
            p.alignment = PP_ALIGN.CENTER
            
            print(f"Added benchmark label: {benchmark_info['metric']} - {benchmark_info['benchmark']}")
    
    # ========== KBA TABLE ==========
    
    def add_kba_table(self, slide, historical_data, brand_config, month_year):
        """Add KBA breakdown table with 6-month rolling data ending at selected month"""
        
        if historical_data is None or historical_data.empty:
            print("No historical data available for table")
            return
        
        # Add table title
        title_box = slide.shapes.add_textbox(
            self.pixels_to_inches(12),
            self.pixels_to_inches(373),
            self.pixels_to_inches(618),
            self.pixels_to_inches(25)
        )
        title_frame = title_box.text_frame
        title_frame.text = "KBA Breakdown"
        p = title_frame.paragraphs[0]
        p.font.size = Pt(14)  # Restored from 12 back to 14
        p.font.bold = True
        p.font.name = brand_config['primary_font']
        p.font.color.rgb = brand_config['text_color_dark']
        p.alignment = PP_ALIGN.CENTER
        
        # Filter data to 6-month rolling window
        filtered_data = self._filter_historical_data(historical_data, month_year)
        
        if filtered_data.empty:
            print("No data available for selected month range")
            return
        
        # Create and populate table
        table = self._create_kba_table_structure(slide, len(filtered_data))
        self._populate_kba_table(table, filtered_data, brand_config)
        self._add_kba_table_lines(slide, brand_config, len(filtered_data))
        
        print("Added KBA breakdown table with dynamic 6-month rolling window")
    
    def _filter_historical_data(self, historical_data, month_year):
        """
        Prepare historical data for rendering.
        
        NOTE: Heavy data preparation (aggregation, 6-month window filtering,
        $0 cost filtering) is now centralized in main_slide_generator.py.
        This method only does defensive checks for data that may arrive
        without prior preparation (e.g. direct calls or tests).
        """
        if historical_data is None or historical_data.empty:
            return pd.DataFrame()
        
        # Defensive: ensure parsed_date exists
        if 'parsed_date' not in historical_data.columns:
            month_col = 'Master Date Table[Month Year]'
            if month_col in historical_data.columns:
                historical_data = historical_data.copy()
                historical_data['parsed_date'] = pd.to_datetime(historical_data[month_col])
            else:
                print(f"  [WARN] No date column found in historical data")
                return pd.DataFrame()
        
        # Defensive: if data hasn't been sorted yet, sort it
        result = historical_data.sort_values('parsed_date', ascending=True)
        
        if not result.empty:
            actual_months = result['parsed_date'].dt.strftime('%B %Y').tolist()
            print(f"  Rendering {len(result)} months: {', '.join(actual_months)}")
        
        return result
    
    def _create_kba_table_structure(self, slide, num_rows):
        """Create the table structure with responsive row heights based on font size 11"""
        columns = [
            'Month', 'Click to Calls', 'Email Leads', 'Hours & Directions',
            'Inventory Searches', 'VDP Views', 'Window Stickers', 'Total KBAs'
        ]
        
        # Responsive table centered within 6.35" red lines with minimal symmetric margins
        # Table: 605px (6.30"), Margins: 2.5px each side
        table_left = self.pixels_to_inches(27)
        # Higher clearance grid starting at 415 (First adjustment version)
        table_top = self.pixels_to_inches(415)
        table_width = self.pixels_to_inches(605)  # Updated to match sum of columns (600 -> 610)
        
        # Row heights from first adjustment
        header_height = self.pixels_to_inches(30)
        row_height = self.pixels_to_inches(28)
        
        rows = num_rows + 1  # +1 for header
        cols = len(columns)
        
        # Calculate table height based on number of rows
        table_height = header_height + (row_height * num_rows)
        
        table = slide.shapes.add_table(rows, cols, table_left, table_top, table_width, table_height).table
        
        # Set fixed height for each row
        table.rows[0].height = header_height
        for i in range(1, len(table.rows)):
            table.rows[i].height = row_height
        
        # Set column widths (proportional to 610px width)
        table.columns[0].width = self.pixels_to_inches(80)  # Month (Reduced from 85)
        table.columns[1].width = self.pixels_to_inches(75)  # Click to Calls
        table.columns[2].width = self.pixels_to_inches(65)  # Email Leads
        table.columns[3].width = self.pixels_to_inches(85)  # Hours & Directions
        table.columns[4].width = self.pixels_to_inches(85)  # Inventory Searches
        table.columns[5].width = self.pixels_to_inches(65)  # VDP Views
        table.columns[6].width = self.pixels_to_inches(75)  # Window Stickers (Restored to 75)
        table.columns[7].width = self.pixels_to_inches(80)  # Total KBAs (Increased from 65)
        
        print(f"  Created table with {num_rows} data rows (each 30px high)")
        
        return table
    
    def _populate_kba_table(self, table, filtered_data, brand_config):
        """Populate table with data"""
        columns = [
            'Month', 'Click to Calls', 'Email Leads', 'Hours & Directions',
            'Inventory Searches', 'VDP Views', 'Window Stickers', 'Total KBAs'
        ]
        
        # DEBUG: Print what's in filtered_data
        print(f"\n=== DEBUG: KBA Table Data ===")
        print(f"Number of rows: {len(filtered_data)}")
        if 'parsed_date' in filtered_data.columns:
            for idx, row in filtered_data.iterrows():
                month_str = row['parsed_date'].strftime('%B %Y')  # Include year
                total = row.get('[Total Conversions]', 0)
                print(f"  Row {idx}: {month_str} - Total: {total}")
        print(f"=== END DEBUG ===\n")
        
        # Remove all cell borders
        self._remove_table_borders(table)
        
        # Style header row
        for col_idx, col_name in enumerate(columns):
            cell = table.rows[0].cells[col_idx]
            cell.text = col_name
            cell.fill.background()
            
            text_frame = cell.text_frame
            p = text_frame.paragraphs[0]
            p.font.size = Pt(10) # Restored from 8
            p.font.bold = True
            p.font.name = brand_config['primary_font']
            p.font.color.rgb = brand_config['text_color_dark']
            p.alignment = PP_ALIGN.CENTER
            p.space_before = Pt(0)
            p.space_after = Pt(0)
            
            # Minimize text frame margins for responsive tight fit
            text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            text_frame.word_wrap = False
            text_frame.margin_left = Pt(3)
            text_frame.margin_right = Pt(3)
            text_frame.margin_top = Pt(3)
            text_frame.margin_bottom = Pt(3)

            # Cell margins - balanced to center content
            cell.margin_top = Pt(4)
            cell.margin_bottom = Pt(4)
            cell.margin_left = Pt(3)
            cell.margin_right = Pt(3)
        
        # Fill data rows
        for row_idx, (_, row_data) in enumerate(filtered_data.iterrows(), start=1):
            month_str = row_data['parsed_date'].strftime('%b %Y')  # MMM YYYY format
            
            row_values = [
                month_str,
                f"{math.floor(row_data.get('[Click to Calls]', 0) + 0.5):,}",
                f"{math.floor(row_data.get('[Email Leads]', 0) + 0.5):,}",
                f"{math.floor(row_data.get('[Hours & Directions]', 0) + 0.5):,}",
                f"{math.floor(row_data.get('[Inventory Searches]', 0) + 0.5):,}",
                f"{math.floor(row_data.get('[VDP Views]', 0) + 0.5):,}",
                f"{math.floor(row_data.get('[Window Stickers]', 0) + 0.5):,}",
                f"{math.floor(row_data.get('[Total Conversions]', 0) + 0.5):,}"
            ]
            
            for col_idx, value in enumerate(row_values):
                cell = table.rows[row_idx].cells[col_idx]
                cell.text = str(value)
                cell.fill.background()
                
                text_frame = cell.text_frame
                p = text_frame.paragraphs[0]
                p.font.size = Pt(10.9) # Restored from 8.5
                p.font.bold = True
                p.font.name = brand_config['primary_font']
                p.font.color.rgb = brand_config['text_color_dark']
                p.alignment = PP_ALIGN.CENTER
                p.space_before = Pt(0)
                p.space_after = Pt(0)
                
                 # Minimize text frame margins for responsive tight fit
                text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
                text_frame.word_wrap = False  # Prevent wrapping for large numbers
                text_frame.margin_left = Pt(3)
                text_frame.margin_right = Pt(3)
                text_frame.margin_top = Pt(3)
                text_frame.margin_bottom = Pt(3)

                # Cell margins - balanced to center content
                cell.margin_top = Pt(4)
                cell.margin_bottom = Pt(4)
                cell.margin_left = Pt(3)
                cell.margin_right = Pt(3)
    
    def _remove_table_borders(self, table):
        """Remove all borders from table cells"""
        for row in table.rows:
            for cell in row.cells:
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                
                # Remove existing borders
                for border_tag in ['{http://schemas.openxmlformats.org/drawingml/2006/main}lnL',
                                 '{http://schemas.openxmlformats.org/drawingml/2006/main}lnR',
                                 '{http://schemas.openxmlformats.org/drawingml/2006/main}lnT',
                                 '{http://schemas.openxmlformats.org/drawingml/2006/main}lnB']:
                    for elem in list(tcPr):
                        if elem.tag == border_tag:
                            tcPr.remove(elem)
                
                # Add explicit "no fill" for all borders
                for border_tag in ['lnL', 'lnR', 'lnT', 'lnB']:
                    ln = etree.SubElement(tcPr, f'{{http://schemas.openxmlformats.org/drawingml/2006/main}}{border_tag}')
                    etree.SubElement(ln, '{http://schemas.openxmlformats.org/drawingml/2006/main}noFill')
    
    def _add_kba_table_lines(self, slide, brand_config, num_months):
        """
        Add horizontal lines to table dynamically based on number of months
        
        Args:
            slide: PowerPoint slide object
            brand_config: Brand configuration dictionary
            num_months: Number of month rows in the table
        """
        # Shift lines slightly right and down for better center alignment with text
        # Shifted an additional 5px right (18 -> 12)
        dx = 12
        dy = 2
        
        table_left = self.pixels_to_inches(26)  # Shifted from 18 to 12 for better alignment with text
        table_width = self.pixels_to_inches(610) # Updated to match new table width (610)
        
        # Must match _create_kba_table_structure exactly
        table_top = 419  # Original was 415, shifted down by 6px to align with text better
        header_height = 36  # Original was 30, increased to 36 to match increased font size and spacing
        row_height = 28
        
        # Always add header line (2px) if there's at least one month
        if num_months > 0:
            # Header line: Table Top (400) + Header Row Height (40) = 440
            header_y = self.pixels_to_inches(table_top + header_height + dy)
            header_line = slide.shapes.add_connector(
                1, table_left, header_y,
                table_left + table_width, header_y
            )
            header_line.line.color.rgb = brand_config['line_color']
            header_line.line.width = Pt(2)
            header_line.shadow.inherit = False
        
        # Add row lines (1px) between months
        row_start = table_top + header_height + dy
        row_spacing = row_height
        
        # Add lines BETWEEN rows (num_months - 1 lines)
        for i in range(num_months - 1):
            line_position = row_start + ((i+1) * row_spacing)
            line = slide.shapes.add_connector(
                1, table_left, self.pixels_to_inches(line_position),
                table_left + table_width, self.pixels_to_inches(line_position)
            )
            line.line.color.rgb = brand_config['line_color']
            line.line.width = Pt(1)
            line.shadow.inherit = False
        
        print(f"  Added {1 if num_months > 0 else 0} header line and {num_months - 1} row lines")
    
    # ========== CHARTS ==========
    
    def add_tactic_chart(self, slide, historical_data, brand_config, brand, tactic, 
                    audience, month_year, strategy=None, market_name="Unknown"):
        """
        Add column + line chart using matplotlib
        
        Args:
            slide: PowerPoint slide object
            historical_data: DataFrame with historical metrics
            brand_config: Brand configuration dictionary
            brand: Brand name (e.g., 'GMC')
            tactic: Tactic name (e.g., 'YouTube')
            audience: Audience type (e.g., 'GEN', 'HIS')
            month_year: Current month/year for filtering
            strategy: Optional strategy for Display tactic splitting
            market_name: Market name for error logging
        """
        if historical_data is None or historical_data.empty:
            print("  [WARN] No historical data for chart")
            return
        
        # Resolve effective tactic (e.g., 'Display' -> 'BT Display') for correct benchmark lookup
        effective_tactic = self.tactic_config._resolve_display_tactic(tactic, strategy)
        
        chart_config = self.tactic_config.get_tactic_chart_config(effective_tactic, strategy)
        if not chart_config:
            print(f"  [WARN] No chart configuration for tactic: {effective_tactic}")
            return
        
        # Filter data to 6-month window
        filtered_data = self._filter_historical_data(historical_data, month_year)
        if filtered_data.empty:
            print(f"  [WARN] No data in 6-month window")
            return
        
        # Create matplotlib chart - passing effective_tactic for benchmark lookup
        chart_image = self._create_matplotlib_chart(filtered_data, brand_config, brand, 
                                                     effective_tactic, audience, chart_config, market_name)
        
        # Add chart image to slide
        self._add_chart_image_to_slide(slide, chart_image)
        
        print(f"  [OK] Added {tactic} chart: {chart_config['title']}")

    def _create_matplotlib_chart(self, filtered_data, brand_config, brand, 
                             tactic, audience, chart_config, market_name="Unknown"):
        """Create a combined bar + line chart using matplotlib"""
        
        # Get data
        from tactic_config import get_metric_column_mapping
        from benchmarks import Benchmarks
        
        column_mapping = get_metric_column_mapping()
        benchmarks = Benchmarks()
        
        # Error collector
        error_collector = ErrorCollector()
        
        # Prepare month labels
        # Use simple space or real newline. User complained about "n2025" which comes from literal \n
        months = [date.strftime('%B\n%Y') for date in filtered_data['parsed_date']]
        
        # Get bar data
        bar_column = column_mapping.get(chart_config['bar_metric'])
        bar_values = []
        for _, row in filtered_data.iterrows():
            val = float(row.get(bar_column, 0)) if pd.notna(row.get(bar_column)) else 0
            bar_values.append(val)
        
        # Get line data (if exists)
        line_values = None
        orig_line_values = None # For labels
        
        if 'line_metric' in chart_config and chart_config['line_metric']:
            line_column = column_mapping.get(chart_config['line_metric'])
            line_values = []
            orig_line_values = []
            
            for i, (_, row) in enumerate(filtered_data.iterrows()):
                val = float(row.get(line_column, 0)) if pd.notna(row.get(line_column)) else 0
                month_str = months[i].replace('\n', ' ')
                
                # Retrieve corresponding bar value for logical checks (e.g. video completions vs impressions)
                # Assuming bar_metric is impressions-related if we are checking rates
                bar_val = bar_values[i]
                
                # --- VALIDATION LOGIC ---
                metric_key_lower = chart_config['line_metric'].lower()
                is_rate = metric_key_lower in ['vcr', 'ctr', 'viewability', 'acr', 'yt_viewability']
                
                plot_val = val
                
                # Check 1: Rate > 100% (1.0)
                if is_rate and val > 1.0:
                    msg = f"{metric_key_lower.upper()} > 100% ({val:.1%})"
                    error_collector.add_error(brand, market_name, tactic, month_str, msg, val)
                    # CLAMP for plotting
                    plot_val = 1.0
                
                # Check 2: Video Completes > Impressions (Logical check)
                # bar_metric usually is 'video_completions' or 'impressions'. 
                # If bar is completions, we can't check against impressions easily unless we fetch impressions column specifically.
                # However, usually Line=VCR, Bar=Video Completions. VCR = Completions/Impressions.
                # If VCR > 100%, it implies Completions > Impressions. So Check 1 covers it.
                
                line_values.append(plot_val)
                orig_line_values.append(val)
        
        # Get benchmark values for each month in the chart
        benchmark_values = []
        benchmark_metric = None
        
        if line_values and 'line_metric' in chart_config:
            line_metric = chart_config['line_metric']
            benchmark_metric = line_metric.upper()
            
            for _, row in filtered_data.iterrows():
                date_val = row.get('parsed_date')
                val = benchmarks.get_benchmark(brand, tactic, audience, benchmark_metric, date=date_val)
                benchmark_values.append(val)
            
            print(f"  [INFO] Found benchmark series for {tactic} - {line_metric}: {benchmark_values}")
        
        # Get safe font to use - returns (family, weight)
        font_family, font_weight = self._get_safe_font(brand_config['primary_font'])
        
        # Get the brand-specific text color
        brand_key = brand.lower() if brand else ''
        if 'cadillac' in brand_key:
            text_color_plt = self._rgb_to_matplotlib(brand_config.get('text_color_dark', RGBColor(255, 255, 255)))
        else:
            # FORCE absolute black for maximum contrast, overriding any brand config grey
            text_color_plt = self._rgb_to_matplotlib(RGBColor(0, 0, 0))
            
        title_font_weight = 'normal'
        # Force normal weight for labels to ensure they are visible on high-res displays
        label_font_weight = 'normal'
        
        # Determine bar metric type for label positioning
        bar_metric = chart_config.get('bar_metric', '')
        line_metric = chart_config.get('line_metric', '')
        
        # Robust case-insensitive check
        line_metric_lower = str(line_metric).lower()
        is_rate_metric = bar_metric in ['vcr', 'ctr', 'viewability', 'acr', 'yt_viewability']
        is_line_rate = line_metric_lower in ['vcr', 'ctr', 'viewability', 'acr', 'yt_viewability']
        
        print(f"DEBUG: Tactic={tactic}, LineMetric={line_metric}, IsLineRate={is_line_rate}")
        
        # Create figure with specific size - increased height for better aesthetics
        fig, ax1 = plt.subplots(figsize=(6.3, 3.42), dpi=150)
        
        # Set background to transparent
        fig.patch.set_alpha(0)
        ax1.patch.set_alpha(0)
        
        # X positions
        x_pos = np.arange(len(months))
        
        # === BAR CHART ===
        # Set zorder for bars (Base layer)
        ax1.set_zorder(10)
        ax1.patch.set_visible(False) 
        
        # Determine bar width and x-axis limits based on number of months
        num_months = len(months)
        if num_months == 1:
            bar_width = 0.35
            ax1.set_xlim(-1, 1)  # Add generous padding to make the single bar look narrow
        elif num_months == 2:
            bar_width = 0.5
            ax1.set_xlim(-0.8, 1.8)
        else:
            bar_width = 0.7
            ax1.set_xlim(-0.5, num_months - 0.5)

        bars = ax1.bar(x_pos, bar_values, 
                    color=self._rgb_to_matplotlib(brand_config['chart_bar_color']),
                    width=bar_width,
                    label=chart_config['bar_label'],
                    zorder=10)
        
        # Set y-axis limits for bars BEFORE adding labels
        bar_y_min, bar_y_max = self._get_y_axis_limits(bar_values, bar_metric, is_rate_metric)
        
        # KEY CHANGE: Align top of bars with 100% rate line if applicable
        # User request: "alinear el top de las columnas con las tasas"
        if is_line_rate and bar_values:
            # Force max bar to touch the top (1.0 on right axis)
            max_bar = max(bar_values)
            if max_bar > 0:
                bar_y_max = max_bar
                print(f"  DEBUG: Aligned Bar Y-Max to {bar_y_max} (100% visual alignment)")
        
        ax1.set_ylim(bar_y_min, bar_y_max)
        
        # Add data labels on bars - BELOW the bars (in negative y-space)
        # "Las impresiones debajo de las barras"
        for bar, value in zip(bars, bar_values):
            height = bar.get_height()
            
            # Place label below the x-axis (negative y)
            y_range = ax1.get_ylim()[1] - ax1.get_ylim()[0]
            y_pos = - (y_range * 0.03)  # Below zero line
            
            # User Request: White background 90% and black font (same as benchmark/line labels)
            label_color = self._rgb_to_matplotlib(RGBColor(0, 0, 0)) 
            
            ax1.text(bar.get_x() + bar.get_width()/2., y_pos,
                    f'{int(value):,}',
                    ha='center', va='top',
                    fontsize=11, # Increased from 9
                    fontfamily=font_family,
                    fontweight='bold', 
                    color=label_color, 
                    zorder=100,
                    bbox=dict(facecolor='white', 
                            edgecolor='none', 
                            alpha=0.9,
                            pad=0.2,
                            boxstyle='round,pad=0.1'))

        # === HIDE LEFT Y-AXIS COMPLETELY ===
        ax1.set_ylabel('')
        ax1.set_yticks([])
        ax1.tick_params(axis='y', which='both', left=False, right=False)

        # === LINE CHART (if exists) ===
        ax2 = None
        if line_values:
            ax2 = ax1.twinx()
            
            # Calculate base y-axis limits
            line_y_min, line_y_max = self._get_y_axis_limits(line_values, line_metric, is_line_rate)

            # CRITICAL FIX: Dynamically adjust y-axis to ALWAYS include benchmarks
            valid_benchmarks = [v for v in benchmark_values if v and v != 'N/A' and isinstance(v, (int, float))]
            if valid_benchmarks:
                max_benchmark = max(valid_benchmarks)
                # Force y_max to be at least 15% above the max benchmark
                benchmark_with_padding = max_benchmark * 1.15
                
                # Check if we need to cap at 100% for rate metrics
                if is_line_rate:
                    capped_padding = min(1.0, benchmark_with_padding)
                    line_y_max = max(line_y_max, capped_padding)
                else:
                    line_y_max = max(line_y_max, benchmark_with_padding)
                
                print(f"  [INFO] Max Benchmark: {max_benchmark:.4f}, Y-max adjusted to: {line_y_max:.4f}")

            # Apply metric-specific caps (changed 'elif' to 'if')
            if line_metric == 'cpcv':
                # Only cap if benchmark doesn't exceed cap
                max_bm = max(valid_benchmarks) if valid_benchmarks else 0
                if not valid_benchmarks or max_bm < 0.10:
                    line_y_max = min(line_y_max, 0.10)

            ax2.set_ylim(line_y_min, line_y_max)
            # Set zorder HIGHER than bars (Line over Bars)
            ax2.set_zorder(15)
            
            # Line WITHOUT markers
            line = ax2.plot(x_pos, line_values,
                    color=self._rgb_to_matplotlib(brand_config['chart_line_color']),
                    linewidth=brand_config.get('chart_line_width', 2.5),
                    label=chart_config['line_label'],
                    clip_on=False, # Allow line to extend beyond axis limits (fixes chopped line at 100%)
                    zorder=15) # Line > Bars
            
            # Add data labels on line points with proper formatting
            for i, value in enumerate(line_values):
                formatted_value = self._format_chart_value(value, line_metric)
                
                # Determine label color - Cadillac uses BLACK for text for better contrast
                if brand == 'Cadillac':
                    label_color = self._rgb_to_matplotlib(RGBColor(0, 0, 0)) # Force Black
                else:
                    label_color = text_color_plt
                
                # Standardizing on centered alignment and specific opacity
                bbox_alpha = 0.9
                # Reduced offset to prevent touching title when values are high
                y_offset_mult = 1.04 

                # User Request: Align continuous line with the numbers
                # By setting va='center' and xytext=(0,0), the label box centers on the line
                va = 'center'
                xytext = (0, 0)
                bbox_alpha = 0.9 # User Request: 90% opacity

                # Use annotate instead of text for precise positioning relative to the point
                # This fixes the alignment issue where the label looked attached to a higher value
                # Use ORIG_LINE_VALUES for the label text so we show the "real" (bad) number if requested
                # But user said "imprimir ese error", arguably we should show 100% on chart? 
                # User: "el límite sea 100%" -> imply visual cap. 
                # User: "imprimir un slide al final ... decir que ... se dieron más video completes"
                # If we show 105% on chart, it looks broken/misaligned with 100% axis. 
                # I will show the CLAMPED value (100%) on the chart label to keep it clean, 
                # and let the error slide tell the full story.
                # formatted_value = self._format_chart_value(orig_line_values[i], line_metric) # Show real
                # formatted_value = self._format_chart_value(orig_line_values[i], line_metric) # Show real
                formatted_value = self._format_chart_value(value, line_metric) # Show clamped
                
                ax2.annotate(formatted_value,
                        xy=(x_pos[i], value), # Use value (clamped) for position
                        xytext=xytext,
                        textcoords='offset points',
                        ha='center', va=va,
                        fontsize=11, 
                        fontfamily=font_family,
                        fontweight='bold', 
                        color=label_color,
                        zorder=100, 
                        bbox=dict(facecolor='white', 
                                edgecolor='none', 
                                alpha=bbox_alpha,
                                pad=0.2,
                                boxstyle='round,pad=0.1'))
            
            # === BENCHMARK LINE (if exists) ===
            if valid_benchmarks:
                benchmark_color = brand_config.get('benchmark_color', brand_config['chart_line_color'])
                benchmark_width = brand_config.get('benchmark_width', 3)
                label_text = f"{benchmark_metric} Benchmark"
                
                # Check if all benchmarks are the same
                if len(set(valid_benchmarks)) == 1:
                    ax2.axhline(y=valid_benchmarks[0], 
                            color=self._rgb_to_matplotlib(benchmark_color),
                            linestyle='--', 
                            linewidth=benchmark_width,
                            label=label_text,
                            zorder=1)
                else:
                    # Draw a stepped line for changing benchmarks
                    # We use 'where=mid' to center the steps on the categories
                    ax2.step(x_pos, benchmark_values,
                            where='mid',
                            color=self._rgb_to_matplotlib(benchmark_color),
                            linestyle='--',
                            linewidth=benchmark_width,
                            label=label_text,
                            zorder=1)
            
            # Configure right y-axis (for line) - NO LABEL
            ax2.set_ylabel('')
            
            # Format y-axis labels based on metric type
            def format_y_axis(x, p):
                return self._format_chart_value(x, line_metric)
            
            ax2.yaxis.set_major_formatter(ticker.FuncFormatter(format_y_axis))
            
            # Use specific locators for rate metrics to ensure clean ticks (e.g. 90%, 95%, 100%)
            if is_line_rate:
                # Per user request: "only 3 indicators, 0%, 50%, 100%"
                # Force strictly these 3 ticks
                ax2.yaxis.set_major_locator(ticker.FixedLocator([0.0, 0.5, 1.0]))   
                # Force axis to 0-1 to ensure alignment
                ax2.set_ylim(0.0, 1.0)
                
                print(f"  DEBUG: Rate ticks set to fixed [0%, 50%, 100%]")
            
            ax2.tick_params(axis='y', labelsize=11, # Increased from 9 
                        labelcolor=text_color_plt,
                        length=0)
            
            # Set y-axis tick label font
            for label in ax2.get_yticklabels():
                label.set_fontfamily(font_family)
                label.set_fontweight(font_weight)
            
            # Style spines for right axis
            ax2.spines['right'].set_visible(False)
            ax2.spines['top'].set_visible(False)
            ax2.spines['left'].set_visible(False)
            ax2.spines['bottom'].set_visible(False)
            
            # Remove grid
            ax2.grid(False)
        
        # === X-AXIS STYLING ===
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(months, 
                            fontsize=12,  # Increased from 10
                            fontfamily=font_family,
                            fontweight=label_font_weight,
                            color=text_color_plt)
        
        # Reduced pad to optimize spacing between impressions and months
        ax1.tick_params(axis='x', which='both', length=0, pad=20)
        
        # === TITLE ===
        ax1.set_title(chart_config['title'],
                    fontsize=15,  # Decrease from 20
                    fontweight='bold', # Used title_font_weight (now 'Bold')
                    fontfamily=font_family,
                    color=text_color_plt,
                    pad=20,  
                    loc='center')
        
        # === REMOVE ALL SPINES ===
        ax1.spines['left'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['top'].set_visible(False)
        ax1.spines['bottom'].set_visible(False)
        
        ax1.grid(False)
        
        # === LEGEND (bottom center) ===
        if line_values and ax2:
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            
            ncol = 3 if valid_benchmarks else 2
            
            legend = ax1.legend(lines1 + lines2, labels1 + labels2,
                    loc='upper center',
                    # Optimized spacing - closer to months
                    bbox_to_anchor=(0.5, -0.30), 
                    ncol=ncol,
                    frameon=False,
                    fontsize=12,  # Increased from 10
                    prop={'family': font_family, 'weight': font_weight})
            
            # Set legend text color
            for text in legend.get_texts():
                text.set_color(text_color_plt)
                text.set_alpha(1.0) # Force full opacity
        else:
            legend = ax1.legend(loc='upper center',
                    # Optimized spacing
                    bbox_to_anchor=(0.5, -0.30),
                    ncol=1,
                    frameon=False,
                    fontsize=12,  # Increased from 10
                    prop={'family': font_family, 'weight': font_weight})
            
            # Set legend text color
            for text in legend.get_texts():
                text.set_color(text_color_plt)
                text.set_alpha(1.0) # Force full opacity
        
        # Adjust layout manually to prevent compression
        # Use subplots_adjust instead of tight_layout for better control
        plt.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.25)
        
        # Save to BytesIO
        img_stream = BytesIO()
        plt.savefig(img_stream, format='png', dpi=150, bbox_inches='tight', 
                    transparent=True)
        plt.close(fig)
        img_stream.seek(0)
        
        return img_stream
    
    def _get_y_axis_limits(self, values, metric, is_rate_metric):
        """
        Calculate appropriate y-axis limits based on data and metric type
        
        Args:
            values: List of data values
            metric: Metric name (e.g., 'vcr', 'cpcv')
            is_rate_metric: Boolean indicating if this is a rate/percentage
        
        Returns:
            tuple: (y_min, y_max)
        """
        if not values or all(v == 0 for v in values):
            return (0, 1)
        
        max_val = max(values)
        min_val = min(values)
        
        if is_rate_metric or metric in ['vcr', 'acr']:
            # For percentage metrics (0-1 range)
            if min_val > 0.9:  # If all values are above 90% (like FEP VCR)
                y_min = 0.85  # Start at 85%
                y_max = 1.0   # End at 100%
            elif min_val > 0.8:  # If all values are above 80%
                y_min = min_val * 0.90  # Start at 90% of minimum
                y_max = min(1.0, max_val * 1.15)  # Headroom
            else:
                y_min = 0
                y_max = min(1.0, max_val * 1.25)  # Restored headroom
        else:
            # For count/cost metrics
            y_min = 0
            y_max = max_val * 1.25  # Restored headroom
        
        return (y_min, y_max)

