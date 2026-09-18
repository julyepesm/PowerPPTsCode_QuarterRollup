import unittest

import pandas as pd

from error_collector import ErrorCollector
from filters_manager import GeneralFiltersConfig
from main_slide_generator import SlideGenerationOrchestrator


class YtdSpendFilterTests(unittest.TestCase):
    def setUp(self):
        self.original_spend = GeneralFiltersConfig.min_tactic_spend
        self.original_ytd_enabled = GeneralFiltersConfig.ytd_filter_enabled
        GeneralFiltersConfig.ytd_filter_enabled = False
        ErrorCollector().clear()
        self.orchestrator = SlideGenerationOrchestrator.__new__(
            SlideGenerationOrchestrator
        )

    def tearDown(self):
        GeneralFiltersConfig.min_tactic_spend = self.original_spend
        GeneralFiltersConfig.ytd_filter_enabled = self.original_ytd_enabled

    def test_kba_excludes_entire_month_below_configured_spend(self):
        GeneralFiltersConfig.min_tactic_spend = 75
        raw = pd.DataFrame([
            {
                'Master Date Table[Month Year]': '2026-06-01',
                'PoP Master Table[Tactic (Reporting)]': 'FEP',
                '[KBA]': 100,
                '[Total Cost]': 30,
            },
            {
                'Master Date Table[Month Year]': '2026-06-01',
                'PoP Master Table[Tactic (Reporting)]': 'Display',
                '[KBA]': 200,
                '[Total Cost]': 44.99,
            },
            {
                'Master Date Table[Month Year]': '2026-07-01',
                'PoP Master Table[Tactic (Reporting)]': 'Display',
                '[KBA]': 300,
                '[Total Cost]': 75,
            },
        ])

        result = self.orchestrator._process_ytd_data(
            raw,
            date_col='Master Date Table[Month Year]',
            category_col='PoP Master Table[Tactic (Reporting)]',
            value_col='[KBA]',
            category_rename='Tactic',
            limit_year=2026,
            limit_month=7,
            error_context={
                'brand': 'GMC', 'market': 'Test Market',
                'report': 'YTD Spend'
            },
        )

        self.assertEqual(result['Month'].astype(str).tolist(), ['July'])
        self.assertEqual(result['Display'].iloc[0], 300)
        errors = ErrorCollector().get_errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['month'], 'June 2026')
        self.assertAlmostEqual(errors[0]['value'], 74.99, places=2)

    def test_impressions_uses_runtime_threshold_and_deduplicates_error(self):
        GeneralFiltersConfig.min_tactic_spend = 100
        raw = pd.DataFrame([
            {
                'Master Date Table[Month Year]': '2026-06-01',
                'PoP Master Table[Vehicle]': 'Vehicle A',
                '[Impressions]': 1000,
                '[Total Cost]': 99.99,
            },
            {
                'Master Date Table[Month Year]': '2026-07-01',
                'PoP Master Table[Vehicle]': 'Vehicle B',
                '[Impressions]': 2000,
                '[Total Cost]': 100,
            },
        ])

        result = self.orchestrator._process_ytd_data(
            raw,
            date_col='Master Date Table[Month Year]',
            category_col='PoP Master Table[Vehicle]',
            value_col='[Impressions]',
            category_rename='Vehicle',
            limit_year=2026,
            limit_month=7,
            error_context={
                'brand': 'GMC', 'market': 'Test Market',
                'report': 'YTD Spend'
            },
        )

        self.assertNotIn('Vehicle A', result.columns)
        self.assertEqual(result['Vehicle B'].iloc[0], 2000)

        self.orchestrator._process_ytd_data(
            raw,
            date_col='Master Date Table[Month Year]',
            category_col='PoP Master Table[Vehicle]',
            value_col='[Impressions]',
            category_rename='Vehicle',
            limit_year=2026,
            limit_month=7,
            error_context={
                'brand': 'GMC', 'market': 'Test Market',
                'report': 'YTD Spend'
            },
        )
        self.assertEqual(len(ErrorCollector().get_errors()), 1)


if __name__ == '__main__':
    unittest.main()
