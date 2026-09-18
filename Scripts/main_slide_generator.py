"""
Main Slide Generator - Refactored Modular Version
This orchestrator coordinates all components to generate PowerPoint presentations
from Power BI data. Now uses the refactored modular architecture.
"""
import os
import argparse
import re
import time
from datetime import datetime
import pandas as pd
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import numpy as np

# Import modular components
from powerbi_connector import PowerBIConnector
from brand_configurations import BrandConfigurations  
from data_queries import DataQueries
from measures import calculate_metrics, get_exec_summary_measures
from glossary import add_glossary_to_deck

# Import refactored slide components
from slide_templates_refactored import SlideTemplates
from executive_summary import create_executive_summary_slide
from ytd_charts_refactored import create_ytd_kba_slide, create_ytd_impressions_slide
from error_collector import ErrorCollector
from flatten_pptx import flatten_presentation
import settings

# GM brands list
GM_BRANDS = settings.GM_BRANDS

class SlideGenerationOrchestrator:
    """Main orchestrator that coordinates all modular components"""
    
    def __init__(self, base_path=None, flatten_slides=False):
        """
        Initialize the orchestrator with all necessary components
        
        Args:
            base_path: Base path for assets (optional)
            flatten_slides: Whether to convert slides to static images (optional)
        """
        self.flatten_slides = flatten_slides
        # Set up base path
        if base_path is None:
            # Get the parent directory of the current script (Scripts -> Python Automation)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.base_path = os.path.dirname(current_dir)
        else:
            self.base_path = base_path
        
        # Initialize data source
        self.powerbi = PowerBIConnector(
            workspace_id=settings.POWERBI_WORKSPACE_ID,
            dataset_id=settings.POWERBI_DATASET_ID, 
            client_id=settings.POWERBI_CLIENT_ID
        )
        
        # Initialize configuration and query builders
        self.brand_configs = BrandConfigurations(self.base_path)
        self.data_queries = DataQueries()
        
        # Initialize refactored slide templates (now uses modular architecture internally)
        self.slide_templates = SlideTemplates(self.brand_configs)
        
        # GM brands list
        self.gm_brands = settings.GM_BRANDS
    
    def authenticate(self, silent_only=False):
        """Authenticate with Power BI"""
        return self.powerbi.authenticate(silent_only=silent_only)
    
    def get_available_data(self):
        """Get all available brand/market/date combinations"""
        if not self.authenticate():
            print("Authentication failed")
            return pd.DataFrame()
        
        query = self.data_queries.get_all_combinations_query(self.gm_brands)
        return self.powerbi.execute_dax_query(query)
    
    def generate_single_slide(self, brand, market_name, month_year, slide_type="data", 
                             tactic=None, site=None, audience=None, 
                             output_folder="Generated_Slides", flatten_slides=None):
        """
        Generate a single slide
        """
        if not self.authenticate():
            print("Authentication failed")
            return None
            
        # Create output folder
        os.makedirs(output_folder, exist_ok=True)
        
        # Get data for data slides
        current_metrics = None
        historical_data = None
        
        if slide_type == "data":
            # Get current metrics
            current_query = self.data_queries.get_detailed_metrics_query(
                brand, market_name, month_year, 
                tactic=tactic, site=site, audience=audience
            )
            current_metrics = self.powerbi.execute_dax_query(current_query)
            
            # Get historical data
            historical_query = self.data_queries.get_historical_metrics_query(
                brand, market_name, month_year, months=6, 
                tactic=tactic, site=site, audience=audience
            )
            historical_data = self.powerbi.execute_dax_query(historical_query)
        
        # Format month_year for display
        formatted_month_year = self._format_month_year(month_year)
        
        # Extract zone/LMA type
        zone_lma_type = self._extract_zone_lma_type(current_metrics)
        
        # Create slide using refactored templates
        if slide_type == "title":
            prs, slide = self.slide_templates.create_title_slide(
                brand, market_name, formatted_month_year, zone_lma_type
            )
        else:  # data slide
            # Get audience label
            audience_label = self._extract_audience_label(current_metrics, site, audience)
            
            # Get strategy for Display tactic splitting
            strategy = self._extract_strategy(current_metrics)
            
            prs, slide = self.slide_templates.create_data_slide(
                brand, market_name, formatted_month_year, 
                current_metrics, historical_data,
                tactic=tactic, 
                audience_label=audience_label,
                strategy=strategy,
                zone_lma_type=zone_lma_type
            )
        
        # Save presentation
        filepath = self._save_presentation(
            prs, brand, market_name, month_year, slide_type,
            tactic, site, audience, output_folder,
            flatten_slides=(flatten_slides if flatten_slides is not None else self.flatten_slides)
        )
        
        return {
            'filepath': filepath,
            'brand': brand,
            'market': market_name,
            'month_year': month_year,
            'slide_type': slide_type,
            'tactic': tactic,
            'site': site,
            'audience': audience,
            'has_current_data': current_metrics is not None and not current_metrics.empty,
            'has_historical_data': historical_data is not None and not historical_data.empty
        }
    
    def generate_all_slides_for_market_month(self, brand, market_name, month_year, 
                                    zone_lma_type=None,
                                    region_override=None,
                                    output_folder="Generated_Slides",
                                    summary_only=False,
                                    flatten_slides=None,
                                    client_code=None,
                                    market_code=None,
                                    display_market_name=None,
                                    file_prefix=None,
                                    include_vehicle_slides=True):
        """
        Generate complete deck with all tactic/site/audience combinations
        """
        # Determine whether to flatten
        do_flatten = flatten_slides if flatten_slides is not None else self.flatten_slides
        
        # Use display name if provided, otherwise default to market_name
        market_display_name = display_market_name if display_market_name else market_name
        
        if not self.authenticate():
            print("Authentication failed")
            return None
        
        # Create output folder
        os.makedirs(output_folder, exist_ok=True)
        
        # Initialize Error Collector
        error_collector = ErrorCollector()
        error_collector.clear()
        
        # Get market metadata ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â market_code is passed so the query filters exactly (no ambiguity)
        metadata_query = self.data_queries.get_market_metadata_query(
            brand, market_name, month_year, zone_lma_type, market_code=market_code
        )
        metadata = self.powerbi.execute_dax_query(metadata_query)
        
        exact_brand = brand
        exact_market = market_name
        # Use the market_code passed from UI if available ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â it is the unique identifier.
        # "XXXXX" is only a fallback when no code is known yet.
        if not market_code:
            market_code = "XXXXX"
        region = "Unknown"
        
        if metadata is not None and not metadata.empty:
            brand_col = self._find_column(metadata, "Brand (Reporting)")
            market_col = self._find_column(metadata, "Market Name")
            code_col = self._find_column(metadata, "Market Code")
            region_col = self._find_column(metadata, "Region")
            
            market_code = metadata[code_col].iloc[0] if code_col else market_code
            region = metadata[region_col].iloc[0] if region_col else "Unknown"
            
            # Use EXACT names from PBI for subsequent strict queries
            if brand_col: exact_brand = metadata[brand_col].iloc[0]
            if market_col: exact_market = metadata[market_col].iloc[0]
            
            print(f"Market metadata: Code={market_code}, Region={region}, Type={zone_lma_type}, Exact Brand={exact_brand}, Exact Market={exact_market}")
        else:
            print(f"[WARN] Could not retrieve market metadata for {market_name}")

        # Get all tactic/site/audience combinations
        combinations = self._get_tactic_combinations(
            exact_brand, exact_market, month_year, zone_lma_type, 
            client_code=client_code, market_code=market_code, strict=True
        )
        
        if combinations.empty:
            # Market Code is the minimum unique filter ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â if it returns nothing, there is no
            # recoverable fallback. Do NOT attempt auto-updating the client code, which could
            # silently produce a report with another market's data.
            print(f"  [WARN] No tactic/site combinations found for {brand} - {market_name} ({market_code}) in {month_year}")
            return None
        
        # Warning if very few tactics found
        if len(combinations) < 3:
            print(f"  [!] WARNING: Very few tactics ({len(combinations)}) found. Data for {month_year} might be incomplete.")
        
        # Get zone_lma_type if not provided
        if not zone_lma_type:
            zone_lma_type = self._get_zone_lma_from_combinations(combinations)
        
        # Apply region override when provided
        if region_override:
            print(f"  [INFO] Using region override: {region_override}")
            region = region_override

        # Sort combinations
        combinations = self._sort_combinations(combinations)
        
        # Format dates
        formatted_month_year, year, month, day = self._parse_month_year(month_year)
        
        # Initialize presentation
        prs = None
        slides_created = 0
        
        # SLIDE 1: Title slide
        print("\n=== Generating Title Slide ===")
        prs, slides_created = self._add_title_slide(
            brand, market_display_name, formatted_month_year, zone_lma_type, prs, slides_created
        )
        
        # SLIDE 2: Executive summary
        print("\n=== Generating Executive Summary Slide ===")
        prs, slides_created = self._add_executive_summary_slide(
            exact_brand, exact_market, month_year, formatted_month_year,
            year, month, day, zone_lma_type, prs, slides_created,
            client_code=client_code, display_market_name=market_display_name,
            market_code=market_code, strict=True
        )
        
        if not summary_only:
            # SLIDES 3+: Individual tactic slides
            print("\n=== Generating Tactic Slides ===")
            prs, slides_created = self._add_tactic_slides(
                exact_brand, exact_market, month_year, formatted_month_year,
                zone_lma_type, combinations, prs, slides_created,
                client_code=client_code, display_market_name=market_display_name,
                market_code=market_code, strict=True
            )
            
            # YTD KBA breakdown chart
            print(f"\n=== Generating YTD Chart Slide ===")
            prs, slides_created = self._add_ytd_chart_slides(
                exact_brand, exact_market, month_year, formatted_month_year,
                year, month, day, zone_lma_type, prs, slides_created,
                client_code=client_code, display_market_name=market_display_name,
                market_code=market_code, strict=True
            )

            if include_vehicle_slides:
                # Vehicle pairs are intentionally placed after both YTD slides.
                prs, slides_created = self._add_vehicle_slides(
                    exact_brand, exact_market, month_year, formatted_month_year,
                    zone_lma_type, prs, slides_created,
                    client_code=client_code, display_market_name=market_display_name,
                    market_code=market_code, strict=True
                )
            else:
                print("\n=== Vehicle Section Disabled: Skipping Vehicle Slides ===")
        else:
            print("\n=== Summary Only Mode: Skipping Tactic, YTD, and Vehicle Slides ===")
        
        if prs is None:
            print("No slides were created")
            return None
        
        if not summary_only:
            print("\n=== Generating Glossary Slide ===")
            try:
                # Get brand config
                brand_config = self.brand_configs.get_brand_config(brand)
                
                glossary_slide = add_glossary_to_deck(prs, brand_config, self.slide_templates)
                slides_created += 1
                print("  [OK] Added glossary slide")
            except Exception as e:
                print(f"  [ERROR] Error generating glossary slide: {e}")
                import traceback
                traceback.print_exc()
        
        # === Add Error Summary Slide ===
        # Create collector instance to access singleton errors
        error_collector = ErrorCollector()
        if error_collector.get_errors():
            print(f"\n=== Generating Error Summary Slide ({len(error_collector.get_errors())} anomalies) ===")
            self.slide_templates.create_error_summary_slide(prs, error_collector.get_errors())

        # Save the complete presentation
        filepath = self._save_complete_deck(
            prs, brand, market_name, month_year, zone_lma_type, 
            market_code, region, output_folder, summary_only,
            flatten_slides=do_flatten, client_code=client_code, file_prefix=file_prefix # <--- 2. SE PASA EL PREFIJO A LA FUNCIÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œN FINAL
        )
        
        print(f"\n{'='*60}")
        print(f"[OK] Successfully created {slides_created} slides")
        print(f"[OK] Saved as: {os.path.basename(filepath)}")
        print(f"[OK] Saved to: {os.path.dirname(filepath)}")
        print(f"{'='*60}")
        
        return {
            'filepath': filepath,
            'brand': brand,
            'market': market_name,
            'month_year': month_year,
            'slides_created': slides_created,
            'total_combinations': len(combinations)
        }

    def generate_quarter_rollup_for_market(self, brand, market_name, start_month_year,
                                           end_month_year, zone_lma_type=None,
                                           output_folder="Generated_Slides",
                                           flatten_slides=None, client_code=None,
                                           market_code=None, display_market_name=None,
                                           file_prefix=None):
        """Generate a cover, period Executive Summary, and three-month YTD slides."""
        do_flatten = flatten_slides if flatten_slides is not None else self.flatten_slides
        market_display_name = display_market_name or market_name

        if not self.authenticate():
            print("Authentication failed")
            return None

        os.makedirs(output_folder, exist_ok=True)
        combinations = self._get_tactic_combinations(
            brand, market_name, zone_lma=zone_lma_type,
            client_code=client_code, market_code=market_code, strict=True,
            start_month_year=start_month_year, end_month_year=end_month_year
        )
        if combinations.empty:
            print(f"  [WARN] No tactics found in rollup period for {brand} - {market_name} ({market_code})")
            return None

        if not zone_lma_type:
            zone_lma_type = self._get_zone_lma_from_combinations(combinations)

        start_date = datetime.fromisoformat(start_month_year.split("T")[0])
        end_date = datetime.fromisoformat(end_month_year.split("T")[0])
        period_label = f"{start_date.strftime('%B')}-{end_date.strftime('%B %Y')}"
        end_formatted, year, month, day = self._parse_month_year(end_month_year)

        prs, slides_created = self._add_title_slide(
            brand, market_display_name, period_label, zone_lma_type, None, 0
        )
        prs, slides_created = self._add_executive_summary_slide(
            brand, market_name, end_month_year, period_label, year, month, day,
            zone_lma_type, prs, slides_created, client_code=client_code,
            display_market_name=market_display_name, market_code=market_code,
            strict=True, start_month_year=start_month_year,
            end_month_year=end_month_year
        )
        prs, slides_created = self._add_ytd_chart_slides(
            brand, market_name, end_month_year, period_label, year, month, day,
            zone_lma_type, prs, slides_created, client_code=client_code,
            display_market_name=market_display_name, market_code=market_code,
            strict=True, rolling_months=3
        )

        try:
            brand_config = self.brand_configs.get_brand_config(brand)
            add_glossary_to_deck(prs, brand_config, self.slide_templates)
            slides_created += 1
        except Exception as e:
            print(f"  [ERROR] Error generating glossary slide: {e}")

        filepath = self._save_complete_deck(
            prs, brand, market_name, end_month_year, zone_lma_type,
            market_code, "Unknown", output_folder, True,
            flatten_slides=do_flatten, client_code=client_code,
            file_prefix=file_prefix
        )
        return {
            'filepath': filepath,
            'brand': brand,
            'market': market_name,
            'period': f"{start_month_year}:{end_month_year}",
            'slides_created': slides_created,
            'total_combinations': len(combinations)
        }
    
    # ========== HELPER METHODS ==========
    
    def _find_column(self, df_or_row, name):
        """Robust column finder ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â delegates to shared utils.find_column"""
        from utils import find_column
        return find_column(df_or_row, name)

    def _is_broad_site_match(self, val, target, tactic):
        """Robust site matching handling Social/Meta/Facebook variations"""
        if not val or not target:
            return val == target
            
        v_upper = str(val).upper().strip()
        t_upper = str(target).upper().strip()
        
        if v_upper == t_upper:
            return True
            
        # Meta/Social variations (including Instagram and IG)
        meta_variants = ['META', 'SOCIAL', 'FACEBOOK', 'FB', 'INSTAGRAM', 'IG', 'ADS']
        meta_pattern = '|'.join(re.escape(name) for name in meta_variants)
        has_meta_alias = lambda value: re.search(
            rf'(?<![A-Z0-9])(?:{meta_pattern})(?![A-Z0-9])', value
        ) is not None
        if has_meta_alias(v_upper) and has_meta_alias(t_upper):
            return True
            
        return False
            
    def _is_broad_audience_match(self, val, target):
        """Robust audience matching handling GEN/General/Hispanic/HIS variations"""
        if not val or not target:
            # If target is GEN or General, accept blank as match
            if str(target).upper().strip() in ['GEN', 'GENERAL']:
                return not val or str(val).upper().strip() in ['GEN', 'GENERAL']
            return not val
            
        v_upper = str(val).upper().strip()
        t_upper = str(target).upper().strip()
        
        if v_upper == t_upper:
            return True
            
        # GEN vs General
        if v_upper in ['GEN', 'GENERAL'] and t_upper in ['GEN', 'GENERAL']:
            return True
            
        # HIS vs Hispanic
        if v_upper in ['HIS', 'HISPANIC'] and t_upper in ['HIS', 'HISPANIC']:
            return True
            
        # ASN vs Asian
        if v_upper in ['ASN', 'ASIAN'] and t_upper in ['ASN', 'ASIAN']:
            return True
            
        return False

    def _get_tactic_combinations(self, brand, market_name, month_year=None, zone_lma=None, client_code=None, market_code=None, strict=False, start_month_year=None, end_month_year=None):
        """Get all tactic and site combinations for the report"""
        query = self.data_queries.get_tactic_site_combinations_query(
            brand, market_name, month_year, zone_lma=zone_lma, client_code=client_code,
            market_code=market_code, strict=strict,
            start_month_year=start_month_year, end_month_year=end_month_year
        )
        # Note: Discovery usually stays fuzzy or uses brand/market. 
        # But if market_code is provided, we can use it.
        combinations = self.powerbi.execute_dax_query(query)
        
        if combinations is None:
            print(f"  [ERROR] DAX Query failed for tactic combinations in {month_year}")
            return pd.DataFrame()

        if not combinations.empty:
            print(f"Found {len(combinations)} tactic/site/audience combinations:")
            
            # Find column names once
            tactic_col = self._find_column(combinations, "Tactic (Reporting)")
            site_col = self._find_column(combinations, "Site (Reporting)")
            audience_col = self._find_column(combinations, "Audience")
            zone_lma_col = self._find_column(combinations, "Zone/LMA")
            region_col = self._find_column(combinations, "Region")
            
            for idx, row in combinations.iterrows():
                tactic = row.get(tactic_col, "Unknown")
                site = row.get(site_col, "Unknown")
                audience = row.get(audience_col, "Unknown")
                zone_lma_val = row.get(zone_lma_col, "Unknown")
                region_val = row.get(region_col, "")
                
                print(f"  - Tactic: {tactic.ljust(15)} | Site: {site.ljust(15)} | Audience: {audience} | Type: {zone_lma_val} | Region: {region_val}")
        
        return combinations
    
    def _sort_combinations(self, combinations):
        """Sort combinations by tactic, then audience (GEN before HIS)"""
        tactic_col = self._find_column(combinations, "Tactic (Reporting)")
        audience_col = self._find_column(combinations, "Audience")
        
        if tactic_col and audience_col:
            return combinations.sort_values(
                by=[tactic_col, audience_col],
                ascending=[True, True]
            )
        return combinations
    
    def _parse_month_year(self, month_year):
        """Parse month_year string into components"""
        try:
            date_obj = datetime.fromisoformat(month_year.split("T")[0])
            formatted = date_obj.strftime('%B %Y')
            year = date_obj.year
            month = date_obj.month
            day = date_obj.day
            return formatted, year, month, day
        except:
            return month_year, None, None, None
    
    def _format_month_year(self, month_year):
        """Format month_year for display"""
        try:
            date_obj = datetime.fromisoformat(month_year.split("T")[0])
            return date_obj.strftime('%B %Y')
        except:
            return month_year
    
    def _extract_zone_lma_type(self, data):
        """Extract zone/LMA type from data"""
        col = self._find_column(data, 'Zone/LMA')
        if data is not None and not data.empty and col:
            return data[col].iloc[0]
        return None
    
    def _extract_audience_label(self, data, site, audience):
        """Extract or construct audience label"""
        col = self._find_column(data, 'Site Audience Label')
        if data is not None and not data.empty and col:
            return data[col].iloc[0]
        return f"{site} - {audience}" if site and audience else "Unknown"
    
    def _extract_strategy(self, data):
        """Extract strategy for Display tactic splitting"""
        col = self._find_column(data, 'Strategy (groups)')
        if not col:
            col = self._find_column(data, 'Strategy')
            
        if data is not None and not data.empty and col:
            return data[col].iloc[0]
        return None
    
    def _get_zone_lma_from_combinations(self, combinations):
        """Get zone/LMA type from combinations DataFrame"""
        col = self._find_column(combinations, 'Zone/LMA')
        if len(combinations) > 0 and col:
            return combinations[col].iloc[0]
        return "LMA"  # Default
    
    def _add_title_slide(self, brand, market_name, formatted_month_year, 
                        zone_lma_type, prs, slides_created):
        """Add title slide to presentation"""
        try:
            prs, title_slide = self.slide_templates.create_title_slide(
                brand, market_name, formatted_month_year, zone_lma_type
            )
            slides_created += 1
            print(f"  [OK] Added title slide (Type: {zone_lma_type})")
        except Exception as e:
            print(f"  [ERROR] Error generating title slide: {e}")
        
        return prs, slides_created
    
    def _add_executive_summary_slide(self, brand, market_name, month_year, 
                                    formatted_month_year, year, month, day,
                                    zone_lma_type, prs, slides_created,
                                    client_code=None, display_market_name=None,
                                    market_code=None, strict=False,
                                    start_month_year=None, end_month_year=None):
        """Add executive summary slide to presentation"""
        market_display_name = display_market_name if display_market_name else market_name
        try:
            print(f"  [DEBUG] Exec Summary Date: Y={year}, M={month}, D={day}, Zone/LMA={zone_lma_type}")
            if not year or not month or not day:
                print("  [WARN] Could not parse date for executive summary")
                return prs, slides_created
            
            if not zone_lma_type or pd.isna(zone_lma_type):
                print("  [WARN] Zone/LMA type is None - cannot create executive summary")
                return prs, slides_created
            
            clean_date = month_year.split("T")[0]
            
            exec_query = self.data_queries.get_executive_summary_query(
                brand, market_name, month_year, zone_lma=zone_lma_type, client_code=client_code,
                market_code=market_code, strict=strict,
                start_month_year=start_month_year, end_month_year=end_month_year
            )
            
            df_exec_raw = self.powerbi.execute_dax_query(exec_query)
            
            if df_exec_raw is None or df_exec_raw.empty:
                print(f"  [WARN] No data available for executive summary in {formatted_month_year}")
                if df_exec_raw is None:
                    print("  [DEBUG] execute_dax_query returned None (Query Error?)")
                return prs, slides_created
            
            if df_exec_raw is not None and not df_exec_raw.empty:
                kba_col = self._find_column(df_exec_raw, "Total Conversions") or self._find_column(df_exec_raw, "KBA")
                if kba_col:
                    total_kba = df_exec_raw[kba_col].sum()
                    print(f"\n[VERIFICATION] Executive Summary Total KBA: {total_kba:,.0f}")
                    
                    # AUDIT: Check for unexpected brand/market overlap
                    id_cols = ['Brand (Reporting)', 'Market Name', 'Market Code', 'Client Code']
                    found_ids = [c for c in df_exec_raw.columns if c in id_cols]
                    if found_ids:
                        print("[AUDIT] Unique ID Combos in this query:")
                        print(df_exec_raw[found_ids].drop_duplicates().to_string(index=False))
                        
                    print("[VERIFICATION] Detailed Rows:")
                    detailed_cols = [c for c in df_exec_raw.columns if any(x in c for x in ["Tactic", "Audience", "Strategy", "Client Code", "Advertiser", "Total Conversions", "KBA"])]
                    print(df_exec_raw[detailed_cols].to_string())
                
                from executive_summary import create_executive_summary_slide
                # Robust renaming based on found columns
                targets = {
                    'Brand': ['Brand (Reporting)', 'Brand'],
                    'Market': ['Market Name', 'Market'],
                    '[Tactic (Reporting)]': ['Tactic (Reporting)'],
                    '[Site (Reporting)]': ['Site (Reporting)'],
                    'Audience': ['Audience'],
                    '[Strategy (groups)]': ['Strategy (groups)', 'Strategy'],
                    'Zone/LMA': ['Zone/LMA'],
                    'Month': ['Month Year', 'Month'],
                    '[Impressions]': ['Impressions'],
                    '[Total Cost]': ['Total Cost'],
                    '[Video Completions]': ['Video Completions'],
                    '[Video Plays]': ['Video Plays'],
                    '[Total Conversions]': ['Total Conversions'],
                    '[Clicks]': ['Clicks'],
                    '[Audio Completes]': ['Audio Completes'],
                    '[Audio Starts]': ['Audio Starts']
                }
                
                final_rename_map = {}
                for target, variants in targets.items():
                    # Try the target itself first if it's already there
                    if target in df_exec_raw.columns:
                        continue
                        
                    for variant in variants:
                        col = self._find_column(df_exec_raw, variant)
                        if col:
                            final_rename_map[col] = target
                            break
                
                if final_rename_map:
                    print(f"  [DEBUG] Renaming Exec Summary columns: {final_rename_map}")
                    df_exec_raw = df_exec_raw.rename(columns=final_rename_map)
                
                # Get unique audiences from data (HIS, GEN, ASIAN)
                audience_col = self._find_column(df_exec_raw, 'Audience')
                
                # Default configuration
                audience_groups = {None: df_exec_raw.copy()}
                
                if audience_col:
                    # Clean the audience column: fix NAs and empty strings to 'GEN'
                    df_exec_raw['Audience_Clean'] = df_exec_raw[audience_col].fillna('GEN').astype(str).str.strip().str.upper()
                    df_exec_raw.loc[df_exec_raw['Audience_Clean'] == '', 'Audience_Clean'] = 'GEN'
                    
                    audiences = sorted(df_exec_raw['Audience_Clean'].unique())
                    print(f"  [DEBUG] Found audiences: {audiences}")
                    
                    audience_groups = {}
                    for aud in audiences:
                        df_audience = df_exec_raw[df_exec_raw['Audience_Clean'] == aud].copy()
                        # Use the audience name directly for all groups including GEN
                        display_aud = aud
                        audience_groups[display_aud] = df_audience
                else:
                    print(f"  [DEBUG] No Audience column found, creating single summary")
                
                # Create one summary slide per audience group
                for display_aud, df_audience in audience_groups.items():
                    log_name = display_aud if display_aud else "GEN (Default)"
                    print(f"\n  === Creating Summary Slide for Audience: {log_name} ===")
                    print(f"    Filtered to {len(df_audience)} rows for audience '{log_name}'")
                    
                    # Create the slide for this audience
                    exec_slide = create_executive_summary_slide(
                        prs, brand, market_display_name, formatted_month_year, 
                        df_audience, self.brand_configs, self.slide_templates, 
                        zone_lma_type, audience=display_aud
                    )
                    
                    if exec_slide is not None:
                        slides_created += 1
                        print(f"  [OK] Added summary slide for {log_name}")
                    else:
                        print(f"  [WARN] create_executive_summary_slide returned None for audience {log_name}")
                
        except Exception as e:
            print(f"  [ERROR] Error generating executive summary slide: {e}")
            import traceback
            traceback.print_exc()
        
        return prs, slides_created
    
    def _add_tactic_slides(self, brand, market_name, month_year, formatted_month_year,
                      zone_lma_type, combinations, prs, slides_created,
                      client_code=None, display_market_name=None,
                      market_code=None, strict=False):
        """Add individual tactic slides to presentation"""
        from filters_manager import GeneralFiltersConfig
        market_display_name = display_market_name if display_market_name else market_name
        
        # ========== GROUP DISPLAY TACTICS BY EFFECTIVE TACTIC & SITE GROUPING ==========
        grouped_combinations = {}
        site_grouping_rules = self.slide_templates.tactic_config.rules.get("site_grouping_rules", {})
        
        for idx, row in combinations.iterrows():
            tactic = row.get("PoP Master Table[Tactic (Reporting)]")
            site = row.get("PoP Master Table[Site (Reporting)]")
            audience = row.get("PoP Master Table[Audience]")
            strategy = row.get("PoP Master Table[Strategy (groups)]")
            
            effective_tactic = self.slide_templates.tactic_config._resolve_display_tactic(tactic, strategy)
            
            # Normalize site if grouping rule exists (CASE-INSENSITIVE)
            display_site = site
            s_upper = str(site).upper().strip()
            matched_group = None
            for group_name, site_list in site_grouping_rules.items():
                g_upper = group_name.upper().strip()
                # Check if site is exactly in list OR if group name is a substring
                if s_upper in [s.upper() for s in site_list] or g_upper in s_upper:
                    display_site = group_name
                    matched_group = group_name
                    break
            
            # Special case for MSP grouping if not caught
            if not matched_group and 'MSP' in s_upper:
                if 'AMPERSAND' in s_upper:
                    display_site = "Ampersand"
                else:
                    display_site = f"MSP {site}"
            
            combo_key = (effective_tactic, display_site, audience)
            
            if combo_key not in grouped_combinations:
                grouped_combinations[combo_key] = {
                    'row': row.copy(),
                    'strategies': set(),
                    'original_sites': set(),
                    'original_tactics': set(), # <--- NEW: Track raw tactics
                    'display_site': display_site
                }
                grouped_combinations[combo_key]['row']["PoP Master Table[Site (Reporting)]"] = display_site
            
            if strategy:
                grouped_combinations[combo_key]['strategies'].add(strategy)
            if site:
                grouped_combinations[combo_key]['original_sites'].add(site)
            # Track the original tactic name to include in consolidated query
            if tactic:
                grouped_combinations[combo_key]['original_tactics'].add(tactic)
        
        processed_combinations = []
        for combo_key, data in grouped_combinations.items():
            row = data['row']
            row['strategies_list'] = list(data['strategies'])
            row['original_sites_list'] = list(data['original_sites'])
            row['original_tactics_list'] = list(data['original_tactics']) # <--- NEW
            processed_combinations.append(row)
        
        # ========== CUSTOM SORTING LOGIC ==========
        def get_tactic_rank(row):
            tactic = str(row.get("PoP Master Table[Tactic (Reporting)]", "")).strip()
            strategy = str(row.get("PoP Master Table[Strategy (groups)]", ""))
            audience = str(row.get("PoP Master Table[Audience]", ""))
            site = str(row.get("PoP Master Table[Site (Reporting)]", "")).upper()
            
            eff_tactic = self.slide_templates.tactic_config._resolve_display_tactic(tactic, strategy)
            
            # LOAD FROM JSON (Centralized)
            ranks = self.slide_templates.tactic_config.rules.get("sorting_ranks", {})
            if not ranks:
                # Fallback if JSON empty
                ranks = {'FEP': 10, 'PreRoll': 30, 'YouTube': 40}
            
            rank = ranks.get(eff_tactic, 999)
            
            # Sub-sort for FEP variants
            if eff_tactic == 'FEP':
                if 'EMRGE' in site: rank = 11
                elif 'MSP' in site: rank = 12
                else: rank = 13
            
            aud_rank = 0 if audience == 'GEN' else 1
            return (rank, aud_rank, audience)

        processed_combinations.sort(key=get_tactic_rank)
        
        # Process the grouped and sorted combinations
        for row in processed_combinations:
            tactic = row.get("PoP Master Table[Tactic (Reporting)]")
            site = row.get("PoP Master Table[Site (Reporting)]")
            audience = row.get("PoP Master Table[Audience]")
            row_zone_lma = row.get("PoP Master Table[Zone/LMA]")
            strategy = row.get("PoP Master Table[Strategy (groups)]")
            
            # CRITICAL: Resolve the effective tactic for this slide
            effective_tactic = self.slide_templates.tactic_config._resolve_display_tactic(tactic, strategy)
            
            strategies_list = row.get('strategies_list', [strategy] if strategy else [])
            
            original_tactics = row.get('original_tactics_list', [tactic] if tactic else [])
            original_sites = row.get('original_sites_list', [site] if site else [])
            
            try:
                # ALWAYS use original (raw) tactics and sites for the DAX query.
                # The display/group names (e.g. "AMPERSAND") don't exist in PBI.
                # The original names (e.g. "Ampersand-Spectrum") do.
                query_tactics = original_tactics if original_tactics else [tactic]
                query_sites = original_sites if original_sites else [site]
                query_strategies = strategies_list if strategies_list else ([strategy] if strategy else [])
                
                current_query = self.data_queries.get_detailed_metrics_query(
                    brand, market_name, month_year, 
                    tactic=query_tactics if len(query_tactics) > 1 else query_tactics[0], 
                    site=query_sites if len(query_sites) > 1 else query_sites[0], 
                    audience=audience, 
                    zone_lma=row_zone_lma,
                    strategy=query_strategies if len(query_strategies) > 1 else (query_strategies[0] if query_strategies else strategy),
                    client_code=client_code,
                    market_code=market_code,
                    strict=strict
                )
                current_metrics_raw = self.powerbi.execute_dax_query(current_query)
                
                # ========== AGGREGATE CURRENT-MONTH ROWS FOR THIS SITE ==========
                if current_metrics_raw is not None and not current_metrics_raw.empty:
                    from filters_manager import aggregate_tactic_metric_rows
                    # The query is scoped by Site (Reporting) and audience.
                    # Sum every strategy/campaign row before applying spend.
                    current_metrics = aggregate_tactic_metric_rows(current_metrics_raw)
                else:
                    current_metrics = current_metrics_raw
                
                # ========== CALCULATE DERIVED METRICS FOR CURRENT MONTH ==========
                # This ensures we have CPC, VCR, CPCV, etc. instead of leaving them as 0
                if current_metrics is not None and not current_metrics.empty:
                    current_metrics = calculate_metrics(current_metrics)
                
                # ========== CHECK CURRENT MONTH'S TOTAL COST ==========
                if current_metrics is not None and not current_metrics.empty:
                    total_cost_col = self._find_column(current_metrics, 'Total Cost')
                    if total_cost_col:
                        current_cost = current_metrics[total_cost_col].iloc[0]
                        
                        # Check performance even if cost is zero
                        impressions_col = self._find_column(current_metrics, 'Impressions')
                        kba_col = self._find_column(current_metrics, 'Total Conversions')
                        video_col = self._find_column(current_metrics, 'Video Completions')
                        clicks_col = self._find_column(current_metrics, 'Clicks')
                        
                        impressions = current_metrics[impressions_col].iloc[0] if impressions_col else 0
                        kbas = current_metrics[kba_col].iloc[0] if kba_col else 0
                        video_completions = current_metrics[video_col].iloc[0] if video_col else 0
                        clicks = current_metrics[clicks_col].iloc[0] if clicks_col else 0
                        
                        has_performance = (
                            (not pd.isna(impressions) and impressions > 0) or 
                            (not pd.isna(kbas) and kbas > 0) or
                            (not pd.isna(video_completions) and video_completions > 0) or
                            (not pd.isna(clicks) and clicks > 0)
                        )
                        
                        spend_threshold = max(float(GeneralFiltersConfig.min_tactic_spend), 0)
                        spend_value = 0 if pd.isna(current_cost) else float(current_cost)
                        is_below_spend_threshold = (
                            pd.isna(current_cost) or spend_value < spend_threshold
                        )

                        if is_below_spend_threshold:
                            if has_performance:
                                print(
                                    f"  [ANOMALY] Kept {tactic} slide with performance despite "
                                    f"low spend (${spend_value:,.2f} < ${spend_threshold:,.2f})"
                                )
                                from error_collector import ErrorCollector
                                err_msg = (
                                    f"Tactic generated performance despite aggregated spend "
                                    f"${spend_value:,.2f} below configured minimum "
                                    f"${spend_threshold:,.2f}."
                                )
                                ErrorCollector().add_error(
                                    brand, market_name, tactic,
                                    formatted_month_year, err_msg, spend_value
                                )
                            else:
                                print(
                                    f"  [FILTER] Skipped {tactic} slide due to aggregated spend "
                                    f"below threshold (${spend_value:,.2f} < ${spend_threshold:,.2f}) "
                                    f"and no performance"
                                )
                                continue
                # ========== CHECK VIDEO TACTICS WITH 0 VIDEO COMPLETIONS ==========
                # CRITICAL: Use effective_tactic (normalized) for this check
                # 1. Determine if it's a video tactic (using JSON rules if available)
                video_tactics = self.slide_templates.tactic_config.rules.get("video_tactics", [])
                if not video_tactics:
                    video_tactics = ['FEP', 'YouTube', 'OLV', 'CTV', 'Meta Video', 'Pinterest Video', 'TikTok', 'PreRoll']
                
                if GeneralFiltersConfig.skip_video_tactics_with_zero_completions:
                    if current_metrics is not None and not current_metrics.empty:
                        if effective_tactic in video_tactics:
                            video_completions_col = self._find_column(current_metrics, 'Video Completions')
                            if video_completions_col:
                                video_completions = current_metrics[video_completions_col].iloc[0]
                                if pd.isna(video_completions) or video_completions <= 0:
                                    # ONLY skip if it also has no impressions and no KBAs
                                    if not ((not pd.isna(impressions) and impressions > 0) or (not pd.isna(kbas) and kbas > 0)):
                                        print(f"  [FILTER] Skipped normalized video tactic {effective_tactic} (original: {tactic}) due to 0 completions and no other activity.")
                                        continue
                                else:
                                    print(f"  [INFO] Normalized video tactic {effective_tactic} has 0 completions but has performance. Keeping slide.")
                
                # Get historical data - bound to the selected tier (ZONE or LMA) so that
                # the KBA table on each tactic slide aggregates only the same tier as the
                # Executive Summary, preventing count mismatches between the two views.
                historical_query = self.data_queries.get_historical_metrics_query(
                    brand, market_name, month_year, months=GeneralFiltersConfig.rolling_window_months, 
                    tactic=None, 
                    site=query_sites if len(query_sites) > 1 else query_sites[0], 
                    audience=None, 
                    zone_lma=zone_lma_type, strategy=None, client_code=client_code,
                    market_code=market_code, strict=strict
                )
                historical_data_raw = self.powerbi.execute_dax_query(historical_query)
                
                # ========== AGGREGATE HISTORICAL DATA BY MONTH & RESOLVED TACTIC ==========
                if historical_data_raw is not None and not historical_data_raw.empty:
                    # Resolve current slide target for matching
                    effective_tactic_goal = self.slide_templates.tactic_config._resolve_display_tactic(tactic, strategy)
                    
                    # Identify historical columns
                    strat_col_found = self._find_column(historical_data_raw, 'Strategy (groups)')
                    tactic_col_found = self._find_column(historical_data_raw, 'Tactic (Reporting)')
                    site_col_found = self._find_column(historical_data_raw, 'Site (Reporting)')
                    audience_col_found = self._find_column(historical_data_raw, 'Audience')

                    # AUDIT: Print top raw combos to find missing KBAs
                    if effective_tactic_goal == 'Meta Display':
                         print(f"\n  [AUDIT] Raw Historical Data for {market_name} (Total Rows: {len(historical_data_raw)})")
                         try:
                             audit_df = historical_data_raw.groupby([tactic_col_found, site_col_found]).agg({'Total Conversions': 'sum'}).sort_values('Total Conversions', ascending=False).head(10)
                             print(audit_df)
                         except: pass

                    # ROBUST PYTHON-SIDE MATCHING
                    def is_row_match(r):
                        # 0. Find columns
                        r_tactic = r[tactic_col_found] if tactic_col_found else tactic
                        r_strat = r[strat_col_found] if strat_col_found else None
                        r_site = r[site_col_found] if site_col_found else None
                        r_aud = r[audience_col_found] if audience_col_found else None
                        
                        # Resolve tactic with SITE awareness
                        r_eff_tactic = self.slide_templates.tactic_config._resolve_display_tactic(r_tactic, r_strat, r_site)
                        
                        if r_eff_tactic != effective_tactic_goal:
                            return False
                            
                        # 2. Site matching (handle Meta/Social/Facebook/Instagram)
                        # ALWAYS use raw original sites for matching, never the display group name
                        if query_sites:
                            site_match = any(
                                self._is_broad_site_match(r_site, qs, effective_tactic_goal) 
                                for qs in query_sites
                            )
                        else:
                            site_match = self._is_broad_site_match(r_site, site, effective_tactic_goal)
                        
                        # LENIENCE: for Meta Display, if the row has NO site, we accept it anyway
                        if effective_tactic_goal == 'Meta Display' and not site_match:
                            if not r_site or str(r_site).strip() == '' or str(r_site).upper() in ['NONE', 'NAN']:
                                site_match = True
                            
                        if not site_match:
                            return False
                            
                        # 3. Audience matching (handle GEN/General/HIS/Hispanic)
                        aud_match = self._is_broad_audience_match(r_aud, audience)
                        
                        # LENIENCE: for GEN (General) audience, if the row has NO audience, we accept it
                        if (audience in ['GEN', 'General']) and not aud_match:
                            if not r_aud or str(r_aud).strip() == '' or str(r_aud).upper() in ['NONE', 'NAN']:
                                aud_match = True
                                
                        # 4. Client matching (as extra safety layer)
                        client_col_found = self._find_column(historical_data_raw, 'Client Code')
                        if client_col_found and client_code:
                            r_client = str(r[client_col_found]).strip().upper()
                            # Handle client_code as list or string
                            if isinstance(client_code, list):
                                if r_client not in [str(c).strip().upper() for c in client_code]:
                                    return False
                            else:
                                if r_client != str(client_code).strip().upper():
                                    return False
                                
                        return aud_match and site_match

                    historical_data_raw['Eff_Tactic_Match'] = historical_data_raw.apply(is_row_match, axis=1)
                    
                    # Filter to only rows matching our slide's broadened target
                    historical_data_matched = historical_data_raw[historical_data_raw['Eff_Tactic_Match']].copy()
                    
                    if not historical_data_matched.empty:
                        month_col = 'Master Date Table[Month Year]'
                        if month_col in historical_data_matched.columns:
                            # Re-aggregate numeric columns by month - this sums up all naming variations
                            numeric_cols = historical_data_matched.select_dtypes(include=[np.number]).columns.tolist()
                            agg_dict = {col: 'sum' for col in numeric_cols}
                            agg_dict[month_col] = 'first'
                            historical_data = historical_data_matched.groupby(month_col, as_index=False).agg(agg_dict)
                        else:
                            historical_data = historical_data_matched
                    else:
                        historical_data = pd.DataFrame()
                else:
                    historical_data = historical_data_raw
                
                # ========== CALCULATE HISTORICAL METRICS ==========
                if historical_data is not None and not historical_data.empty:
                    historical_data = calculate_metrics(historical_data)
                
                # ========== PREPARE HISTORICAL DATA (centralized) ==========
                # Parse dates, filter window, filter low spend, sort ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â all in one place
                # so slide_components receives clean, ready-to-render data.
                if historical_data is not None and not historical_data.empty:
                    month_col_hist = 'Master Date Table[Month Year]'
                    if month_col_hist in historical_data.columns:
                        # 1. Parse dates
                        historical_data['parsed_date'] = pd.to_datetime(
                            historical_data[month_col_hist], format='mixed', dayfirst=False
                        )
                        
                        # 2. Filter to configured rolling window
                        try:
                            selected_month = pd.to_datetime(formatted_month_year, format='%B %Y')
                        except Exception:
                            selected_month = historical_data['parsed_date'].max()
                        start_month = selected_month - pd.DateOffset(months=GeneralFiltersConfig.rolling_window_months - 1)
                        historical_data = historical_data[
                            (historical_data['parsed_date'] >= start_month) &
                            (historical_data['parsed_date'] <= selected_month)
                        ].copy()
                        
                        # 3. Filter historical months by the configurable spend threshold.
                        if GeneralFiltersConfig.exclude_zero_cost_months:
                            cost_col = None
                            for c in ['[Total Cost]', 'Total Cost']:
                                if c in historical_data.columns:
                                    cost_col = c
                                    break

                            if cost_col:
                                spend_threshold = max(float(GeneralFiltersConfig.min_tactic_spend), 0)
                                historical_cost = pd.to_numeric(
                                    historical_data[cost_col], errors='coerce'
                                ).fillna(0)
                                # Preserve the original strict cost-only rule, replacing
                                # zero with the configurable threshold. The boundary passes.
                                mask = historical_cost >= spend_threshold
                                historical_data = historical_data[mask].copy()
                            
                        # 4. Sort chronologically
                        historical_data = historical_data.sort_values('parsed_date', ascending=True)
                
                # Extract labels
                audience_label = self._extract_audience_label(current_metrics, site, audience)
                
                # Add slide using refactored templates
                try:
                    print(f"  [PROCESS] Attempting slide: {effective_tactic} | Site: {site} | Aud: {audience}")
                    _, slide = self.slide_templates.create_data_slide(
                        brand, market_display_name, formatted_month_year, 
                        current_metrics, historical_data,
                        tactic=effective_tactic,  # USE RESOLVED TACTIC, not raw
                        audience_label=audience_label,
                        strategy=strategy,
                        zone_lma_type=zone_lma_type,
                        existing_prs=prs
                    )
                    
                    if slide:
                        slides_created += 1
                        print(f"  [SUCCESS] Created slide for {effective_tactic} ({site})")
                    else:
                        print(f"  [FAILED] create_data_slide returned None for {effective_tactic} ({site})")
                except Exception as slide_err:
                    print(f"  [ERROR] Slide creation crash for {effective_tactic}: {str(slide_err)}")
                    import traceback
                    traceback.print_exc()
                
            except Exception as e:
                print(f"  [ERROR] Loop error generating metrics for {tactic}/{site}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return prs, slides_created
    
    def _add_ytd_chart_slides(self, brand, market_name, month_year, formatted_month_year,
                             year, month, day, zone_lma_type, prs, slides_created,
                             client_code=None, display_market_name=None,
                             market_code=None, strict=False, rolling_months=None):
        """Add YTD chart slides (KBA and Impressions)"""
        market_display_name = display_market_name if display_market_name else market_name
        
        # 1. YTD KBA Slide
        try:
            kba_query = self.data_queries.get_ytd_kba_by_tactic_query(
                brand, market_name, month_year, zone_lma=zone_lma_type, client_code=client_code,
                market_code=market_code, strict=False, months=rolling_months
            )
            df_kba_raw = self.powerbi.execute_dax_query(kba_query)
            
            if df_kba_raw is not None and not df_kba_raw.empty:
                ytd_kba_pivot = self._process_ytd_data(
                    df_kba_raw, 
                    date_col='Master Date Table[Month Year]',
                    category_col='PoP Master Table[Tactic (Reporting)]',
                    value_col='[KBA]',
                    category_rename='Tactic',
                    limit_year=year,
                    limit_month=month,
                    error_context={
                        'brand': brand,
                        'market': market_name,
                        'report': 'YTD Spend',
                    }
                )
                
                from ytd_charts_refactored import create_ytd_kba_slide
                prs, kba_slide = create_ytd_kba_slide(
                    prs, brand, market_display_name, formatted_month_year, 
                    ytd_kba_pivot, self.brand_configs, self.slide_templates, 
                    zone_lma_type
                )
                if kba_slide:
                    slides_created += 1
                    
        except Exception as e:
            print(f"  [ERROR] Error generating YTD KBA slide: {e}")
            
        # 2. YTD Impressions Slide
        try:
            impressions_query = self.data_queries.get_ytd_impressions_by_vehicle_query(
                brand, market_name, month_year, zone_lma=zone_lma_type, client_code=client_code,
                market_code=market_code, strict=False, months=rolling_months
            )
            df_impressions_raw = self.powerbi.execute_dax_query(impressions_query)
            
            if df_impressions_raw is not None and not df_impressions_raw.empty:
                ytd_impressions_pivot = self._process_ytd_data(
                    df_impressions_raw,
                    date_col='Master Date Table[Month Year]',
                    category_col='PoP Master Table[Vehicle]',
                    value_col='[Impressions]',
                    category_rename='Vehicle',
                    limit_year=year,
                    limit_month=month,
                    error_context={
                        'brand': brand,
                        'market': market_name,
                        'report': 'YTD Spend',
                    }
                )
                
                # Filter vehicles by brand colors
                vehicle_colors = settings.get_vehicle_colors(brand)
                if vehicle_colors:
                    valid_vehicles = set(vehicle_colors.keys())
                    columns_to_drop = []
                    vehicle_cols = [c for c in ytd_impressions_pivot.columns if c != 'Month']
                    error_collector = ErrorCollector()
                    
                    for vehicle in vehicle_cols:
                        if vehicle not in valid_vehicles:
                            other_brand = settings.get_brand_for_vehicle(vehicle)
                            if other_brand and other_brand.lower() != brand.lower():
                                error_collector.add_error(
                                    market=market_name, brand=brand, tactic="YTD Vehicle",
                                    month=formatted_month_year,
                                    message=f"Vehicle '{vehicle}' belongs to {other_brand}, not {brand}."
                                )
                                columns_to_drop.append(vehicle)
                    
                    if columns_to_drop:
                        ytd_impressions_pivot = ytd_impressions_pivot.drop(columns=columns_to_drop)

                from ytd_charts_refactored import create_ytd_impressions_slide
                prs, imp_slide = create_ytd_impressions_slide(
                    prs, brand, market_display_name, formatted_month_year,
                    ytd_impressions_pivot, self.brand_configs, self.slide_templates,
                    zone_lma_type
                )
                if imp_slide:
                    slides_created += 1
                    
        except Exception as e:
            print(f"  [ERROR] Error generating YTD Impressions slide: {e}")
            
        return prs, slides_created

    def _add_ytd_slide_title(self, slide, market_name, title_text, subtitle_text, brand_config):
        """Add YTD slide title with optional subtitle"""
        pixels_to_inches = self.slide_templates.pixels_to_inches
        
        market_box = slide.shapes.add_textbox(
            pixels_to_inches(0),
            pixels_to_inches(32),
            pixels_to_inches(1280),
            pixels_to_inches(50)
        )
        market_frame = market_box.text_frame
        market_frame.text = market_name
        
        market_para = market_frame.paragraphs[0]
        market_para.alignment = PP_ALIGN.CENTER
        market_para.font.size = Pt(32)
        market_para.font.bold = True
        market_para.font.name = brand_config.get('primary_font', 'Segoe UI')
        market_para.font.color.rgb = brand_config.get('text_color_dark', RGBColor(0, 0, 0))
        
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
        title_para.font.size = Pt(32)
        title_para.font.bold = True
        title_para.font.name = brand_config.get('primary_font', 'Segoe UI')
        title_para.font.color.rgb = brand_config.get('text_color_dark', RGBColor(0, 0, 0))
        
        if subtitle_text:
            subtitle_box = slide.shapes.add_textbox(
                pixels_to_inches(0),
                pixels_to_inches(145),
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

    def _add_vehicle_slides(self, brand, market_name, month_year,
                            formatted_month_year, zone_lma_type, prs,
                            slides_created, client_code=None,
                            display_market_name=None, market_code=None,
                            strict=False):
        """Add Insights/Summary pairs for qualifying current-month vehicles."""
        supported_brands = {"buick", "gmc", "cadillac"}
        if str(brand).lower().strip() not in supported_brands:
            return prs, slides_created

        from filters_manager import GeneralFiltersConfig
        from vehicle_insights_summary import (
            create_vehicle_insights_slide,
            create_vehicle_summary_slide,
            prepare_vehicle_current_data,
            prepare_vehicle_historical_data,
        )
        from vehicle_catalog import get_vehicle_catalog

        market_display_name = display_market_name if display_market_name else market_name
        spend_threshold = max(float(GeneralFiltersConfig.min_tactic_spend), 0)

        try:
            print("\n=== Generating Vehicle Insights and Summary Slides ===")
            vehicle_catalog = get_vehicle_catalog(self.base_path)
            current_query = self.data_queries.get_vehicle_current_metrics_query(
                brand, market_name, month_year,
                zone_lma=zone_lma_type,
                client_code=client_code,
                market_code=market_code,
                strict=strict,
            )
            current_raw = self.powerbi.execute_dax_query(current_query)
            active_models, excluded_models = prepare_vehicle_current_data(
                current_raw,
                self.slide_templates.tactic_config,
                vehicle_catalog,
                brand,
                spend_threshold,
            )

            for excluded in excluded_models:
                vehicle_name = excluded["vehicle"]
                if excluded.get("exclusion_type") == "taxonomy":
                    message = (
                        "Vehicle slides not generated by JSON taxonomy: "
                        f"classification={excluded['classification']}; "
                        f"status={excluded['status']}; source value(s)="
                        f"{excluded['source_values']}. {excluded['reason']} "
                        f"Total vehicle spend was ${excluded['total_spend']:,.2f}."
                    )
                else:
                    message = (
                        f"Vehicle slides not generated: none of its "
                        f"{excluded['combination_count']} aggregated Tactic + Site + "
                        f"Audience combinations met the configured minimum spend "
                        f"of ${spend_threshold:,.2f}. Total vehicle spend was "
                        f"${excluded['total_spend']:,.2f}; highest combination was "
                        f"${excluded['max_combination_spend']:,.2f}."
                    )
                ErrorCollector().add_error(
                    brand=brand,
                    market=market_name,
                    tactic=f"Vehicle: {vehicle_name}",
                    month=formatted_month_year,
                    message=message,
                    value=excluded["total_spend"],
                )

            if not active_models:
                print(
                    "  [VEHICLE FILTER] No taxonomy-approved vehicles met the "
                    f"${spend_threshold:,.2f} minimum; no vehicle slides were added."
                )
                return prs, slides_created

            historical_query = self.data_queries.get_vehicle_historical_metrics_query(
                brand, market_name, month_year, months=3,
                zone_lma=zone_lma_type,
                client_code=client_code,
                market_code=market_code,
                strict=strict,
            )
            historical_raw = self.powerbi.execute_dax_query(historical_query)
            historical_by_model = prepare_vehicle_historical_data(
                historical_raw,
                self.slide_templates.tactic_config,
                vehicle_catalog,
                brand,
                active_models.keys(),
                spend_threshold,
                apply_spend_filter=GeneralFiltersConfig.exclude_zero_cost_months,
            )

            for vehicle_name, current_data in active_models.items():
                try:
                    historical_data = historical_by_model.get(
                        vehicle_name, pd.DataFrame()
                    )
                    create_vehicle_insights_slide(
                        prs, brand, market_display_name, formatted_month_year,
                        vehicle_name, current_data, historical_data,
                        self.brand_configs, self.slide_templates, zone_lma_type,
                        vehicle_catalog=vehicle_catalog,
                    )
                    slides_created += 1
                    create_vehicle_summary_slide(
                        prs, brand, market_display_name, formatted_month_year,
                        vehicle_name, current_data, self.brand_configs,
                        self.slide_templates, zone_lma_type,
                        vehicle_catalog=vehicle_catalog,
                    )
                    slides_created += 1
                    print(f"  [OK] Added vehicle slide pair for {vehicle_name}")
                except Exception as vehicle_error:
                    print(
                        f"  [ERROR] Failed vehicle slide pair for {vehicle_name}: "
                        f"{vehicle_error}"
                    )
                    import traceback
                    traceback.print_exc()

        except Exception as error:
            print(f"  [ERROR] Error generating vehicle slides: {error}")
            import traceback
            traceback.print_exc()

        return prs, slides_created

    def _process_ytd_data(self, ytd_data_raw, date_col, category_col, value_col,
                          category_rename, limit_year=None, limit_month=None,
                          error_context=None):
        """Generic method to process raw YTD data into pivot table format"""
        # Find column names flexibly (handle both 'Name' and 'Table[Name]')
        real_date_col = self._find_column(ytd_data_raw, date_col)
        real_cat_col = self._find_column(ytd_data_raw, category_col)
        real_val_col = self._find_column(ytd_data_raw, value_col)
        real_cost_col = self._find_column(ytd_data_raw, 'Total Cost')
        
        if not real_date_col or not real_cat_col or not real_val_col:
            print(f"  [ERROR] YTD Column mismatch: Date({real_date_col}), Cat({real_cat_col}), Val({real_val_col})")
            print(f"  Available: {list(ytd_data_raw.columns)}")
            return pd.DataFrame()

        ytd_data_raw = ytd_data_raw.rename(columns={
            real_date_col: 'RawDate',
            real_cat_col: category_rename,
            real_val_col: 'Value'
        })
        
        ytd_data_raw['RawDate'] = pd.to_datetime(ytd_data_raw['RawDate'])
        
        if limit_year is not None and limit_month is not None:
            ytd_data_raw = ytd_data_raw[
                (ytd_data_raw['RawDate'].dt.year == limit_year) &
                (ytd_data_raw['RawDate'].dt.month >= 1) & # From January
                (ytd_data_raw['RawDate'].dt.month <= limit_month)
            ].copy()

        # The configured spend threshold replaces the former YTD zero-cost
        # rule. Sum cost across all categories in each month, then remove the
        # entire month when its total is below the inclusive threshold.
        from filters_manager import GeneralFiltersConfig
        spend_threshold = max(float(GeneralFiltersConfig.min_tactic_spend), 0)
        if real_cost_col:
            ytd_data_raw['_YTD_Cost'] = pd.to_numeric(
                ytd_data_raw[real_cost_col], errors='coerce'
            ).fillna(0)
            monthly_costs = ytd_data_raw.groupby('RawDate')['_YTD_Cost'].sum()
            excluded_months = monthly_costs[monthly_costs < spend_threshold]
            if not excluded_months.empty:
                ytd_data_raw = ytd_data_raw[
                    ~ytd_data_raw['RawDate'].isin(excluded_months.index)
                ].copy()
                print(
                    f"  [YTD SPEND FILTER] Removed {len(excluded_months)} months "
                    f"below configured spend threshold (${spend_threshold:,.2f})"
                )
                if error_context:
                    collector = ErrorCollector()
                    existing = {
                        (error.get('brand'), error.get('market'),
                         error.get('tactic'), error.get('month'))
                        for error in collector.get_errors()
                    }
                    for excluded_date, excluded_cost in excluded_months.items():
                        month_label = pd.Timestamp(excluded_date).strftime('%B %Y')
                        error_key = (
                            error_context['brand'], error_context['market'],
                            error_context.get('report', 'YTD Spend'), month_label
                        )
                        if error_key not in existing:
                            collector.add_error(
                                brand=error_context['brand'],
                                market=error_context['market'],
                                tactic=error_context.get('report', 'YTD Spend'),
                                month=month_label,
                                message=(
                                    f"YTD month excluded because aggregated spend "
                                    f"${excluded_cost:,.2f} was below the configured "
                                    f"minimum ${spend_threshold:,.2f}."
                                ),
                                value=float(excluded_cost),
                            )
                            existing.add(error_key)
            ytd_data_raw = ytd_data_raw.drop(columns=['_YTD_Cost'])
        else:
            print(
                "  [WARN] YTD Total Cost column not found; configurable spend "
                "threshold was not applied"
            )

        ytd_data_raw['Month'] = ytd_data_raw['RawDate'].dt.strftime('%B')
        
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                    'July', 'August', 'September', 'October', 'November', 'December']
        ytd_data_raw['Month'] = pd.Categorical(
            ytd_data_raw['Month'], categories=month_order, ordered=True
        )
        
        ytd_pivot = ytd_data_raw.pivot_table(
            index='Month',
            columns=category_rename,
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Ensure Month is back as a column and not index (already done by reset_index)
        
        category_columns = [col for col in ytd_pivot.columns if col != 'Month']
        
        ytd_pivot['Total'] = ytd_pivot[category_columns].sum(axis=1)
        ytd_pivot = ytd_pivot[ytd_pivot['Total'] > 0].drop(columns=['Total'])
        
        # ===== APPLY YTD FILTER TO MONTHLY ROWS =====
        # Filter out months with totals below minimum thresholds
        if GeneralFiltersConfig.ytd_filter_enabled:
            # Recalculate total for filtering
            ytd_pivot['_temp_total'] = ytd_pivot[category_columns].sum(axis=1)
            # FIXED CASE-SENSITIVE BUG: check 'impressions' in lowercase
            threshold = GeneralFiltersConfig.ytd_min_impressions if 'impressions' in value_col.lower() else GeneralFiltersConfig.ytd_min_outcomes
            initial_months = len(ytd_pivot)
            ytd_pivot = ytd_pivot[ytd_pivot['_temp_total'] >= threshold]
            dropped_months = initial_months - len(ytd_pivot)
            if dropped_months > 0:
                print(f"  [YTD FILTER] Removed {dropped_months} months below threshold ({threshold:,})")
            ytd_pivot = ytd_pivot.drop(columns=['_temp_total'])
            
        return ytd_pivot
    
    def _save_presentation(self, prs, brand, market_name, month_year, slide_type,
                          tactic, site, audience, output_folder, flatten_slides=False):
        """Save single slide presentation and return filepath"""
        safe_market_name = str(market_name).replace("/", "-").replace(" ", "_").replace(":", "-")
        
        try:
            date_obj = datetime.fromisoformat(month_year.split("T")[0])
            safe_month_year = date_obj.strftime('%Y-%m-%d')
        except:
            safe_month_year = str(month_year).replace(":", "-").replace(" ", "_").replace("/", "-")
        
        tactic_part = f"_{tactic.replace(' ', '_')}" if tactic else ""
        site_part = f"_{site.replace(' ', '_')}" if site else ""
        audience_part = f"_{audience}" if audience else ""
        
        filename = f"{brand}_{safe_market_name}_{safe_month_year}{tactic_part}{site_part}{audience_part}_{slide_type}.pptx"
        filepath = os.path.join(output_folder, filename)
        
        try:
            prs.save(filepath)
        except PermissionError:
            print(f"\n[CRITICAL ERROR] Could not save to: {filename}")
            import sys
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] Unexpected error saving presentation: {e}")
            raise
        
        if flatten_slides:
            try:
                flatten_presentation(filepath)
            except RuntimeError as e:
                print(f"\n[WARNING] Flatten failed ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â file saved as EDITABLE: {e}")
            
        return filepath
        
    def _build_folder_path(self, brand, zone_lma_type, month_year, region, base_folder="Generated_Slides"):
        """Build the appropriate folder path"""
        try:
            date_obj = datetime.fromisoformat(month_year.split("T")[0])
            month_num = date_obj.strftime('%m')
            month_name = date_obj.strftime('%B')
            month_folder = f"{month_num} - {month_name}"
        except:
            month_folder = "Unknown_Month"
        
        if zone_lma_type == "ZONE":
            if brand in ["Buick", "GMC", "Chevrolet"]:
                folder_path = os.path.join(base_folder, "Zone", brand, month_folder, region)
            else:
                folder_path = os.path.join(base_folder, "Zone", brand, month_folder, region)
        elif zone_lma_type == "LMA":
            folder_path = os.path.join(base_folder, "LMA", brand, month_folder, region)
        else:
            folder_path = os.path.join(base_folder, zone_lma_type, brand, month_folder, region)
        
        return folder_path

    def _save_complete_deck(self, prs, brand, market_name, month_year, zone_lma_type, 
                           market_code, region, output_folder, summary_only=False,
                           flatten_slides=False, client_code=None, file_prefix=None): # <--- 3. SE ANADE FILE_PREFIX
        """Save complete deck and return filepath"""
        folder_path = self._build_folder_path(brand, zone_lma_type, month_year, region, output_folder)
        os.makedirs(folder_path, exist_ok=True)
        
        try:
            date_obj = datetime.fromisoformat(month_year.split("T")[0])
            full_month_year = date_obj.strftime('%B %Y')  # Ej: January 2025
        except:
            full_month_year = str(month_year)[:7]
        
        suffix = " Summary" if summary_only else ""
        filename_market_code = (
            market_code[0] if isinstance(market_code, (list, tuple, set)) and market_code
            else market_code
        )
        
        # --- LOGICA DE MARCACION CON PREFIJO INTELIGENTE DE LA UI ---
        if zone_lma_type == "LMA":
            # Si la UI nos mando un prefijo calculado (KAUG o KAUG-AUGGA), lo usamos. 
            # Si no, usamos el Client Code directo.
            final_prefix = file_prefix if file_prefix else (client_code if client_code else market_code)
            filename = f"{final_prefix} {brand} {full_month_year} Digital Metrics{suffix}.pptx"
            
        else:
            # Regla ZONE: Usa el market_code y un orden diferente
            filename = f"{filename_market_code}-{full_month_year} {brand} Zone Reporting{suffix}.pptx"
        # ------------------------------------------------------------
        
        filepath = os.path.join(folder_path, filename)
        
        # Safety net: prevent silent overwrite if collision wasn't caught upstream
        if os.path.exists(filepath):
            base, ext = os.path.splitext(filename)
            filename = f"{base} ({market_code}){ext}"
            filepath = os.path.join(folder_path, filename)
            print(f"  [WARN] Filename collision detected - saving as: {filename}")
        
        try:
            prs.save(filepath)
        except PermissionError:
            print(f"\n[CRITICAL ERROR] Could not save to: {filename}")
            import sys
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] Unexpected error saving presentation: {e}")
            raise
        
        if flatten_slides:
            print(f"\n[INFO] Flattening presentation to images...")
            try:
                flatten_presentation(filepath)
            except RuntimeError as e:
                print(f"\n[WARNING] Flatten failed - file saved as EDITABLE: {e}")
        
        return filepath
        
    def generate_multiple_slides(self, limit=None, brands=None, slide_type="data", 
                                output_folder="Generated_Slides", flatten_slides=None):
        """Generate multiple individual slides from available data"""
        combinations_df = self.get_available_data()
        
        if combinations_df.empty:
            print("No data found")
            return []
        
        if brands:
            combinations_df = combinations_df[
                combinations_df['PoP Master Table[Brand (Reporting)]'].isin(brands)
            ]
        
        if limit:
            combinations_df = combinations_df.head(limit)
        
        results = []
        for index, row in combinations_df.iterrows():
            try:
                brand = row['PoP Master Table[Brand (Reporting)]']
                market_name = row['PoP Master Table[Market Name]']
                month_year = row['Master Date Table[Month Year]']
                
                result = self.generate_single_slide(
                    brand, market_name, month_year, slide_type, 
                    output_folder=output_folder, flatten_slides=flatten_slides
                )
                
                if result:
                    results.append(result)
                    
            except Exception as e:
                print(f"Error processing {index + 1}: {e}")
                continue
        
        return results

