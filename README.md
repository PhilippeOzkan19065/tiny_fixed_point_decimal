# tiny_fixed_point_decimal

Exact decimal arithmetic with a fixed number of fractional digits, stored as a
plain Python integer so you avoid the overhead of `decimal.Decimal`.

## Usage

```python
from tiny_fixed_point_decimal import FixedDecimal, DivisionByZero, InvalidOperation

price = FixedDecimal.from_string("12.34", 2)   # 1234 scaled by 100
qty   = FixedDecimal.from_string("3", 2)       # 300 scaled by 100
total = price * qty                            # 37.02
print(total)                                   # 37.02

# Division truncates toward zero.
third = FixedDecimal.from_string("1.00", 2) / FixedDecimal.from_string("3.00", 2)
print(third)                                   # 0.33

# Mixing places is an error; both operands must agree.
try:
    price + FixedDecimal.from_string("1.0", 1)
except InvalidOperation as exc:
    print(exc)                                 # places mismatch: 2 != 1

try:
    price / FixedDecimal.zero(2)
except DivisionByZero:
    print("cannot divide by zero")
```

## Why this exists

`decimal.Decimal` carries a context, rounding modes, and arbitrary precision
machinery that you pay for even when you only need two decimal places for money.
This library stores the value as `scaled = value * 10**places` in a Python `int`,
which is exact, small, and fast for the sizes that appear in prices and
quantities. The trade-off is deliberate: there is no rounding mode and no
context. Division truncates toward zero, multiplication truncates the extra
fractional digits, and every operation requires both operands to share the same
number of places. If you need rounding or mixed scales, this is not the library
for you.

## The awkward edge

`FixedDecimal` does not compare equal to a `FixedDecimal` with a different
number of places, even if the real values are the same: `FixedDecimal(100, 2)`
and `FixedDecimal(10, 1)` are both `1.0` but are not equal, and ordering them
raises `InvalidOperation`. You must normalise places yourself before comparing
or combining values from different sources.
