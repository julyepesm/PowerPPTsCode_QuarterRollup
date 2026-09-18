import unittest
from unittest.mock import MagicMock, patch
import tempfile

import pandas as pd

from main_slide_generator import (
    BUICK_GMC_ROLLUP_MARKET_CODES,
    resolve_rollup_market_rows,
    process_buick_gmc_quarter_rollup,
    SlideGenerationOrchestrator,
    get_rollup_targets,
)
from data_queries import DataQueries


class RollupCatalogTests(unittest.TestCase):
    def test_gmc_xtpc_is_split_while_buick_remains_combined(self):
        targets = get_rollup_targets()
        self.assertEqual(len(targets), 23)
        self.assertEqual([t['market_code'] for t in targets if t['client_code'] == 'XTPC'],
                         [None, 'PANFL', 'TALFL'])
        catalog = pd.DataFrame([
            {'Brand': brand, 'MarketCode': dma, 'ClientCode': 'XTPC',
             'MarketName': 'Source name', 'ZoneLMA': 'LMA'}
            for brand in ('Buick', 'GMC') for dma in ('PANFL', 'TALFL', None)
        ])
        with tempfile.TemporaryDirectory() as folder, patch('main_slide_generator.SlideGenerationOrchestrator') as cls:
            generator = cls.return_value
            from utils import find_column
            generator._find_column.side_effect = find_column
            generator.powerbi.execute_dax_query.return_value = catalog
            generator.generate_quarter_rollup_for_market.return_value = {'filepath': 'test.pptx'}
            result = process_buick_gmc_quarter_rollup(output_folder=folder)
            calls = [c.kwargs for c in generator.generate_quarter_rollup_for_market.call_args_list]
        self.assertEqual([(c['brand'], c['client_code'], c['market_code']) for c in calls],
                         [('Buick', 'XTPC', None), ('GMC', 'XTPC', 'PANFL'), ('GMC', 'XTPC', 'TALFL')])
        self.assertEqual(result['successful_decks'], 3)
        for call in calls[1:]:
            self.assertTrue(call['file_prefix'].startswith('XTPC-' + call['market_code']))
            for builder in (DataQueries().get_executive_summary_query,
                            DataQueries().get_ytd_kba_by_tactic_query,
                            DataQueries().get_ytd_impressions_by_vehicle_query):
                query = builder('GMC', None, '2026-08-01', client_code='XTPC', market_code=call['market_code'])
                self.assertIn('[Client Code] = "XTPC"', query)
                self.assertIn(f'[Market Code] = "{call["market_code"]}"', query)

    def test_rollup_uses_period_summary_but_full_year_to_date_charts(self):
        generator = SlideGenerationOrchestrator.__new__(SlideGenerationOrchestrator)
        generator.flatten_slides = False
        generator.authenticate = MagicMock(return_value=True)
        generator._get_tactic_combinations = MagicMock(return_value=pd.DataFrame({'Tactic': ['FEP']}))
        prs = MagicMock()
        generator._add_title_slide = MagicMock(return_value=(prs, 1))
        generator._add_executive_summary_slide = MagicMock(return_value=(prs, 2))
        generator._add_ytd_chart_slides = MagicMock(return_value=(prs, 4))
        generator.brand_configs = MagicMock()
        generator.slide_templates = MagicMock()
        generator._save_complete_deck = MagicMock(return_value='test.pptx')
        with tempfile.TemporaryDirectory() as folder, patch('main_slide_generator.add_glossary_to_deck'):
            generator.generate_quarter_rollup_for_market(
                'Buick', None, '2026-06-01', '2026-08-01', zone_lma_type='LMA',
                output_folder=folder, client_code='XTPC', display_market_name='Combined')
        summary = generator._add_executive_summary_slide.call_args
        self.assertEqual(summary.args[3], 'June-August 2026')
        self.assertEqual(summary.kwargs['start_month_year'], '2026-06-01')
        ytd = generator._add_ytd_chart_slides.call_args
        self.assertEqual(ytd.args[3], 'January-August 2026')
        self.assertIsNone(ytd.kwargs['rolling_months'])
        self.assertFalse(ytd.kwargs['apply_filters'])
        for query_builder in (DataQueries().get_ytd_kba_by_tactic_query, DataQueries().get_ytd_impressions_by_vehicle_query):
            query = query_builder('Buick', None, '2026-08-01', client_code='XTPC', months=None)
            self.assertIn('1, 1)', query)
            self.assertNotIn('EDATE', query)

    def test_rollup_ytd_keeps_low_volume_january_and_excludes_other_years(self):
        generator = SlideGenerationOrchestrator.__new__(SlideGenerationOrchestrator)
        raw = pd.DataFrame({
            'Date': ['2025-12-01', '2026-01-01', '2026-08-01', '2026-09-01'],
            'Tactic': ['FEP'] * 4, 'KBA': [500, 1, 200, 500], 'Total Cost': [100, 1, 100, 100],
        })
        result = generator._process_ytd_data(raw, 'Date', 'Tactic', 'KBA', 'Tactic',
                                              limit_year=2026, limit_month=8, apply_filters=False)
        self.assertEqual(result['Month'].tolist(), ['January', 'August'])
        self.assertEqual(result['FEP'].sum(), 201)

    def test_client_code_keeps_both_dma_rows_and_missing_metadata(self):
        catalog = pd.DataFrame([
            {'Brand': 'Buick', 'MarketCode': 'TALFL', 'ClientCode': 'XTPC'},
            {'Brand': 'Buick', 'MarketCode': 'PANFL', 'ClientCode': 'XTPC'},
            {'Brand': 'Buick', 'MarketCode': None, 'ClientCode': 'XTPC'},
            {'Brand': 'Buick', 'MarketCode': 'TALFL', 'ClientCode': 'OTHER'},
            {'Brand': 'GMC', 'MarketCode': 'TALFL', 'ClientCode': 'XTPC'},
        ])
        matches = resolve_rollup_market_rows(catalog, 'Brand', 'MarketCode', 'ClientCode')
        self.assertEqual([(b, c, len(rows)) for b, c, rows in matches],
                         [('Buick', 'XTPC', 3), ('GMC', 'XTPC', 1)])

    def test_rollup_query_scopes_client_without_dma_or_name_filter(self):
        query = DataQueries().get_executive_summary_query(
            'Buick', None, client_code='XTPC', zone_lma='LMA',
            start_month_year='2026-06-01', end_month_year='2026-08-01')
        self.assertIn('[Client Code] = "XTPC"', query)
        self.assertNotIn('[Market Code] =', query)
        self.assertNotIn('[Market Name] =', query)
        self.assertIn('>= DATEVALUE("2026-06-01")', query)
        self.assertIn('<= DATEVALUE("2026-08-01")', query)

    def test_batch_reports_missing_pairs_and_continues_after_failure(self):
        catalog = pd.DataFrame([
            {'[Brand]': brand, '[MarketCode]': dma, '[ClientCode]': code,
             '[MarketName]': 'Source name', '[ZoneLMA]': 'LMA'}
            for brand, dma, code in [('Buick', 'ALBGA', 'XALY'), ('GMC', 'ATLGA', 'XATL')]
        ])
        with tempfile.TemporaryDirectory() as folder, patch('main_slide_generator.SlideGenerationOrchestrator') as cls:
            generator = cls.return_value
            from utils import find_column
            generator._find_column.side_effect = find_column
            generator.powerbi.execute_dax_query.return_value = catalog
            generator.generate_quarter_rollup_for_market.side_effect = [RuntimeError('failed slide'), {'filepath': 'test.pptx'}]
            result = process_buick_gmc_quarter_rollup(output_folder=folder)
            self.assertEqual(result['successful_decks'], 1)
            self.assertEqual(result['errors'], 22)
            self.assertEqual(len(result['details']), 23)
            call = generator.generate_quarter_rollup_for_market.call_args.kwargs
            self.assertEqual(call['client_code'], 'XATL')
            self.assertIsNone(call['market_name'])
            self.assertIsNone(call['market_code'])

    def test_ytd_helpers_return_slides_not_tuples(self):
        generator = SlideGenerationOrchestrator.__new__(SlideGenerationOrchestrator)
        generator.powerbi = MagicMock()
        generator.powerbi.execute_dax_query.return_value = pd.DataFrame({'value': [1]})
        generator.data_queries = DataQueries()
        generator.brand_configs = MagicMock()
        generator.slide_templates = MagicMock()
        generator._process_ytd_data = MagicMock(return_value=pd.DataFrame({'Month': ['June']}))
        prs = object()
        with patch('ytd_charts_refactored.create_ytd_kba_slide', return_value=object()), patch('ytd_charts_refactored.create_ytd_impressions_slide', return_value=object()):
            result, count = generator._add_ytd_chart_slides(
                'Buick', None, '2026-08-01', 'June-August 2026', 2026, 8, 1,
                'LMA', prs, 2, client_code='XTPC', display_market_name='Combined', rolling_months=3)
        self.assertIs(result, prs)
        self.assertEqual(count, 4)

    def test_matches_compound_codes_for_both_brands(self):
        rows = []
        for brand in ("Buick", "GMC"):
            for index, code in enumerate(BUICK_GMC_ROLLUP_MARKET_CODES):
                rows.append({
                    "Brand": brand,
                    "MarketCode": f"{code}-{brand[:2].upper()}{index:02d}",
                    "MarketName": f"{code} test market",
                })

        catalog = pd.DataFrame(rows)
        matches = resolve_rollup_market_rows(catalog, "Brand", "MarketCode")

        print(f"ROLLUP TEST MATCHES: {len(matches)}")
        for brand, requested_code, market_rows in matches:
            print(f"  {brand} {requested_code}: {market_rows['MarketCode'].tolist()}")

        self.assertEqual(len(matches), 22)
        self.assertEqual(
            {(brand, code) for brand, code, _ in matches},
            {(brand, code) for brand in ("Buick", "GMC") for code in BUICK_GMC_ROLLUP_MARKET_CODES},
        )


if __name__ == "__main__":
    unittest.main()