# ========== CONVENIENCE FUNCTIONS ==========
def generate_test_slides():
    """Generate a few test slides to verify everything works"""
    generator = SlideGenerationOrchestrator()
    results = generator.generate_multiple_slides(limit=3, slide_type="title", output_folder="Test_Slides")
    results += generator.generate_multiple_slides(limit=3, slide_type="data", output_folder="Test_Slides")
    return results

def generate_brand_slides(brand_name, limit=5):
    """Generate slides for a specific brand"""
    generator = SlideGenerationOrchestrator()
    title_results = generator.generate_multiple_slides(limit=limit, brands=[brand_name], slide_type="title", output_folder=f"{brand_name}_Slides")
    data_results = generator.generate_multiple_slides(limit=limit, brands=[brand_name], slide_type="data", output_folder=f"{brand_name}_Slides")
    return title_results + data_results

def generate_specific_slide(brand, market, month_year, slide_type="data"):
    """Generate a specific slide for debugging"""
    generator = SlideGenerationOrchestrator()
    result = generator.generate_single_slide(brand, market, month_year, slide_type, output_folder="Generated_Slides")
    return result

def show_available_data():
    """Display available data for slide generation"""
    generator = SlideGenerationOrchestrator()
    combinations_df = generator.get_available_data()
    if combinations_df.empty: return
    print(f"Total combinations available: {len(combinations_df)}")

