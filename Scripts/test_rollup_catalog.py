import unittest

import pandas as pd

from main_slide_generator import (
    BUICK_GMC_ROLLUP_MARKET_CODES,
    resolve_rollup_market_rows,
)


class RollupCatalogTests(unittest.TestCase):
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