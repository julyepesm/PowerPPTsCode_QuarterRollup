"""Reusable Executive Summary rollup builder."""

import calendar
import datetime

import pandas as pd
import streamlit as st

from main_slide_generator import SlideGenerationOrchestrator
from rollup_builder import build_targets, generate_rollup_batch, load_catalog, normalize_period, period_label, quarter_period
import settings


def get_generator():
    if 'rollup_generator' not in st.session_state:
        st.session_state.rollup_generator = SlideGenerationOrchestrator()
    st.session_state.rollup_generator.powerbi.on_device_code = show_sign_in
    return st.session_state.rollup_generator


def show_sign_in(url, code):
    st.info('Sign in to Microsoft in another tab, enter this code, and complete the prompts. This page will continue automatically.')
    st.link_button('Open Microsoft sign-in', url)
    st.code(code, language=None)


def select_markets(ids):
    st.session_state.rollup_markets = ids


st.set_page_config(page_title='Executive Summary Rollup', layout='centered')
st.title('Executive Summary Rollup')
st.write('Choose a reporting period, brand, region, and markets to generate your decks.')

today = datetime.date.today()
previous_month = today.replace(day=1) - datetime.timedelta(days=1)
start_index = previous_month.year * 12 + previous_month.month - 3
default_start = datetime.date(start_index // 12, start_index % 12 + 1, 1)
mode = st.selectbox('Reporting period', ['Month range', 'Quarter'], key='rollup_period_mode')
years = list(range(2000, max(today.year + 6, 2031)))

if mode == 'Quarter':
    year_col, quarter_col = st.columns(2)
    with year_col:
        year = st.selectbox('Year', years, index=years.index(previous_month.year), key='rollup_quarter_year')
    with quarter_col:
        quarter = st.selectbox('Quarter', [1, 2, 3, 4], index=(previous_month.month - 1) // 3,
                               format_func=lambda q: f'Q{q}', key='rollup_quarter')
    start, end = quarter_period(year, quarter)
else:
    start_col, end_col = st.columns(2)
    with start_col:
        start_year = st.selectbox('Start year', years, index=years.index(default_start.year), key='rollup_start_year')
        start_month = st.selectbox('Start month', list(range(1, 13)), index=default_start.month - 1,
                                   format_func=lambda m: calendar.month_name[m], key='rollup_start_month')
    with end_col:
        end_year = st.selectbox('End year', years, index=years.index(previous_month.year), key='rollup_end_year')
        end_month = st.selectbox('End month', list(range(1, 13)), index=previous_month.month - 1,
                                 format_func=lambda m: calendar.month_name[m], key='rollup_end_month')
    start, end = f'{start_year:04d}-{start_month:02d}-01', f'{end_year:04d}-{end_month:02d}-01'

try:
    start, end = normalize_period(start, end)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

st.caption(f'Executive Summary: {period_label(start, end)}. '
           f'YTD: {period_label(end[:4] + "-01-01", end)}.')
if datetime.date.fromisoformat(end) >= today.replace(day=1):
    st.info('This period includes the current month or future months. Data may be incomplete.')

brand_col, tier_col = st.columns(2)
with brand_col:
    brand = st.selectbox('Brand', settings.GM_BRANDS, key='rollup_brand')
with tier_col:
    tier = st.selectbox('Tier', ['LMA', 'ZONE'], key='rollup_tier')

signature = (brand, tier, start, end)
st.caption('Load markets reads existing Power BI data. If sign-in is needed, a Microsoft link and code will appear here.')
if st.button('Load markets', key='rollup_load'):
    try:
        with st.spinner('Loading markets for the selected period...'):
            catalog = load_catalog(get_generator(), brand, tier, start, end)
        st.session_state.rollup_catalog = catalog
        st.session_state.rollup_catalog_signature = signature
        st.session_state.rollup_markets = []
        st.session_state.pop('rollup_selection_scope', None)
        st.session_state.pop('rollup_region', None)
    except Exception as exc:
        st.session_state.pop('rollup_catalog_signature', None)
        st.error(str(exc))

if st.session_state.get('rollup_catalog_signature') != signature:
    st.info('Load markets for these selections to choose a region and markets.')
    st.stop()

catalog = st.session_state.rollup_catalog
if catalog.empty:
    st.warning('No markets were returned for this brand, tier, and period.')
    st.stop()

regions = sorted(catalog.Region.unique().tolist())
region = st.selectbox('Region', [None] + regions,
                      format_func=lambda value: 'All regions' if value is None else value or 'Unassigned region',
                      key='rollup_region')
targets, issues = build_targets(catalog, brand, tier, region)
if brand in ('Buick', 'GMC') and tier == 'LMA':
    st.caption('Buick XTPC is one combined deck. GMC XTPC-PANFL and XTPC-TALFL are separate decks.')
if issues:
    st.warning('Some source rows have incomplete market mappings and cannot be assigned to a deck. Review the details before generating.')
    with st.expander('Unresolved market mappings'):
        st.dataframe(pd.DataFrame(issues), hide_index=True)
if not targets:
    st.warning('No usable market scopes are available for this selection.')
    st.stop()

by_id = {target['id']: target for target in targets}
scope = signature + (region,)
if st.session_state.get('rollup_selection_scope') != scope:
    st.session_state.rollup_markets = []
    st.session_state.rollup_selection_scope = scope

all_col, clear_col = st.columns(2)
with all_col:
    st.button('Select all', on_click=select_markets, args=(list(by_id),), key='rollup_select_all')
with clear_col:
    st.button('Clear selection', on_click=select_markets, args=([],), key='rollup_clear')
selected = st.multiselect('Markets', list(by_id), format_func=lambda key: by_id[key]['label'], key='rollup_markets')
flatten = st.toggle('Flatten slides (non-editable version)', value=False, key='rollup_flatten')
st.write(f'{len(selected)} of {len(targets)} available decks selected.')

if st.button('Generate rollup decks', type='primary', disabled=not selected, key='rollup_generate'):
    try:
        progress_bar = st.progress(0, text='Starting report generation...')

        def update_progress(index, total, target):
            text = f"Generating {target['label']} ({index + 1}/{total})" if target else 'Batch finished'
            progress_bar.progress(index / total, text=text)

        result = generate_rollup_batch(
            get_generator(), [by_id[key] for key in selected], start, end,
            flatten_slides=flatten, progress=update_progress, catalog_issues=issues, period_mode=mode)
        st.session_state.rollup_result = result
        progress_bar.empty()
    except Exception as exc:
        st.error(f'Could not complete the batch: {exc}')

if 'rollup_result' in st.session_state:
    result = st.session_state.rollup_result
    st.subheader('Last generation result')
    st.caption(period_label(result['start_month'], result['end_month']))
    message = f"Generated {result['successful_decks']} of {result['expected_decks']} decks."
    if result['errors']:
        st.warning(message)
    else:
        st.success(message)
    st.write(f"Saved to: `{result['output_folder']}`")
    st.dataframe(pd.DataFrame(result['details']), hide_index=True)