# ========== FUNCIONES INTEGRADAS PARA STREAMLIT ==========

BUICK_GMC_ROLLUP_MARKET_CODES = [
    "XALY", "XATL", "XAUG", "XBIR", "XCHN", "XCLM",
    "XHUN", "XMAC", "XMON", "XMOB", "XTPC"
]


def resolve_rollup_market_rows(catalog, brand_col, code_col):
    """Return catalog rows grouped by the requested Buick/GMC market codes."""
    matches = []
    for brand in ("Buick", "GMC"):
        brand_rows = catalog[
            catalog[brand_col].astype(str).str.strip().str.lower() == brand.lower()
        ].copy()
        brand_rows["_MarketCodeClean"] = brand_rows[code_col].map(
            lambda value: str(value).strip().upper()
        )

        for requested_code in BUICK_GMC_ROLLUP_MARKET_CODES:
            market_rows = brand_rows[
                (brand_rows["_MarketCodeClean"] == requested_code) |
                brand_rows["_MarketCodeClean"].str.startswith(f"{requested_code}-")
            ]
            if not market_rows.empty:
                matches.append((brand, requested_code, market_rows.drop(columns=["_MarketCodeClean"])))
    return matches


def process_buick_gmc_quarter_rollup(start_month_year="2026-06-01",
                                     end_month_year="2026-08-01",
                                     output_folder="Generated_Slides",
                                     flatten_slides=False):
    """Generate the 22 Buick/GMC June-August rollup decks."""
    generator = SlideGenerationOrchestrator(flatten_slides=flatten_slides)
    if not generator.authenticate():
        return {"errors": 1, "details": [{"Status": "Failed", "Error": "Authentication failed"}]}

    timestamp_str = datetime.now().strftime("%b-%d_%H-%M")
    batch_output_dir = os.path.join(output_folder, f"Buick_GMC_Rollup_{timestamp_str}")
    os.makedirs(batch_output_dir, exist_ok=True)

    catalog_query = """
    EVALUATE
    SELECTCOLUMNS(
        SUMMARIZECOLUMNS(
            'PoP Master Table'[Brand (Reporting)],
            'PoP Master Table'[Zone/LMA],
            'PoP Master Table'[Market Name],
            'PoP Master Table'[Market Code],
            'PoP Master Table'[Client Code]
        ),
        "Brand", 'PoP Master Table'[Brand (Reporting)],
        "ZoneLMA", 'PoP Master Table'[Zone/LMA],
        "MarketName", 'PoP Master Table'[Market Name],
        "MarketCode", 'PoP Master Table'[Market Code],
        "ClientCode", 'PoP Master Table'[Client Code]
    )
    """
    catalog = generator.powerbi.execute_dax_query(catalog_query)
    if catalog is None or catalog.empty:
        return {"errors": 1, "details": [{"Status": "Failed", "Error": "Market catalog is empty"}]}

    column_aliases = {
        "Brand": generator._find_column(catalog, "Brand"),
        "Type": generator._find_column(catalog, "ZoneLMA"),
        "Market": generator._find_column(catalog, "MarketName"),
        "Code": generator._find_column(catalog, "MarketCode"),
        "Client": generator._find_column(catalog, "ClientCode"),
    }
    missing_columns = [key for key, value in column_aliases.items() if value is None]
    if missing_columns:
        return {
            "errors": 1,
            "expected_decks": len(BUICK_GMC_ROLLUP_MARKET_CODES) * 2,
            "successful_decks": 0,
            "details": [{
                "Status": "Failed",
                "Error": (
                    f"Catalog columns missing: {missing_columns}. "
                    f"Returned columns: {list(catalog.columns)}"
                ),
            }],
            "output_folder": batch_output_dir,
        }

    brand_col = column_aliases["Brand"]
    type_col = column_aliases["Type"]
    market_col = column_aliases["Market"]
    code_col = column_aliases["Code"]
    client_col = column_aliases["Client"]
    details = []

    for brand, requested_code, market_rows in resolve_rollup_market_rows(
        catalog, brand_col, code_col
    ):
            row = market_rows.iloc[0]
            market_codes = [
                str(value).strip() for value in market_rows[code_col].dropna().unique()
                if str(value).strip() and str(value).strip().lower() != "nan"
            ]
            market_code = market_codes[0] if len(market_codes) == 1 else market_codes
            client_codes = []
            if client_col:
                client_codes = [
                    str(value).strip() for value in market_rows[client_col].dropna().unique()
                    if str(value).strip().lower() != "nan" and str(value).strip()
                ]
            client_code = client_codes if len(client_codes) > 1 else (client_codes[0] if client_codes else None)
            result = generator.generate_quarter_rollup_for_market(
                brand=brand,
                market_name=str(row[market_col]).strip(),
                start_month_year=start_month_year,
                end_month_year=end_month_year,
                zone_lma_type=str(row[type_col]).strip(),
                output_folder=batch_output_dir,
                flatten_slides=flatten_slides,
                client_code=client_code,
                market_code=market_code,
                display_market_name=str(row[market_col]).strip(),
                file_prefix=f"{brand}_{market_code}"
            )
            details.append({
                "Brand": brand,
                "Market Code": requested_code,
                "Status": "Success" if result else "Failed"
            })

    expected = len(BUICK_GMC_ROLLUP_MARKET_CODES) * 2
    successful = sum(item["Status"] == "Success" for item in details)
    if not details:
        brand_values = sorted(
            catalog[brand_col].dropna().astype(str).str.strip().unique().tolist()
        )
        code_values = sorted(
            catalog[code_col].dropna().astype(str).str.strip().unique().tolist()
        )
        details.append({
            "Status": "Failed",
            "Error": (
                "Power BI returned no Buick/GMC rows for the configured market codes. "
                f"Returned catalog rows: {len(catalog)}. Expected codes: "
                f"{', '.join(BUICK_GMC_ROLLUP_MARKET_CODES)}. "
                f"Returned brands: {brand_values[:20]}. "
                f"Returned market-code samples: {code_values[:40]}"
            ),
        })
    return {
        "errors": expected - successful,
        "expected_decks": expected,
        "successful_decks": successful,
        "details": details,
        "output_folder": batch_output_dir
    }


