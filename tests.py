
import unittest
from datetime import date

from engine import (
    calculate_eut_factor,
    calculate_test_hours,
    calculate_test_cost,
    calculate_quote_pricing
)

from processor import is_eligible_retest


class TestEMCTestLab(unittest.TestCase):

    # EUT factor tests
    def test_eut_factor_one(self):
        self.assertEqual(calculate_eut_factor(1), 1.0)

    def test_eut_factor_two(self):
        self.assertEqual(calculate_eut_factor(2), 1.5)

    def test_eut_factor_three(self):
        self.assertEqual(calculate_eut_factor(3), 1.5)

    def test_eut_factor_four(self):
        self.assertEqual(calculate_eut_factor(4), 2.0)

    def test_eut_factor_five(self):
        self.assertEqual(calculate_eut_factor(5), 2.0)

    # Test hours and cost
    def test_test_hours(self):
        self.assertEqual(calculate_test_hours(3.5, 2.0), 7.0)

    def test_test_cost(self):
        self.assertEqual(calculate_test_cost(5.0, 1000), 5000.0)

    # Bundle discount tests
    def test_bundle_discount_3_tests(self):
        result = calculate_quote_pricing(10000, 3)
        self.assertEqual(result["bundle_discount_rs"], 500)
        self.assertEqual(result["report_fee_rs"], 8000)

    def test_bundle_discount_5_tests(self):
        result = calculate_quote_pricing(10000, 5)
        self.assertEqual(result["bundle_discount_rs"], 1000)

    # Rush surcharge test
    def test_rush_surcharge(self):
        result = calculate_quote_pricing(10000, 1, rush=True)
        self.assertEqual(result["rush_surcharge_rs"], 4000)

    # Retest pricing test
    def test_retest_pricing(self):
        result = calculate_quote_pricing(
            10000, 1, is_retest=True
        )
        self.assertEqual(result["retest_discount_rs"], 5000)
        self.assertEqual(result["report_fee_rs"], 0)
        self.assertEqual(result["total_rs"], 5900)

    # Retest eligibility tests
    def test_retest_exactly_30_days(self):
        state = {
            "failed_tests": {
                ("QT-001", "T-06"): date(2026, 9, 9)
            }
        }

        result = is_eligible_retest(
            date(2026, 10, 9),
            "QT-001",
            "T-06",
            state
        )

        self.assertTrue(result)

    def test_retest_after_31_days(self):
        state = {
            "failed_tests": {
                ("QT-001", "T-06"): date(2026, 9, 9)
            }
        }

        result = is_eligible_retest(
            date(2026, 10, 10),
            "QT-001",
            "T-06",
            state
        )

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)

