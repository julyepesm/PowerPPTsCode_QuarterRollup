# 🔍 Market Search & Filtering Logic

This document explains how the **PowerPPTs** engine identifies and retrieves data for specific markets within the Power BI dataset.

## 🏗️ Core Logic Flow
The market search logic is centralized in the `DataQueries` class (`Scripts/data_queries.py`), primarily within the `_build_common_filters_list` helper method. This approach ensures that every query (Metadata, Impressions, Conversions) uses the exact same identification rules.

### 1. The "Code-First" Strategy
The system prioritizes **Market Codes** over **Market Names** to ensure data integrity.
- **Why?** Market names can vary slightly in the database (e.g., "Miami-Ft. Lauderdale" vs "Miami FL"), and more importantly, they can be ambiguous when multiple clients share the same city (e.g., "SPOKANE, WA" could map to `SPOWA-GSPO` and `SPOWA-XSPO`). The Market Code is the minimum unique identifier that also inherently encodes the client.
- **Logic**:
  ```python
  if market_code and market_code != "XXXXX":
      filters.append(f"'PoP Master Table'[Market Code] = \"{market_code}\"")
  elif market_name:
      # Fallback to name-based search
  ```

### 2. Strict vs. Relaxed Name Matching
When a Market Code is not available, the system falls back to the Market Name with two distinct modes:
- **Strict Mode (`strict=True`)**: Performs an exact case-sensitive match.
  - *DAX*: `'PoP Master Table'[Market Name] = "Market Name"`
- **Relaxed Mode (`strict=False`)**: Performs a partial string search. This is useful during the "Discovery" phase or when the user provides a shortened name.
  - *DAX*: `CONTAINSSTRING('PoP Master Table'[Market Name], "Market Name")`

### 3. Coupling with Brand & Tier
A market is never searched for in isolation. It is always coupled with:
- **Brand**: `'PoP Master Table'[Brand (Reporting)] = "Chevrolet"`
- **Tier (Zone/LMA)**: `'PoP Master Table'[Zone/LMA] = "LMA"`
- **Date**: `'Master Date Table'[Month Year] = DATEVALUE("2026-01-01")`

---

## 🛰️ Metadata Discovery Sequence
Before generating any slides, the orchestrator performs a **Metadata Fetch**:

1. **Initial Search**: The UI fetches all valid combinations of Brand + Market + Date to populate user dropdowns.
2. **Metadata Query**: Once a market is selected, the script calls `get_market_metadata_query` to retrieve the hidden **Market Code** and **Region**. This query prefers the `market_code` as a primary identifier to resolve any ambiguities immediately.
3. **Internal Remapping**: The orchestrator (`main_slide_generator.py`) takes these returned values and uses them for all subsequent "Data Slides" queries. This ensures that even if the user selected "Miami", the actual queries use `Market Code = 'XMFL'`.

---

## 🛡️ Handling Anomalies (Client Code Logic)
A recent addition handles scenarios where multiple distinct clients (Advertisers) share the same Market Name or Market Code.

- **LMA vs ZONE Discrimination**:
  - **LMA Mode**: If a `client_code` is provided, it is kept as a mandatory discriminator filter. This prevents data leakage between different dealerships or regions sharing the same market name.
  - **ZONE Mode**: The `client_code` is intentionally bypassed (set to `None`). The system filters only by `market_code`, allowing it to aggregate all underlying client codes within that zone.
- **Auto-Correction**: If the requested Client Code returns no data, the engine checks if there is exactly one alternative client for that market and automatically remaps the query to use the active client.

---
> [!IMPORTANT]
> **Key Maintenance Rule**: If a market name changes in the Power BI dashboard, the system will still function correctly as long as the **Market Code** remains stable, thanks to the prioritization logic in `_build_common_filters_list`.

---

## 🔄 Version History (Recent Updates)
**May 2026 Update (`main` branch merge)**: 
- **LMA vs ZONE Logic**: Introduced distinct logic for `ZONE` reporting where `client_code` is set to `None` to ensure all clients under a market code are aggregated, while `LMA` continues to use `client_code` as a discriminator.
- **Strict Market Code Usage**: Updated `get_market_metadata_query` to prioritize `market_code` over `market_name` to fix ambiguity issues with overlapping city names (e.g., SPOWA-GSPO / SPOWA-XSPO).