def diagnose_buick_gmc_rollup_catalog():
    """Print the live Power BI catalog values used by the rollup matcher."""
    generator = SlideGenerationOrchestrator()
    if not generator.authenticate():
        return False

    query = """
    EVALUATE
    SELECTCOLUMNS(
        SUMMARIZECOLUMNS(
            'PoP Master Table'[Brand (Reporting)],
            'PoP Master Table'[Market Code],
            'PoP Master Table'[Market Name],
            'PoP Master Table'[Client Code]
        ),
        "Brand", 'PoP Master Table'[Brand (Reporting)],
        "MarketCode", 'PoP Master Table'[Market Code],
        "MarketName", 'PoP Master Table'[Market Name],
        "ClientCode", 'PoP Master Table'[Client Code]
    )
    """
    catalog = generator.powerbi.execute_dax_query(query)
    if catalog is None or catalog.empty:
        print("LIVE CATALOG: empty")
        return False

    print(f"LIVE CATALOG ROWS: {len(catalog)}")
    print(f"LIVE CATALOG COLUMNS: {list(catalog.columns)}")
    print("LIVE BRANDS:")
    print(catalog.iloc[:, 0].astype(str).value_counts().head(20).to_string())
    print("LIVE SAMPLE ROWS:")
    print(catalog.head(20).to_string(index=False))
    brand_col = generator._find_column(catalog, "Brand")
    code_col = generator._find_column(catalog, "MarketCode")
    if brand_col and code_col:
        matches = resolve_rollup_market_rows(catalog, brand_col, code_col)
        print(f"LIVE ROLLUP MATCHES: {len(matches)} of 22")
        for brand, requested_code, rows in matches:
            actual_codes = rows[code_col].dropna().astype(str).unique().tolist()
            print(f"  {brand} {requested_code}: {actual_codes}")
    return True

