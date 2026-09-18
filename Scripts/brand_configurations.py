import os
from pptx.dml.color import RGBColor


class BrandConfigurations:
    """Manages brand-specific configurations for GM brands"""
    
    def __init__(self, base_path=None):
        if base_path is None:
            # Get the parent directory of the Scripts folder
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.base_path = os.path.dirname(current_dir)
        else:
            self.base_path = base_path
        
        # Common asset paths
        self.mrg_logo_path = os.path.join(self.base_path, "Design", "Logos", "MRG long logo.png")
        
        # Brand configurations
        self.brand_configs = self._setup_brand_configs()
    
    def _setup_brand_configs(self):
        """Define brand-specific configurations for all GM brands"""
        return {
            'buick': {
                'name': 'Buick',
                'background_image': os.path.join(self.base_path, "Design", "Background Images", "Buick Intro Background.jpg"),
                'logo_path': os.path.join(self.base_path, "Design", "Logos", "Buick logo_transparent.png"),
                'logo_size': {'width': 335, 'height': 118},
                'logo_position': {'x': 72, 'y': 44},
                'primary_color': RGBColor(254, 80, 0),      # #FE5000 - Orange
                'secondary_color': RGBColor(244, 181, 106), # #F4B56A - Light Orange
                'text_color_dark': RGBColor(51, 51, 51),    # #333333
                'text_color_darker': RGBColor(51, 51, 51),  # #333333
                'gm_confidential_color': RGBColor(51, 51, 51),  # Dark text for GM Confidential
                'background_light': RGBColor(246, 245, 244), # #F6F5F4
                'background_lighter': RGBColor(239, 237, 234), # #EFEDEA
                'primary_font': 'Buick Text Light',
                'accent_font': 'Buick Text Light',
                'line_width': 2,
                'line_color': RGBColor(254, 80, 0),      # #FE5000 - Orange
                'chart_bar_color': RGBColor(244, 181, 106),    # #F4B56A - Light Orange
                'chart_line_color': RGBColor(102, 102, 102),   # #666666 - Dark Grey
                'chart_line_width': 2,
                'benchmark_color': RGBColor(51, 51, 51),  # #333333
                'benchmark_width': 2,
                'metric_box': {
                    'fill_color': RGBColor(239, 237, 234),  # #EFEDEA
                    'has_border': True,
                    'border_color': RGBColor(239, 237, 234),  # #EFEDEA
                    'border_width': 1,  # 1px
                }
            },
            'chevrolet': {
                'name': 'Chevrolet',
                'background_image': os.path.join(self.base_path, "Design", "Background Images", "Chevy Intro Background.jpg"),
                'logo_path': os.path.join(self.base_path, "Design", "Logos", "Chevrolet logo.png"),
                'logo_size': {'width': 329, 'height': 110},
                'logo_position': {'x': 72, 'y': 44},
                'primary_color': RGBColor(0, 119, 217),     # #0077D9 - Blue
                'secondary_color': RGBColor(242, 188, 24),  # #F2BC18 - Gold
                'accent_orange': RGBColor(241, 101, 34),    # #F16522 - Orange
                'accent_red': RGBColor(234, 33, 43),        # #EA212B - Red
                'text_color_dark': RGBColor(57, 56, 57),    # #393839
                'text_color_darker': RGBColor(57, 56, 57),  # #393839
                'gm_confidential_color': RGBColor(57, 56, 57),  # Dark text for GM Confidential
                'background_light': RGBColor(222, 213, 197), # #DED5C5
                'background_lighter': RGBColor(241, 241, 241), # #F1F1F1
                'primary_font': 'Chevy Sans Light',
                'accent_font': 'Chevy Sans Light',
                'line_width': 2,
                'line_color': RGBColor(0, 119, 217),     # #0077D9 - Blue
                'chart_bar_color': RGBColor(0, 119, 217),    # #0077D9 - Blue
                'chart_line_color': RGBColor(57, 56, 57),    # #393839 - Dark Grey
                'chart_line_width': 2,
                'benchmark_color': RGBColor(57, 56, 57),  # #393839
                'benchmark_width': 2,
                'metric_box': {
                    'fill_color': RGBColor(241, 241, 241),  # #F1F1F1
                    'has_border': False,
                    'border_color': None,
                    'border_width': 0,
                    'rounded_corners': False
                },
            },
            'cadillac': {
                'name': 'Cadillac',
                'background_image': os.path.join(self.base_path, "Design", "Background Images", "Cadillac Intro Background.jpg"),
                'logo_path': os.path.join(self.base_path, "Design", "Logos", "Cadillac Logo.png"),
                'logo_size': {'width': 328, 'height': 214},
                'logo_position': {'x': 72, 'y': 0},
                'primary_color': RGBColor(250, 0, 55),      # #FA0037 - Red
                'secondary_color': RGBColor(44, 40, 232),   # #2C28E8 - Blue
                'accent_gold': RGBColor(243, 200, 70),      # #F3C846 - Gold
                'text_color_white': RGBColor(255, 255, 255), # #FFFFFF - White
                'text_color_dark': RGBColor(255, 255, 255), # #FFFFFF - White (changed for Cadillac)
                'text_color_darker': RGBColor(255, 255, 255), # #FFFFFF - White (changed for Cadillac)
                'gm_confidential_color': RGBColor(255, 255, 255), # White text for GM Confidential
                'primary_font': 'Cadillac Gothic Narrow',
                'accent_font': 'Cadillac Gothic Narrow',
                'line_width': 2,
                'line_color': RGBColor(255, 255, 255), # #FFFFFF - White (default)
                'chart_bar_color': RGBColor(255, 255, 255), # #FFFFFF - White (default)
                'chart_line_color': RGBColor(255, 255, 255), # #FFFFFF - White (ALWAYS white)
                'chart_line_width': 3,
                'benchmark_color': RGBColor(255, 255, 255),  # #FFFFFF (ALWAYS white)
                'benchmark_width': 3,
                'metric_box': {
                    'fill_color': RGBColor(85, 85, 85),  # #555555 - Lighter grey for better visibility/opacity
                    'has_border': False,
                    'border_color': None,
                    'border_width': 0,
                    'rounded_corners': False
                },
                # Tactic-specific color overrides
                'tactic_colors': {
                    'FEP': {
                        'line_color': RGBColor(243, 200, 70),      # Gold (for structural lines)
                        'chart_bar_color': RGBColor(243, 200, 70)  # Gold (for chart bars)
                    },
                    'PREROLL': {
                        'line_color': RGBColor(250, 0, 55),        # Red
                        'chart_bar_color': RGBColor(250, 0, 55)
                    },
                    'YOUTUBE': {
                        'line_color': RGBColor(250, 0, 55),        # Red
                        'chart_bar_color': RGBColor(250, 0, 55)
                    },
                    'BT DISPLAY': {
                        'line_color': RGBColor(114, 159, 84),      # Green
                        'chart_bar_color': RGBColor(114, 159, 84)
                    },
                    'RETARGETING DISPLAY': {
                        'line_color': RGBColor(114, 159, 84),      # Green
                        'chart_bar_color': RGBColor(114, 159, 84)
                    },
                    'CONSIDERATION DISPLAY': {
                        'line_color': RGBColor(114, 159, 84),      # Green
                        'chart_bar_color': RGBColor(114, 159, 84)
                    },
                    'META DISPLAY': {
                        'line_color': RGBColor(44, 40, 232),       # Blue
                        'chart_bar_color': RGBColor(44, 40, 232)
                    },
                    'META VIDEO': {
                        'line_color': RGBColor(44, 40, 232),       # Blue
                        'chart_bar_color': RGBColor(44, 40, 232)
                    },
                    'PINTEREST DISPLAY': {
                        'line_color': RGBColor(254, 150, 102),     # Peach/Orange
                        'chart_bar_color': RGBColor(254, 150, 102)
                    },
                    'PINTEREST VIDEO': {
                        'line_color': RGBColor(254, 150, 102),     # Peach/Orange
                        'chart_bar_color': RGBColor(254, 150, 102)
                    },
                    'TIKTOK': {
                        'line_color': RGBColor(254, 150, 102),     # Peach/Orange
                        'chart_bar_color': RGBColor(254, 150, 102)
                    },
                    'SEARCH': {
                        'line_color': RGBColor(166, 105, 153),     # Purple
                        'chart_bar_color': RGBColor(166, 105, 153)
                    },
                    'AUDIO': {
                        'line_color': RGBColor(166, 105, 153),     # Purple
                        'chart_bar_color': RGBColor(166, 105, 153)
                    }
                }
            },
            'gmc': {
                'name': 'GMC',
                'background_image': os.path.join(self.base_path, "Design", "Background Images", "GMC Intro Background.png"),
                'logo_path': os.path.join(self.base_path, "Design", "Logos", "GMC.png"),
                'logo_size': {'width': 262, 'height': 104},
                'logo_position': {'x': 57, 'y': 71},
                'primary_color': RGBColor(170, 0, 0),       # #AA0000 - Red
                'secondary_color': RGBColor(235, 235, 235), # #EBEBEB - Light Gray
                'text_color_dark': RGBColor(0, 0, 0),       # #000000 - Black
                'text_color_darker': RGBColor(0, 0, 0),     # #000000 - Black
                'gm_confidential_color': RGBColor(0, 0, 0), # #000000 - Black for GM Confidential
                'primary_font': 'StratumGMC Light',
                'accent_font': 'StratumGMC Light',
                'line_width': 2,
                'line_color': RGBColor(170, 0, 0),       # #AA0000 - Red
                'chart_bar_color': RGBColor(179, 179, 179),    # #B3B3B3 - Grey
                'chart_line_color': RGBColor(102, 102, 102),   # #666666 - Dark Grey
                'table_header_color': (170, 0, 0),      # Dark red for headers
                'table_row_color_1': (254, 161, 158),     # Light pink for data rows
                'table_row_color_2': (254, 192, 191),     # Lighter pink for data rows
                'chart_line_width': 2,
                'benchmark_color': RGBColor(0, 0, 0),  # #000000
                'benchmark_width': 2,
                'metric_box': {
                    'fill_color': RGBColor(235, 235, 235),  # #EBEBEB
                    'has_border': False,
                    'border_color': None,
                    'border_width': 0,
                    'rounded_corners': False
                }
            }
        }
    
    def get_brand_config(self, brand_name, tactic=None):
        """Get brand configuration, handling various input formats"""
        brand_key = brand_name.lower().strip()
        
        # Handle variations
        if brand_key in ['chevy', 'chevrolet']:
            brand_key = 'chevrolet'
        elif brand_key in ['caddy', 'cad']:
            brand_key = 'cadillac'
        
        if brand_key not in self.brand_configs:
            raise ValueError(f"Unsupported brand: {brand_name}. Supported brands: {list(self.brand_configs.keys())}")
        
        # Get the config and add the brand_name key
        config = self.brand_configs[brand_key].copy()  # Make a copy to avoid modifying original
        config['brand_name'] = brand_key  # Add the brand_name key
        
        # Apply tactic-specific colors for Cadillac if tactic is provided
        if brand_key == 'cadillac' and tactic:
            tactic_key = tactic.upper().strip()
            if 'tactic_colors' in config and tactic_key in config['tactic_colors']:
                # Override the default colors with tactic-specific colors
                tactic_colors = config['tactic_colors'][tactic_key]
                config['line_color'] = tactic_colors.get('line_color', config['line_color'])
                config['chart_bar_color'] = tactic_colors.get('chart_bar_color', config['chart_bar_color'])
                config['chart_line_color'] = tactic_colors.get('chart_line_color', config['chart_line_color'])
                print(f"  Applied {tactic_key} colors: {config['line_color']}")
        
        return config
    
    def get_mrg_logo_path(self):
        """Get MRG logo path"""
        return self.mrg_logo_path