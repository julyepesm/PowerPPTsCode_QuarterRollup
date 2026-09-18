"""
Display Tactic Resolution Helper
=================================

This module provides utilities to consistently resolve Display tactics
into BT Display or Retargeting Display based on Strategy field.

This ensures consistent handling across:
- Data queries
- Executive summary cards
- YTD charts
- Tactic slides
- All reporting
"""

import re


def _is_social_site(site):
    """Return True when the site identifies a social platform.

    Short aliases such as ``IG`` must match a complete token. A plain
    substring check incorrectly classified names such as ``DetroitTigers``
    as Instagram because they contain the letters ``IG``.
    """
    site_upper = str(site).upper().strip() if site else ""
    if not site_upper:
        return False

    social_platform_names = (
        'FACEBOOK', 'META', 'INSTAGRAM', 'TWITTER', 'SNAPCHAT',
        'SOCIAL', 'IG', 'FB'
    )
    alias_pattern = '|'.join(re.escape(name) for name in social_platform_names)
    return re.search(
        rf'(?<![A-Z0-9])(?:{alias_pattern})(?![A-Z0-9])',
        site_upper
    ) is not None


def resolve_display_tactic(tactic, strategy, site=None):
    """
    Resolve Display tactic into granular type based on Strategy and Site
    """
    t_upper = str(tactic).upper().strip()
    is_social_site = _is_social_site(site)

    # Normalize Social naming variations
    social_display_keywords = ['SOCIAL DISPLAY', 'META DISPLAY', 'PAID SOCIAL', 'FACEBOOK DISPLAY', 'META ADS']
    
    # Specific exclusion for Pinterest/TikTok if they come in as 'Social'
    if 'PINTEREST' in t_upper or 'TIKTOK' in t_upper:
        return tactic

    if t_upper in social_display_keywords or t_upper in ['SOCIAL', 'FACEBOOK', 'META', 'FB'] or is_social_site:
        if 'VIDEO' in t_upper:
            return 'Meta Video'
        return 'Meta Display'

    if tactic in ['Social Video', 'Meta Video'] or t_upper in ['SOCIAL VIDEO', 'META VIDEO']:
        return 'Meta Video'

    # If tactic is already a standard normalized name (CASE-INSENSITIVE check), return the standard version
    standard_tactics = ['PreRoll', 'FEP', 'YouTube', 'Meta Display', 'Meta Video', 'BT Display', 'Retargeting Display', 'Consideration Display', 'Audio', 'Search', 'TikTok', 'Pinterest Display', 'Pinterest Video']
    
    for std in standard_tactics:
        if t_upper == std.upper():
            return std

    # Only process strategy splitting if tactic is strictly "Display" 
    # (The generic bucket that needs splitting)
    if t_upper != 'DISPLAY' and t_upper != 'META DISPLAY' and not is_social_site:
        return tactic
    
    # If no strategy provided, default to BT Display if it's generic "Display"
    if not strategy or str(strategy).strip() == '':
        return 'BT Display' if tactic == 'Display' else tactic
    
    # Normalize strategy to handle case variations
    strategy_clean = str(strategy).strip()
    strategy_upper = strategy_clean.upper()
    
    # Define Consideration Display strategies
    consideration_keywords = ['CONSIDERATION', 'HPA']
    for keyword in consideration_keywords:
        if keyword in strategy_upper:
            return 'Consideration Display'

    # Define BT Display strategies (all non-retargeting strategies)
    bt_display_keywords = [
        'BT',
        'INMARKET',
        'IN MARKET',
        'IN-MARKET',
        'PURCHASE'
    ]
    
    # Check if it's a BT Display strategy
    for keyword in bt_display_keywords:
        if keyword in strategy_upper:
            return 'BT Display'
    
    # Check for Retargeting Display
    retargeting_keywords = ['RETARGETING', 'RETARGET']
    for keyword in retargeting_keywords:
        if keyword in strategy_upper:
            return 'Retargeting Display'
    
    # Unknown strategy - default to BT Display for safety if it's the generic tactic
    if tactic == 'Display':
        print(f"  ℹ Unknown Display strategy '{strategy_clean}' - defaulting to BT Display")
        return 'BT Display'
    
    return tactic

