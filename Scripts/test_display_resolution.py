import unittest

from display_resolution import resolve_display_tactic
from main_slide_generator import SlideGenerationOrchestrator


class DisplayResolutionTests(unittest.TestCase):
    def test_detroit_tigers_is_not_treated_as_instagram(self):
        self.assertEqual(
            resolve_display_tactic('FEP', 'BT/InMarket', 'DetroitTigers'),
            'FEP',
        )

    def test_instagram_alias_still_resolves_to_meta(self):
        for site in ('IG', 'IG Ads', 'Media - IG', 'FB/IG'):
            with self.subTest(site=site):
                self.assertEqual(
                    resolve_display_tactic('Display', 'BT/InMarket', site),
                    'Meta Display',
                )

    def test_named_social_platform_still_resolves_to_meta(self):
        self.assertEqual(
            resolve_display_tactic('Display', 'BT/InMarket', 'Instagram Ads'),
            'Meta Display',
        )

    def test_compound_words_do_not_resolve_to_meta(self):
        for site in ('DetroitTigers', 'FBinvestors', 'MetaInvestors'):
            with self.subTest(site=site):
                self.assertEqual(
                    resolve_display_tactic('FEP', 'BT/InMarket', site),
                    'FEP',
                )

    def test_historical_site_aliases_require_independent_words(self):
        match = SlideGenerationOrchestrator._is_broad_site_match

        for actual, target in (
            ('Meta', 'Facebook Ads'),
            ('IG', 'Media - IG'),
            ('FB/IG', 'Instagram Ads'),
        ):
            with self.subTest(actual=actual, target=target):
                self.assertTrue(match(None, actual, target, 'Meta Display'))

        for actual, target in (
            ('DetroitTigers', 'IG'),
            ('FBinvestors', 'FB'),
            ('MetaInvestors', 'Meta'),
        ):
            with self.subTest(actual=actual, target=target):
                self.assertFalse(match(None, actual, target, 'Meta Display'))


if __name__ == '__main__':
    unittest.main()