def process_batch_generation(target_date_iso, sel_brand, sel_type, codes_data, summary_only, flatten_slides=False,
                             is_ytd=True, ytd_min_outcomes=100, ytd_min_impressions=1000,
                             rolling_window_months=6, exclude_zero_cost_months=True,
                             skip_video_tactics_with_zero_completions=True,
                             min_tactic_spend=50, include_vehicle_slides=True):
    """
    Función generadora para Streamlit. Emite (yields) actualizaciones de estado 
    mientras procesa la generación de reportes por lotes.
    """
    from filters_manager import GeneralFiltersConfig
    GeneralFiltersConfig.update_batch({
        'ytd_filter_enabled': is_ytd,
        'ytd_min_outcomes': ytd_min_outcomes,
        'ytd_min_impressions': ytd_min_impressions,
        'rolling_window_months': rolling_window_months,
        'exclude_zero_cost_months': exclude_zero_cost_months,
        'skip_video_tactics_with_zero_completions': skip_video_tactics_with_zero_completions,
        'min_tactic_spend': min_tactic_spend
    })
    import time
    from datetime import datetime
    import os
    
    yield {"type": "start"}
    
    generator = SlideGenerationOrchestrator()
    if not generator.authenticate():
        yield {"type": "step_fail", "code": "AUTH", "reason": "Authentication failed"}
        return

    # --- AQUI ESTA LA "MAQUINA DEL TIEMPO" RESTAURADA ---
    base_output_dir = "Generated_Slides"
    timestamp_str = datetime.now().strftime("%b-%d_%H-%M")
    batch_output_dir = os.path.join(base_output_dir, timestamp_str)
    os.makedirs(batch_output_dir, exist_ok=True)
    # -----------------------------------------------------

    errors_count = 0
    details = []

    # Iteramos sobre los diccionarios enviados desde la UI
    for index, item in enumerate(codes_data):
        market_code = item["market"]
        client_code = item["client"]
        file_prefix = item.get("prefix") # Recibimos el prefijo inteligente
        
        yield {"type": "step_start", "index": index, "code": market_code, "client": client_code}
        
        try:
            # 1. Buscar el nombre del mercado basado en el market_code
            market_lookup_query = f"""
            EVALUATE
            SUMMARIZECOLUMNS(
                'PoP Master Table'[Market Name],
                FILTER('PoP Master Table', 'PoP Master Table'[Market Code] = "{market_code}")
            )
            """
            market_data = generator.powerbi.execute_dax_query(market_lookup_query)
            
            if market_data is None or market_data.empty:
                # Fallback: Usar el nombre de la UI si PBI no responde
                market_name = item.get("name", "Unknown Market")
                print(f"  [INFO] Market Name lookup failed for {market_code}, using UI name: {market_name}")
            else:
                # Si tenemos datos de PBI, verificamos si el nombre de la UI esta entre los resultados
                potential_names = market_data['PoP Master Table[Market Name]'].astype(str).unique().tolist()
                ui_name = item.get("name")
                
                if ui_name and ui_name in potential_names:
                    market_name = ui_name
                    print(f"  [INFO] Using UI-provided Market Name: {market_name}")
                else:
                    market_name = potential_names[0]
                    print(f"  [INFO] Using first PBI Market Name: {market_name}")
            
            # 2. Generar el reporte PASANDO LA CARPETA, EL CLIENT_CODE Y EL FILE_PREFIX
            # ZONE: filter by market_code only - aggregate all client codes under it.
            # LMA: keep client_code as the discriminator (unchanged).
            effective_client_code = None if sel_type == "ZONE" else client_code

            result = generator.generate_all_slides_for_market_month(
                brand=sel_brand,
                market_name=market_name,
                zone_lma_type=sel_type,
                month_year=target_date_iso,
                output_folder=batch_output_dir, 
                summary_only=summary_only,
                flatten_slides=flatten_slides,
                client_code=effective_client_code,
                market_code=market_code,  # <- market code flows end-to-end as the primary filter
                display_market_name=market_name,
                file_prefix=file_prefix,
                include_vehicle_slides=include_vehicle_slides
            )
            
            if result:
                yield {"type": "step_success", "market": market_name, "code": market_code, "client": client_code}
                details.append({"Market Code": market_code, "Status": "Success", "Error": ""})
            else:
                yield {"type": "step_fail", "code": market_code, "client": client_code, "reason": "Generación devolvió None"}
                errors_count += 1
                details.append({"Market Code": market_code, "Status": "Failed", "Error": "No data or gen error"})
                
        except Exception as e:
            yield {"type": "step_fail", "code": market_code, "client": client_code, "reason": str(e)}
            errors_count += 1
            details.append({"Market Code": market_code, "Status": "Failed", "Error": str(e)})
            
        time.sleep(0.5) # Pausa para no saturar la API

    # Resumen final
    yield {
        "type": "complete", 
        "errors": errors_count, 
        "details": details,
        "output_folder": batch_output_dir
    }