# Update the mapping for backward compatibility
DISPLAY_STRATEGY_MAPPING = {
    'BT': 'BT Display',
    'InMarket': 'BT Display',
    'In Market': 'BT Display',
    'Consideration': 'BT Display',
    'Purchase': 'BT Display',
    'Awareness': 'BT Display',
    'Prospecting': 'BT Display',
    'Conquest': 'BT Display',
    'Retargeting': 'Retargeting Display',
    'Remarketing': 'Retargeting Display'
}


def apply_display_resolution_to_dataframe(df, tactic_col='[Tactic (Reporting)]', strategy_col='[Strategy (groups)]', output_col='Tactic_Resolved'):
    """
    Apply Display resolution to entire DataFrame
    
    Creates a new column with resolved tactic names.
    
    Args:
        df (DataFrame): Input dataframe
        tactic_col (str): Name of tactic column
        strategy_col (str): Name of strategy column
        output_col (str): Name of output column to create
    
    Returns:
        DataFrame: DataFrame with new resolved tactic column
    
    Example:
        >>> df = apply_display_resolution_to_dataframe(df)
        >>> df['Tactic_Resolved'].value_counts()
        BT Display           1234
        Retargeting Display   567
        YouTube               890
        FEP                   456
    """
    df = df.copy()
    
    # Apply resolution row by row
    df[output_col] = df.apply(
        lambda row: resolve_display_tactic(
            row[tactic_col] if tactic_col in df.columns else None,
            row[strategy_col] if strategy_col in df.columns else None
        ),
        axis=1
    )
    
    return df


def get_display_tactic_from_row(row, tactic_col='[Tactic (Reporting)]', strategy_col='[Strategy (groups)]'):
    """
    Get resolved Display tactic from a single DataFrame row
    
    Convenience function for row-level operations.
    
    Args:
        row (Series): DataFrame row
        tactic_col (str): Name of tactic column
        strategy_col (str): Name of strategy column
    
    Returns:
        str: Resolved tactic name
    """
    tactic = row.get(tactic_col, None)
    strategy = row.get(strategy_col, None)
    return resolve_display_tactic(tactic, strategy)


# Mapping for backward compatibility
DISPLAY_STRATEGY_MAPPING = {
    'BT': 'BT Display',
    'InMarket': 'BT Display',
    'Consideration': 'BT Display',
    'Purchase': 'BT Display',
    'Retargeting': 'Retargeting Display'
}


if __name__ == "__main__":
    """Test the Display resolution logic"""
    print("=== DISPLAY TACTIC RESOLUTION TEST ===\n")
    
    test_cases = [
        ("Display", "BT", "BT Display"),
        ("Display", "InMarket", "BT Display"),
        ("Display", "Consideration", "BT Display"),
        ("Display", "Purchase", "BT Display"),
        ("Display", "Retargeting", "Retargeting Display"),
        ("Display", "bt", "BT Display"),  # Lowercase
        ("Display", "RETARGETING", "Retargeting Display"),  # Uppercase
        ("Display", None, "Display"),  # No strategy
        ("YouTube", "BT", "YouTube"),  # Non-Display tactic
        ("FEP", "Retargeting", "FEP"),  # Non-Display tactic
    ]
    
    print("Test Results:")
    print("-" * 70)
    
    passed = 0
    failed = 0
    
    for tactic, strategy, expected in test_cases:
        result = resolve_display_tactic(tactic, strategy)
        status = "[OK]" if result == expected else "[FAIL]"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} Tactic: {tactic:15} Strategy: {str(strategy):15} → {result:20} (expected: {expected})")
    
    print("-" * 70)
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("[OK] All tests passed!")
    else:
        print("[FAIL] Some tests failed!")
