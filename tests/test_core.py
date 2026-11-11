"""Tests for tiny_fixed_point_decimal.core."""

import unittest

from tiny_fixed_point_decimal import (
    FixedDecimal,
    InvalidOperation,
    DivisionByZero,
)


class TestConstruction(unittest.TestCase):
    def test_scaled_and_places(self):
        d = FixedDecimal(12345, 2)
        self.assertEqual(d.scaled, 12345)
        self.assertEqual(d.places, 2)

    def test_rejects_bool_as_int(self):
        with self.assertRaises(TypeError):
            FixedDecimal(True, 2)
        with self.assertRaises(TypeError):
            FixedDecimal(1, False)

    def test_rejects_non_int(self):
        with self.assertRaises(TypeError):
            FixedDecimal("1", 2)
        with self.assertRaises(TypeError):
            FixedDecimal(1, "2")

    def test_rejects_negative_places(self):
        with self.assertRaises(ValueError):
            FixedDecimal(1, -1)

    def test_zero(self):
        z = FixedDecimal.zero(3)
        self.assertEqual(z.scaled, 0)
        self.assertEqual(z.places, 3)


class TestFromString(unittest.TestCase):
    def test_simple(self):
        d = FixedDecimal.from_string("12.34", 2)
        self.assertEqual(d.scaled, 1234)
        self.assertEqual(d.places, 2)

    def test_padding(self):
        d = FixedDecimal.from_string("1.5", 3)
        self.assertEqual(d.scaled, 1500)

    def test_extra_zeros_allowed(self):
        d = FixedDecimal.from_string("1.500", 2)
        self.assertEqual(d.scaled, 150)

    def test_extra_nonzero_rejected(self):
        with self.assertRaises(InvalidOperation):
            FixedDecimal.from_string("1.501", 2)

    def test_signs(self):
        self.assertEqual(FixedDecimal.from_string("+1.2", 1).scaled, 12)
        self.assertEqual(FixedDecimal.from_string("-1.2", 1).scaled, -12)

    def test_no_integer_part(self):
        self.assertEqual(FixedDecimal.from_string(".5", 1).scaled, 5)

    def test_no_fractional_part(self):
        self.assertEqual(FixedDecimal.from_string("7.", 2).scaled, 700)

    def test_no_dot(self):
        self.assertEqual(FixedDecimal.from_string("7", 2).scaled, 700)

    def test_invalid_characters(self):
        for bad in ["1a", "1.2.3", "", ".", "+", "-", "1e3", " 1"]:
            with self.assertRaises(InvalidOperation, msg=bad):
                FixedDecimal.from_string(bad, 2)

    def test_type_errors(self):
        with self.assertRaises(TypeError):
            FixedDecimal.from_string(12, 2)
        with self.assertRaises(TypeError):
            FixedDecimal.from_string("12", "2")


class TestArithmetic(unittest.TestCase):
    def test_add(self):
        a = FixedDecimal.from_string("1.25", 2)
        b = FixedDecimal.from_string("2.75", 2)
        self.assertEqual((a + b).scaled, 400)

    def test_sub(self):
        a = FixedDecimal.from_string("5.00", 2)
        b = FixedDecimal.from_string("2.50", 2)
        self.assertEqual((a - b).scaled, 250)

    def test_mul_truncates(self):
        a = FixedDecimal.from_string("1.11", 2)
        b = FixedDecimal.from_string("1.11", 2)
        # 1.2321 -> 1.23
        self.assertEqual((a * b).scaled, 123)

    def test_mul_negative_truncates_toward_zero(self):
        a = FixedDecimal.from_string("-1.11", 2)
        b = FixedDecimal.from_string("1.11", 2)
        self.assertEqual((a * b).scaled, -123)

    def test_div_truncates(self):
        a = FixedDecimal.from_string("1.00", 2)
        b = FixedDecimal.from_string("3.00", 2)
        # 0.333... -> 0.33
        self.assertEqual((a / b).scaled, 33)

    def test_div_negative_truncates_toward_zero(self):
        a = FixedDecimal.from_string("-1.00", 2)
        b = FixedDecimal.from_string("3.00", 2)
        self.assertEqual((a / b).scaled, -33)

    def test_div_by_zero(self):
        a = FixedDecimal.from_string("1.00", 2)
        b = FixedDecimal.from_string("0.00", 2)
        with self.assertRaises(DivisionByZero):
            a / b

    def test_places_mismatch(self):
        a = FixedDecimal.from_string("1.0", 1)
        b = FixedDecimal.from_string("1.00", 2)
        for op in ("__add__", "__sub__", "__mul__", "__truediv__"):
            with self.assertRaises(InvalidOperation):
                getattr(a, op)(b)

    def test_type_error_for_non_fixed(self):
        a = FixedDecimal.from_string("1.0", 1)
        with self.assertRaises(TypeError):
            a + 1

    def test_neg_and_abs(self):
        a = FixedDecimal.from_string("-1.25", 2)
        self.assertEqual((-a).scaled, 125)
        self.assertEqual(abs(a).scaled, 125)


class TestComparison(unittest.TestCase):
    def test_ordering(self):
        a = FixedDecimal.from_string("1.00", 2)
        b = FixedDecimal.from_string("2.00", 2)
        self.assertTrue(a < b)
        self.assertTrue(a <= b)
        self.assertTrue(b > a)
        self.assertTrue(b >= a)
        self.assertTrue(a <= FixedDecimal.from_string("1.00", 2))

    def test_equality(self):
        a = FixedDecimal.from_string("1.00", 2)
        b = FixedDecimal.from_string("1.00", 2)
        c = FixedDecimal.from_string("1.0", 1)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertNotEqual(a, "1.00")

    def test_hash(self):
        a = FixedDecimal.from_string("1.00", 2)
        b = FixedDecimal.from_string("1.00", 2)
        self.assertEqual(hash(a), hash(b))

    def test_ordering_places_mismatch(self):
        a = FixedDecimal.from_string("1.0", 1)
        b = FixedDecimal.from_string("1.00", 2)
        with self.assertRaises(InvalidOperation):
            a < b


class TestString(unittest.TestCase):
    def test_str_positive(self):
        self.assertEqual(str(FixedDecimal.from_string("12.34", 2)), "12.34")

    def test_str_negative(self):
        self.assertEqual(str(FixedDecimal.from_string("-0.05", 2)), "-0.05")

    def test_str_zero_places(self):
        self.assertEqual(str(FixedDecimal(42, 0)), "42")

    def test_str_padding(self):
        self.assertEqual(str(FixedDecimal(5, 2)), "0.05")

    def test_repr(self):
        self.assertEqual(repr(FixedDecimal(123, 2)), "FixedDecimal(123, 2)")


if __name__ == "__main__":
    unittest.main()
