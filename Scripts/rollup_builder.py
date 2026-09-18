"""Reusable rollup selection and batch execution, independent of Streamlit."""

from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re

import pandas as pd

from data_queries import DataQueries
from utils import find_column
import settings


def normalize_period(start, end):
    start = date.fromisoformat(str(start).split('T')[0]).replace(day=1)
    end = date.fromisoformat(str(end).split('T')[0]).replace(day=1)
    if start > end:
        raise ValueError('Start month must be before or equal to end month.')
    return start.isoformat(), end.isoformat()


def quarter_period(year, quarter):
    if quarter not in (1, 2, 3, 4):
        raise ValueError('Quarter must be Q1, Q2, Q3, or Q4.')
    month = (quarter - 1) * 3 + 1
    return date(year, month, 1).isoformat(), date(year, month + 2, 1).isoformat()


def period_label(start, end):
    start, end = map(date.fromisoformat, normalize_period(start, end))
    if start == end:
        return end.strftime('%B %Y')
    if start.year == end.year:
        return f"{start:%B}-{end:%B %Y}"
    return f"{start:%B %Y}-{end:%B %Y}"


def catalog_query(brand, tier, start, end):
    start, end = normalize_period(start, end)
    if brand not in settings.GM_BRANDS or tier not in ('LMA', 'ZONE'):
        raise ValueError('Choose a supported brand and tier.')
    filters = DataQueries()._build_common_filters_list(
        brand, None, zone_lma=tier, start_month_year=start, end_month_year=end)
    fields = {'Brand': 'Brand (Reporting)', 'Type': 'Zone/LMA', 'Region': 'Region',
              'MarketName': 'Market Name', 'MarketCode': 'Market Code', 'ClientCode': 'Client Code'}
    columns = ',\n'.join(f"'PoP Master Table'[{name}]" for name in fields.values())
    aliases = ',\n'.join(f'"{alias}", \'PoP Master Table\'[{name}]' for alias, name in fields.items())
    return f"""EVALUATE
    SELECTCOLUMNS(
        CALCULATETABLE(SUMMARIZE('PoP Master Table', {columns}), {', '.join(filters)}),
        {aliases}
    )"""


def load_catalog(generator, brand, tier, start, end):
    if not generator.authenticate():
        raise RuntimeError('Power BI authentication failed. Follow the sign-in instructions and try again.')
    raw = generator.powerbi.execute_dax_query(catalog_query(brand, tier, start, end))
    fields = ['Brand', 'Type', 'Region', 'MarketName', 'MarketCode', 'ClientCode']
    if raw is None:
        raise RuntimeError('Power BI could not load the market catalog. See the terminal for details.')
    if raw.empty:
        return pd.DataFrame(columns=fields)
    clean = pd.DataFrame(index=raw.index)
    for field in fields:
        column = find_column(raw, field)
        # executeQueries can omit entirely blank columns, notably ClientCode for ZONE.
        if column is None and field not in ('Region', 'ClientCode', 'MarketName'):
            raise ValueError(f'Market catalog is missing {field}. Returned columns: {list(raw.columns)}')
        clean[field] = raw[column].fillna('').astype(str).str.strip() if column else ''
    return clean.drop_duplicates().reset_index(drop=True)


def build_targets(catalog, brand, tier, region=None):
    """Return selectable report scopes plus visible unresolved mapping rows."""
    data = catalog[(catalog.Brand == brand) & (catalog.Type == tier)].copy()
    if region is not None:
        data = data[data.Region == region]
    if tier == 'ZONE':
        data['ClientCode'] = ''
    targets, issues = [], []
    for (source_region, client), rows in data.groupby(['Region', 'ClientCode'], dropna=False, sort=True):
        if tier == 'LMA' and (not client or client.upper() in ('N/A', 'NAN', 'UNKNOWN')):
            issues.append({'Region': source_region, 'Client Code': client, 'Issue': 'LMA rows have no usable Client Code', 'Rows': len(rows)})
            continue
        combined = tier == 'LMA' and brand == 'Buick' and client == 'XTPC'
        if combined:
            scopes = [(None, rows, 'Tallahassee-Panama City, FL')]
        else:
            codes = rows.MarketCode.fillna('').astype(str).str.strip()
            valid = ~codes.str.upper().isin(['', 'N/A', 'NAN', 'UNKNOWN', 'XXXXX'])
            if (~valid).any():
                issues.append({'Region': source_region, 'Client Code': client,
                               'Issue': 'Rows have no usable Market Code; cannot assign to a deck',
                               'Rows': int((~valid).sum())})
            scopes = [(code, group, None) for code, group in rows[valid].groupby('MarketCode', sort=True)]
        for market, group, display in scopes:
            names = sorted(name for name in group.MarketName.unique() if name and name.upper() not in ('N/A', 'NAN'))
            display = display or (names[0] if names else market)
            report_code = f'{client}-{market}' if client and market else client or market
            known_markets = {code for code in rows.MarketCode if code and str(code).upper() not in ('N/A', 'NAN', 'UNKNOWN', 'XXXXX')}
            filename_code = report_code if client and not combined and len(known_markets) > 1 else client or market
            scope = [brand, tier, source_region, client, market]
            target_id = hashlib.sha256(json.dumps(scope).encode()).hexdigest()[:16]
            targets.append({'id': target_id, 'brand': brand, 'tier': tier,
                            'region': source_region, 'client_code': client or None,
                            'market_code': market, 'display_market_name': display,
                            'report_code': report_code,
                            'filename_code': filename_code,
                            'label': f'{report_code} | {display} | {source_region or "Unassigned region"}'})
    return targets, issues