# ========== EJECUCIÓN COMO SCRIPT CLI (Stand-alone) ==========
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PowerBI Slide Generator")
    parser.add_argument("--brand", type=str, help="Brand name (e.g. Cadillac)")
    parser.add_argument("--market", type=str, help="Market name (e.g. Houston)")
    parser.add_argument("--month", type=str, help="Target month (ISO format or YYYY-MM-DD)")
    parser.add_argument("--type", type=str, default="LMA", help="Zone/LMA type")
    parser.add_argument("--all", action="store_true", help="Process all markets for selected brands")
    parser.add_argument("--quarter-rollup", action="store_true", help="Generate the 11-market Buick/GMC June-August 2026 rollup")
    parser.add_argument("--diagnose-rollup-catalog", action="store_true", help="Print live Power BI catalog columns and sample rows")
    
    args = parser.parse_args()
    
    print("="*70)
    print("PowerBI Slide Generator - Refactored Modular Version (w/ argparse)")
    print("="*70)

    if args.diagnose_rollup_catalog:
        raise SystemExit(0 if diagnose_buick_gmc_rollup_catalog() else 1)

    if args.quarter_rollup:
        rollup_result = process_buick_gmc_quarter_rollup()
        print(f"Generated {rollup_result.get('successful_decks', 0)} of {rollup_result.get('expected_decks', 22)} decks")
        print(f"Output folder: {rollup_result.get('output_folder', 'Unavailable')}")
        raise SystemExit(0 if rollup_result.get('errors', 1) == 0 else 1)
    
    generator = SlideGenerationOrchestrator()
    
    # CONFIGURATION FOR CLI
    USE_ALL_MARKETS = args.all
    brands = [args.brand] if args.brand else ["GMC", "Buick", "Cadillac"]
    market_name_val = args.market
    month_val = args.month if args.month else "2026-01-01"
    zone_lma_types = [args.type] if args.type else ["LMA"]
    
    if not generator.authenticate():
        print("Authentication failed")
    else:
        markets_to_process = []
        
        if USE_ALL_MARKETS:
            for brand in brands:
                for ztype in zone_lma_types:
                    query = f'''
                    EVALUATE
                    SUMMARIZECOLUMNS(
                        'PoP Master Table'[Market Code],
                        'PoP Master Table'[Market Name],
                        FILTER(
                            ALL('PoP Master Table'),
                            'PoP Master Table'[Brand (Reporting)] = "{brand}" &&
                            'PoP Master Table'[Zone/LMA] = "{ztype}"
                        )
                    )
                    '''
                    res = generator.powerbi.execute_dax_query(query)
                    if res is not None and not res.empty:
                        for _, row in res.iterrows():
                            markets_to_process.append({
                                'code': row['PoP Master Table[Market Code]'],
                                'name': row['PoP Master Table[Market Name]'],
                                'brand': brand,
                                'type': ztype
                            })
        else:
            # Single market mode
            # If no market name provided, default to common test cases if needed or error
            if not market_name_val:
                print("[ERROR] Please provide --market name or use --all")
                import sys
                sys.exit(1)
                
            for brand in brands:
                for ztype in zone_lma_types:
                    markets_to_process.append({
                        'code': "DISCOVERY", # Code will be resolved by metadata query
                        'name': market_name_val,
                        'brand': brand,
                        'type': ztype
                    })
        
        processed_markets = set()
        target_month_iso = month_val
        if "T" not in target_month_iso:
            target_month_iso += "T00:00:00"

        for item in markets_to_process:
            market_name = item['name']
            brand = item['brand']
            zone_lma_type = item['type']
            
            processing_key = (brand, market_name, zone_lma_type)
            if processing_key in processed_markets:
                continue
                
            print(f"\n{'='*70}")
            print(f"Generating Slides for {brand} {market_name}...")
            print(f"{'='*70}\n")
            
            result = generator.generate_all_slides_for_market_month(
                brand=brand,
                market_name=market_name,
                zone_lma_type=zone_lma_type,
                month_year=target_month_iso,
                output_folder="Generated_Slides",
                flatten_slides=True,
                client_code=None,
                display_market_name=market_name
            )
            
            if result:
                print(f"\n[OK] Success: {os.path.basename(result['filepath'])}")
                processed_markets.add(processing_key)
            else:
                print(f"\n[ERROR] Failed for {brand} {market_name}")
            
            time.sleep(0.5)

        print(f"\n{'='*70}")
        print("COMPLETE! Generated all brand decks in Generated_Slides folder")
        print(f"{'='*70}")
