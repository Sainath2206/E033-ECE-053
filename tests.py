
import unittest

from engine import (
    calculate_eut_factor,
    calculate_test_hours,
    calculate_test_cost
)


class TestEMCTestLab(unittest.TestCase):

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

    def test_test_hours(self):
        self.assertEqual(calculate_test_hours(3.5, 2.0), 7.0)

    def test_test_cost(self):
        self.assertEqual(calculate_test_cost(5.0, 1000), 5000.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
