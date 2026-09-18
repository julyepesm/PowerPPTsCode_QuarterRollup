import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from main_slide_generator import SlideGenerationOrchestrator


class VehicleSectionToggleTests(unittest.TestCase):
    def _build_orchestrator(self):
        orchestrator = SlideGenerationOrchestrator.__new__(SlideGenerationOrchestrator)
        orchestrator.flatten_slides = False
        orchestrator.authenticate = MagicMock(return_value=True)
        orchestrator.data_queries = MagicMock()
        orchestrator.powerbi = MagicMock()
        orchestrator.powerbi.execute_dax_query.return_value = pd.DataFrame()
        orchestrator._get_tactic_combinations = MagicMock(
            return_value=pd.DataFrame({"Combination": [1, 2, 3]})
        )
        orchestrator._sort_combinations = MagicMock(side_effect=lambda data: data)
        orchestrator._parse_month_year = MagicMock(
            return_value=("January 2026", 2026, 1, 1)
        )

        presentation = MagicMock()
        orchestrator._add_title_slide = MagicMock(return_value=(presentation, 1))
        orchestrator._add_executive_summary_slide = MagicMock(
            return_value=(presentation, 2)
        )
        orchestrator._add_tactic_slides = MagicMock(return_value=(presentation, 3))
        orchestrator._add_ytd_chart_slides = MagicMock(
            return_value=(presentation, 5)
        )
        orchestrator._add_vehicle_slides = MagicMock(
            return_value=(presentation, 7)
        )
        orchestrator.brand_configs = MagicMock()
        orchestrator.slide_templates = MagicMock()
        orchestrator._save_complete_deck = MagicMock(return_value="report.pptx")
        return orchestrator

    def test_vehicle_slides_are_skipped_when_section_is_disabled(self):
        orchestrator = self._build_orchestrator()

        with patch("main_slide_generator.add_glossary_to_deck"):
            result = orchestrator.generate_all_slides_for_market_month(
                brand="GMC",
                market_name="Test Market",
                month_year="2026-01-01T00:00:00",
                zone_lma_type="ZONE",
                output_folder=".",
                market_code="TEST",
                include_vehicle_slides=False,
            )

        orchestrator._add_vehicle_slides.assert_not_called()
        self.assertEqual(result["slides_created"], 6)

    def test_vehicle_slides_remain_enabled_by_default(self):
        orchestrator = self._build_orchestrator()

        with patch("main_slide_generator.add_glossary_to_deck"):
            orchestrator.generate_all_slides_for_market_month(
                brand="GMC",
                market_name="Test Market",
                month_year="2026-01-01T00:00:00",
                zone_lma_type="ZONE",
                output_folder=".",
                market_code="TEST",
            )

        orchestrator._add_vehicle_slides.assert_called_once()


if __name__ == "__main__":
    unittest.main()