def safe_filename(value):
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', str(value)).strip('._') or 'Unassigned'


def report_filename_stem(target, start, end, period_mode='Month range', split_client=False):
    start, end = normalize_period(start, end)
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if period_mode == 'Quarter':
        quarter = (first.month - 1) // 3 + 1
        if (start, end) != quarter_period(first.year, quarter):
            raise ValueError('Quarter filenames require a complete calendar quarter.')
        label = f'Q{quarter} {first.year}'
    elif period_mode == 'Month range':
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
        a, b = months[first.month - 1], months[last.month - 1]
        if first == last:
            label = f'{a} {first.year}'
        elif first.year == last.year:
            label = f'{a}-{b} {last.year}'
        else:
            label = f'{a} {first.year}-{b} {last.year}'
    else:
        raise ValueError('Choose Month range or Quarter.')
    code = target.get('filename_code') or target['client_code'] or target['market_code']
    if split_client or (target['brand'] == 'GMC' and target['client_code'] == 'XTPC'):
        code = target['report_code']
    return f'{code} {target["brand"]} {label} Summary'


def compact_deck_path(folder, brand, tier, region, report_code, filename_stem=None):
    """Keep Windows/Office paths short even under a long OneDrive root."""
    folder = Path(folder).resolve()
    scope = [brand, tier, region, report_code]
    digest = hashlib.sha256(json.dumps(scope).encode()).hexdigest()[:8]
    readable = filename_stem or '_'.join(safe_filename(part) for part in scope)
    readable = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', readable).strip(' .')
    # Reserve room for extension, scope identity, and a collision counter.
    budget = 240 - len(str(folder)) - 1 - len(f'_{digest}_9999.pptx')
    if budget < 12:
        raise ValueError('The output folder path is too long. Choose a shorter output folder.')
    stem = readable if len(readable) <= budget else f'{readable[:budget]}_{digest}'
    path = folder / f'{stem}.pptx'
    counter = 1
    while path.exists():
        path = folder / f'{stem} ({counter + 1}).pptx'
        counter += 1
        if counter > 9999:
            raise ValueError('Too many files with the same report name in this folder.')
    return str(path)


def generate_rollup_batch(generator, targets, start, end, output_folder='Generated_Slides',
                          flatten_slides=False, progress=None, catalog_issues=None, period_mode='Month range'):
    start, end = normalize_period(start, end)
    if not targets:
        raise ValueError('Select at least one market.')
    if len({target['id'] for target in targets}) != len(targets):
        raise ValueError('A report scope was selected more than once.')
    filenames = []
    for target in targets:
        markets = {t['market_code'] for t in targets
                   if t['brand'] == target['brand'] and t['client_code'] == target['client_code']}
        filenames.append(report_filename_stem(target, start, end, period_mode,
                                               split_client=bool(target['client_code']) and len(markets) > 1))
    if not generator.authenticate():
        raise RuntimeError('Power BI authentication failed.')
    folder = Path(output_folder) / f"Rollup_{start[:7]}_{end[:7]}_{datetime.now():%Y%m%d_%H%M%S_%f}"
    folder.mkdir(parents=True)
    result = {'start_month': start, 'end_month': end, 'period_mode': period_mode,
              'ytd_start_month': f'{end[:4]}-01-01', 'expected_decks': len(targets),
              'successful_decks': 0, 'errors': 0, 'details': [],
              'output_folder': str(folder), 'catalog_issues': catalog_issues or []}
    (folder / 'selection.json').write_text(json.dumps(targets, indent=2), encoding='utf-8')

    def save_results():
        (folder / 'rollup_results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        pd.DataFrame(result['details']).to_csv(folder / 'rollup_results.csv', index=False)

    save_results()
    for index, target in enumerate(targets):
        if progress:
            progress(index, len(targets), target)
        detail = {'Brand': target['brand'], 'Tier': target['tier'], 'Region': target['region'],
                  'Client Code': target['client_code'], 'Market Code': target['market_code'],
                  'Report Code': target['report_code'], 'Status': 'Failed'}
        try:
            generated = generator.generate_quarter_rollup_for_market(
                brand=target['brand'], market_name=None, start_month_year=start,
                end_month_year=end, zone_lma_type=target['tier'],
                output_folder=str(folder), flatten_slides=flatten_slides, compact_output=True,
                filename_stem=filenames[index],
                client_code=target['client_code'], market_code=target['market_code'],
                display_market_name=target['display_market_name'], region=target['region'],
                file_prefix=f"{safe_filename(target['report_code'])}_{start[:7]}_{end[:7]}")
            if not generated:
                raise RuntimeError('No data returned for this report scope in the selected period.')
            detail.update(Status='Success', File=generated['filepath'])
            result['successful_decks'] += 1
        except (Exception, SystemExit) as exc:
            detail['Error'] = str(exc) or 'Report generation stopped unexpectedly.'
            result['errors'] += 1
        result['details'].append(detail)
        save_results()
    if progress:
        progress(len(targets), len(targets), None)
    return result
