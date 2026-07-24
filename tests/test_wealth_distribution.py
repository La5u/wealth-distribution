import sys
import unittest
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wealth_distribution import load_paired_2024_wealth, load_rows, log_correlation, percentage


class WealthDistributionTest(unittest.TestCase):
    def test_exact_decade_bands(self):
        rows = load_rows()
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row["upper_usd"] / row["lower_usd"] == 10 for row in rows))

    def test_wir_middle_bands(self):
        rows = {row["label"]: row for row in load_rows()}
        self.assertEqual(rows["$1m–$10m"]["count"], 60_319_510)
        self.assertEqual(rows["$10m–$100m"]["count"], 1_769_200)
        self.assertEqual(rows["$100m–$1b"]["count"], 73_710)

    def test_log_correlation(self):
        self.assertAlmostEqual(log_correlation(load_rows()), -0.994993, places=6)

    def test_tiny_percentages_are_not_scientific_notation(self):
        self.assertEqual(percentage(0.000000007), "0.000000007%")

    def test_2024_reported_threshold_subtractions(self):
        rows = {row["label"]: row for row in load_rows(2024)}
        self.assertEqual(rows["$1m–$10m"]["count"], 60_000_000 - 2_341_378)
        self.assertEqual(rows["$10m–$100m"]["count"], 2_341_378 - 104_060)
        self.assertEqual(rows["$100m–$1b"]["count"], 104_060 - 2_781)
        self.assertEqual(sum(rows[label]["count"] for label in ("$1b–$10b", "$10b–$100b", "$100b–$1t")), 2_781)
        self.assertEqual(sum(row["count"] for row in rows.values()) + 1_550_000_000, 3_808_000_000)

    def test_paired_shares_preserve_credit_suisse_totals(self):
        path = Path(__file__).resolve().parents[1] / "data" / "paired_shares_2021.csv"
        with path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 9)
        self.assertAlmostEqual(sum(float(row["adult_share_pct"]) for row in rows), 100, places=9)
        self.assertAlmostEqual(sum(float(row["reconciled_count"]) for row in rows), 5_298_500_000, places=0)
        self.assertAlmostEqual(sum(float(row["wealth_share_pct"]) for row in rows), 100, places=9)
        self.assertAlmostEqual(sum(float(row["total_wealth_bn"]) for row in rows), 463_600, places=6)

    def test_2024_paired_wealth_reconciles(self):
        rows = {row["label"]: row for row in load_paired_2024_wealth()}
        self.assertAlmostEqual(rows["$1m–$10m"]["total_wealth_bn"], 135_890.917337, places=6)
        self.assertAlmostEqual(rows["$10m–$100m"]["total_wealth_bn"], 53_815.785116, places=6)
        self.assertAlmostEqual(rows["$100m–$1b"]["total_wealth_bn"], 22_553.697547, places=6)
        self.assertEqual([row["span"] for row in rows.values()], [1] * 9)
        self.assertAlmostEqual(sum(row["total_wealth_bn"] for row in rows.values()), 470_510, places=6)
        self.assertAlmostEqual(sum(row["wealth_share_pct"] for row in rows.values()), 100, places=9)


if __name__ == "__main__":
    unittest.main()
