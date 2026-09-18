class DataQueries:
    """Handles all DAX queries for Power BI data retrieval"""

    def _build_common_filters_list(self, brand, market_name, month_year=None, tactic=None, site=None, audience=None, zone_lma=None, strategy=None, client_code=None, market_code=None, strict=False, start_month_year=None, end_month_year=None):
        """Helper to build list of DAX filter strings for CALCULATETABLE"""
        
        # 1. Primary Filters (Market and Brand)
        filters = [f"'PoP Master Table'[Brand (Reporting)] = \"{brand}\""]
        
        # PRIORITIZE MARKET CODE: If we have a code, use it. Match against Name only as secondary/relaxed if no code.
        # This solves the "multiple names for same code" issue.
        if market_code and market_code != "XXXXX":
            filters.append(f"'PoP Master Table'[Market Code] = \"{market_code}\"")
        elif market_name:
            if strict:
                filters.append(f"'PoP Master Table'[Market Name] = \"{market_name}\"")
            else:
                filters.append(f"CONTAINSSTRING('PoP Master Table'[Market Name], \"{market_name}\")")

        # 2. Date Filter
        if start_month_year and end_month_year:
            start_date = start_month_year.split("T")[0]
            end_date = end_month_year.split("T")[0]
            filters.append(f"'Master Date Table'[Month Year] >= DATEVALUE(\"{start_date}\")")
            filters.append(f"'Master Date Table'[Month Year] <= DATEVALUE(\"{end_date}\")")
        elif month_year:
            clean_date = month_year.split("T")[0]
            filters.append(f"'Master Date Table'[Month Year] = DATEVALUE(\"{clean_date}\")")

        # 3. Tactic Filter (STRENGTHENED TO HANDLE LISTS)
        if tactic:
            if isinstance(tactic, list):
                if len(tactic) > 0:
                    t_parts = [f"'PoP Master Table'[Tactic (Reporting)] = \"{t}\"" for t in tactic]
                    filters.append("(" + " || ".join(t_parts) + ")")
            else:
                filters.append(f"'PoP Master Table'[Tactic (Reporting)] = \"{tactic}\"")
        if site:
            if isinstance(site, list):
                site_parts = [f"'PoP Master Table'[Site (Reporting)] = \"{s}\"" for s in site]
                filters.append("(" + " || ".join(site_parts) + ")")
            else:
                filters.append(f"'PoP Master Table'[Site (Reporting)] = \"{site}\"")
        if audience:
            filters.append(f"'PoP Master Table'[Audience] = \"{audience}\"")
        if zone_lma:
            filters.append(f"'PoP Master Table'[Zone/LMA] = \"{zone_lma}\"")
            
        # client_code is always added as an additional filter when available.
        # It is safe to combine with market_code because market_code now always comes
        # from the UI directly (never from an ambiguous iloc[0] lookup).
        #
        # This handles two scenarios correctly:
        #   - Convention followed (e.g. market_code="SPOWA-GSPO", client_code="GSPO"):
        #       â†’ filter is redundant but harmless
        #   - Convention NOT followed (e.g. market_code="SPOWA", two clients exist):
        #       â†’ client_code is the necessary discriminator
        if client_code:
            if isinstance(client_code, list):
                cc_parts = [f"'PoP Master Table'[Client Code] = \"{cc}\"" for cc in client_code]
                filters.append("(" + " || ".join(cc_parts) + ")")
            else:
                filters.append(f"'PoP Master Table'[Client Code] = \"{client_code}\"")

        if strategy:
            if isinstance(strategy, list):
                if len(strategy) > 0:
                    or_parts = [f"'PoP Master Table'[Strategy (groups)] = \"{s}\"" for s in strategy]
                    filters.append("(" + " || ".join(or_parts) + ")")
            else:
                filters.append(f"'PoP Master Table'[Strategy (groups)] = \"{strategy}\"")

        return filters
    
    def get_all_combinations_query(self, gm_brands):
        """Get all GM brand markets and available dates"""
        brand_filter = " || ".join([f'\'PoP Master Table\'[Brand (Reporting)] = "{brand}"' for brand in gm_brands])
        
        query = f"""
        EVALUATE
        CALCULATETABLE(
            SUMMARIZE(
                'PoP Master Table',
                'PoP Master Table'[Brand (Reporting)],
                'PoP Master Table'[Market Name],
                'PoP Master Table'[Zone/LMA],
                'Master Date Table'[Month Year]
            ),
            {brand_filter}
        )
        """
        return query
    
    def get_tactic_site_combinations_query(self, brand, market_name, month_year=None, zone_lma=None, client_code=None, market_code=None, strict=False, start_month_year=None, end_month_year=None):
        """Get all tactic and site combinations for a specific brand/market/month"""
        filters = self._build_common_filters_list(
            brand, market_name, month_year=month_year, 
            zone_lma=zone_lma, client_code=client_code,
            market_code=market_code, strict=strict,
            start_month_year=start_month_year, end_month_year=end_month_year
        )
        filter_str = ", ".join(filters)
        
        query = f"""
        EVALUATE
        CALCULATETABLE(
            SUMMARIZE(
                'PoP Master Table',
                'PoP Master Table'[Tactic (Reporting)],
                'PoP Master Table'[Site (Reporting)],
                'PoP Master Table'[Audience],
                'PoP Master Table'[Strategy (groups)],
                'PoP Master Table'[Zone/LMA],
                'PoP Master Table'[Market Code],
                'PoP Master Table'[Region],
                'PoP Master Table'[Client Code]
            ),
            {filter_str}
        )
        """
        return query
    
    def get_detailed_metrics_query(self, brand, market_name, month_year, tactic=None, site=None, audience=None, zone_lma=None, strategy=None, client_code=None, market_code=None, strict=False):
        """Get comprehensive metrics for a specific brand/market/month/tactic/site"""
        filters = self._build_common_filters_list(
            brand, market_name, month_year=month_year,
            tactic=tactic, site=site, audience=audience,
            zone_lma=zone_lma, strategy=strategy, client_code=client_code,
            market_code=market_code, strict=strict
        )
        filter_str = ", ".join(filters)
        
        query = f"""
        EVALUATE
        CALCULATETABLE(
            SUMMARIZE(
                'PoP Master Table',
                'PoP Master Table'[Brand (Reporting)],
                'PoP Master Table'[Market Name],
                'PoP Master Table'[Tactic (Reporting)],
                'PoP Master Table'[Strategy (groups)],
                'PoP Master Table'[Zone/LMA],
                "Total Cost", SUM('PoP Master Table'[Total Cost]),
                "Impressions", SUM('PoP Master Table'[Impressions]),
                "Video Completions", SUM('PoP Master Table'[Video Completions]),
                "Video Plays", SUM('PoP Master Table'[Video Plays]),
                "Clicks", SUM('PoP Master Table'[Clicks]),
                "Total Conversions", SUM('PoP Master Table'[Total Conversions]),
                "Click to Calls", SUM('PoP Master Table'[Click to Calls]),
                "Email Leads", SUM('PoP Master Table'[Email Leads]),
                "Hours & Directions", SUM('PoP Master Table'[Hours & Directions]),
                "Inventory Searches", SUM('PoP Master Table'[Inventory Searches]),
                "VDP Views", SUM('PoP Master Table'[VDP Views]),
                "Window Stickers", SUM('PoP Master Table'[Window Stickers]),
                "Audio Completes", SUM('PoP Master Table'[Audio Completes]),
                "Audio Starts", SUM('PoP Master Table'[Audio Starts]),
                "Unique Viewable Impressions", SUM('PoP Master Table'[Unique Viewable Impressions]),
                "Unique Measured Impressions", SUM('PoP Master Table'[Unique Measured Impressions]),
                "Active View: Viewable Impressions", SUM('PoP Master Table'[Active View: Viewable Impressions]),
                "Active View: Measurable Impressions", SUM('PoP Master Table'[Active View: Measurable Impressions])
            ),
            {filter_str}
        )
        """
        return query
    
    def get_historical_metrics_query(self, brand, market_name, month_year, months=6, tactic=None, site=None, audience=None, zone_lma=None, strategy=None, client_code=None, market_code=None, strict=False):
        """
        Get historical metrics with rolling window filtering directly in DAX
        """
        filters = self._build_common_filters_list(
            brand, market_name, 
            tactic=tactic, site=site, audience=audience,
            zone_lma=zone_lma, strategy=strategy, client_code=client_code,
            market_code=market_code, strict=strict
        )
        
        # Add rolling window filter in DAX: Last X months relative to report date
        clean_date = month_year.split("T")[0]
        filters.append(f"'Master Date Table'[Month Year] >= EDATE(DATEVALUE(\"{clean_date}\"), -({months}-1))")
        filters.append(f"'Master Date Table'[Month Year] <= DATEVALUE(\"{clean_date}\")")
        
        # Filter ValidMonth is a Measure so it must be evaluated with FILTER
        filter_str = ", ".join(filters)
        
        query = f"""
        EVALUATE
        CALCULATETABLE(
            SUMMARIZE(
                'PoP Master Table',
                'Master Date Table'[Month Year],
                'PoP Master Table'[Strategy (groups)],
                'PoP Master Table'[Tactic (Reporting)],
                'PoP Master Table'[Site (Reporting)],
                'PoP Master Table'[Audience],
                "Total Cost", SUM('PoP Master Table'[Total Cost]),
                "Impressions", SUM('PoP Master Table'[Impressions]),
                "Video Completions", SUM('PoP Master Table'[Video Completions]),
                "Video Plays", SUM('PoP Master Table'[Video Plays]),
                "Clicks", SUM('PoP Master Table'[Clicks]),
                "Total Conversions", SUM('PoP Master Table'[Total Conversions]),
                "Click to Calls", SUM('PoP Master Table'[Click to Calls]),
                "Email Leads", SUM('PoP Master Table'[Email Leads]),
                "Hours & Directions", SUM('PoP Master Table'[Hours & Directions]),
                "Inventory Searches", SUM('PoP Master Table'[Inventory Searches]),
                "VDP Views", SUM('PoP Master Table'[VDP Views]),
                "Window Stickers", SUM('PoP Master Table'[Window Stickers]),
                "Audio Completes", SUM('PoP Master Table'[Audio Completes]),
                "Audio Starts", SUM('PoP Master Table'[Audio Starts]),
                "Unique Viewable Impressions", SUM('PoP Master Table'[Unique Viewable Impressions]),
                "Unique Measured Impressions", SUM('PoP Master Table'[Unique Measured Impressions]),
                "Active View: Viewable Impressions", SUM('PoP Master Table'[Active View: Viewable Impressions]),
                "Active View: Measurable Impressions", SUM('PoP Master Table'[Active View: Measurable Impressions])
            ),
            {filter_str}
        )
        """
        return query

    def get_vehicle_current_metrics_query(self, brand, market_name, month_year,
                                          zone_lma=None, client_code=None,
                                          market_code=None, strict=False):
        """Get current-month metrics at the grain required by vehicle slides."""
        filters = self._build_common_filters_list(
            brand, market_name, month_year=month_year,
            zone_lma=zone_lma, client_code=client_code,
            market_code=market_code, strict=strict
        )
        filter_str = ", ".join(filters)

        return f"""
        EVALUATE
        CALCULATETABLE(
            SUMMARIZE(
                'PoP Master Table',
                'PoP Master Table'[Vehicle],
                'PoP Master Table'[Tactic (Reporting)],
                'PoP Master Table'[Strategy (groups)],
                'PoP Master Table'[Site (Reporting)],
                'PoP Master Table'[Audience],
                'PoP Master Table'[Zone/LMA],
                "Total Cost", SUM('PoP Master Table'[Total Cost]),
                "Impressions", SUM('PoP Master Table'[Impressions]),
                "Video Completions", SUM('PoP Master Table'[Video Completions]),
                "Video Plays", SUM('PoP Master Table'[Video Plays]),
                "Clicks", SUM('PoP Master Table'[Clicks]),
                "Total Conversions", SUM('PoP Master Table'[Total Conversions])
            ),
            {filter_str}
        )
        """

    def get_vehicle_historical_metrics_query(self, brand, market_name, month_year,
                                             months=3, zone_lma=None,
                                             client_code=None, market_code=None,
                                             strict=False):
        """Get rolling vehicle/tactic metrics for vehicle Insights charts."""
        filters = self._build_common_filters_list(
            brand, market_name, zone_lma=zone_lma,
            client_code=client_code, market_code=market_code,
            strict=strict
        )
        clean_date = month_year.split("T")[0]
        filters.append(
            f"'Master Date Table'[Month Year] >= "
            f"EDATE(DATEVALUE(\"{clean_date}\"), -({months}-1))"
        )
        filters.append(
            f"'Master Date Table'[Month Year] <= DATEVALUE(\"{clean_date}\")"
        )
        filter_str = ", ".join(filters)

        return f"""
        EVALUATE
        CALCULATETABLE(
            SUMMARIZE(
                'PoP Master Table',
                'Master Date Table'[Month Year],
                'PoP Master Table'[Vehicle],
                'PoP Master Table'[Tactic (Reporting)],
                'PoP Master Table'[Strategy (groups)],
                'PoP Master Table'[Site (Reporting)],
                'PoP Master Table'[Audience],
                "Total Cost", SUM('PoP Master Table'[Total Cost]),
                "Impressions", SUM('PoP Master Table'[Impressions]),
                "Video Completions", SUM('PoP Master Table'[Video Completions]),
                "Video Plays", SUM('PoP Master Table'[Video Plays]),
                "Clicks", SUM('PoP Master Table'[Clicks]),
                "Total Conversions", SUM('PoP Master Table'[Total Conversions])
            ),
            {filter_str}
        )
        """
    
    def get_market_metadata_query(self, brand, market_name, month_year, zone_lma=None, market_code=None):
        """Get market metadata (code, region, exact names) for a specific brand/market/month.
        
        If market_code is provided it is used as the primary identifier (exact, unambiguous match).
        Falls back to market_name only when market_code is unknown â€” note that market_name can be
        shared across multiple markets (e.g. "SPOKANE, WA" â†’ SPOWA-GSPO and SPOWA-XSPO).
        """
        clean_month_year = month_year.split("T")[0]
        
        filters = [
            f"'PoP Master Table'[Brand (Reporting)] = \"{brand}\"",
            f"'Master Date Table'[Month Year] = DATEVALUE(\"{clean_month_year}\")"
        ]
        
        # Prefer market_code â€” it is the minimum unique identifier and already encodes the client.
        # Market Name is ambiguous when two clients share the same city (e.g. SPOWA-GSPO / SPOWA-XSPO).
        if market_code and market_code != "XXXXX":
            filters.append(f"'PoP Master Table'[Market Code] = \"{market_code}\"")
        else:
            filters.append(f"'PoP Master Table'[Market Name] = \"{market_name}\"")
        
        if zone_lma:
            filters.append(f"'PoP Master Table'[Zone/LMA] = \"{zone_lma}\"")
        
        filter_str = ", ".join(filters)
        
        query = f"""
        EVALUATE
        CALCULATETABLE(
            SUMMARIZE(
                'PoP Master Table',
                'PoP Master Table'[Brand (Reporting)],
                'PoP Master Table'[Market Name],
                'PoP Master Table'[Market Code],
                'PoP Master Table'[Region]
            ),
            {filter_str}
        )
        """
        return query

    def get_executive_summary_query(self, brand, market_name, month_year=None, zone_lma=None, client_code=None, market_code=None, strict=False, start_month_year=None, end_month_year=None):
        """Build query for executive summary using CALCULATETABLE"""
        filters = self._build_common_filters_list(
            brand, market_name, month_year=month_year,
            zone_lma=zone_lma, client_code=client_code,
            market_code=market_code, strict=strict,
            start_month_year=start_month_year, end_month_year=end_month_year
        )
            
        filter_str = ", ".join(filters)
        query = f"""
        EVALUATE
        CALCULATETABLE(
            SUMMARIZE(
                'PoP Master Table',
                'PoP Master Table'[Brand (Reporting)],
                'PoP Master Table'[Market Name],
                'PoP Master Table'[Tactic (Reporting)],
                'PoP Master Table'[Site (Reporting)],
                'PoP Master Table'[Audience],
                'PoP Master Table'[Strategy (groups)],
                'PoP Master Table'[Zone/LMA],
                'Master Date Table'[Month Year],
                "Impressions", SUM('PoP Master Table'[Impressions]),
                "Total Cost", SUM('PoP Master Table'[Total Cost]),
                "Video Completions", SUM('PoP Master Table'[Video Completions]),
                "Video Plays", SUM('PoP Master Table'[Video Plays]),
                "Total Conversions", SUM('PoP Master Table'[Total Conversions]),
                "Clicks", SUM('PoP Master Table'[Clicks]),
                "Audio Completes", SUM('PoP Master Table'[Audio Completes]),
                "Audio Starts", SUM('PoP Master Table'[Audio Starts])
            ),
            {filter_str}
        )
        """
        return query

    def get_ytd_impressions_by_vehicle_query(self, brand, market_name, month_year, zone_lma=None, client_code=None, market_code=None, strict=False, months=None):
        """
        Get YTD impressions data grouped by vehicle and month
        Uses a 6-month rolling window to match Cadillac reporting standards.
        """
        clean_date = month_year.split("T")[0]
        
        filters = self._build_common_filters_list(
            brand, market_name,
            zone_lma=zone_lma, client_code=client_code,
            market_code=market_code, strict=strict
        )

        filters = [f for f in filters if "'Master Date Table'[Month Year]" not in f]

        if months is None:
            filters.append(f"'Master Date Table'[Month Year] >= DATE(YEAR(DATEVALUE(\"{clean_date}\")), 1, 1)")
            filters.append(f"'Master Date Table'[Month Year] <= DATEVALUE(\"{clean_date}\")")
        else:
            filters.append(f"'Master Date Table'[Month Year] >= EDATE(DATEVALUE(\"{clean_date}\"), -({months}-1))")
            filters.append(f"'Master Date Table'[Month Year] <= DATEVALUE(\"{clean_date}\")")

        filter_str = ", ".join(filters)
        
        query = f"""
        EVALUATE
        CALCULATETABLE(
            SUMMARIZE(
                'PoP Master Table',
                'Master Date Table'[Month Year],
                'PoP Master Table'[Vehicle],
                "Impressions", SUM('PoP Master Table'[Impressions]),
                "Total Cost", SUM('PoP Master Table'[Total Cost])
            ),
            {filter_str}
        )
        """
        return query

    def get_ytd_kba_by_tactic_query(self, brand, market_name, month_year, zone_lma=None, client_code=None, market_code=None, strict=False, months=None):
        """
        Get YTD KBA (Total Conversions) data grouped by tactic and month
        Uses a 6-month rolling window to match Cadillac reporting standards.
        """
        clean_date = month_year.split("T")[0]
        
        filters = self._build_common_filters_list(
            brand, market_name,
            zone_lma=zone_lma, client_code=client_code,
            market_code=market_code, strict=strict
        )
        filters = [f for f in filters if "'Master Date Table'[Month Year]" not in f]

        if months is None:
            filters.append(f"'Master Date Table'[Month Year] >= DATE(YEAR(DATEVALUE(\"{clean_date}\")), 1, 1)")
            filters.append(f"'Master Date Table'[Month Year] <= DATEVALUE(\"{clean_date}\")")
        else:
            filters.append(f"'Master Date Table'[Month Year] >= EDATE(DATEVALUE(\"{clean_date}\"), -({months}-1))")
            filters.append(f"'Master Date Table'[Month Year] <= DATEVALUE(\"{clean_date}\")")

        filter_str = ", ".join(filters)
        
        query = f"""
        EVALUATE
        CALCULATETABLE(
            SUMMARIZE(
                'PoP Master Table',
                'Master Date Table'[Month Year],
                'PoP Master Table'[Tactic (Reporting)],
                "KBA", SUM('PoP Master Table'[Total Conversions]),
                "Total Cost", SUM('PoP Master Table'[Total Cost])
            ),
            {filter_str}
        )
        """
        return query
