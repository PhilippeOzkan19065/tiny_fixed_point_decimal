"""Core implementation of fixed-point decimal arithmetic.

The design goal is to avoid the overhead of the standard library's
``decimal.Decimal`` while still providing exact decimal arithmetic for a
small, fixed number of fractional digits.  A value is stored as an integer
``scaled`` equal to the real value multiplied by ``10**places``.  All
arithmetic is performed on Python integers, which are exact and fast for the
sizes involved.

Only addition, subtraction, multiplication, and division are supported.
Division truncates toward zero and raises :class:`DivisionByZero` when the
divisor is zero.  There is no rounding mode, no context, and no arbitrary
precision: the number of fractional digits is fixed at construction time.
"""

from __future__ import annotations

__all__ = ["FixedDecimal", "InvalidOperation", "DivisionByZero"]


class InvalidOperation(ValueError):
    """Raised when an operation is not defined for the given operands."""


class DivisionByZero(ZeroDivisionError):
    """Raised when dividing by a zero FixedDecimal."""


class FixedDecimal:
    """A decimal number with a fixed number of fractional digits.

    The value is stored as an integer ``scaled`` such that the represented
    real number is ``scaled / 10**places``.  ``places`` is fixed for the
    lifetime of the object; arithmetic between two ``FixedDecimal`` instances
    requires equal ``places`` and raises :class:`InvalidOperation` otherwise.
    """

    __slots__ = ("_scaled", "_places")

    def __init__(self, scaled: int, places: int) -> None:
        """Create a value from an already-scaled integer.

        ``scaled`` must be an ``int`` and ``places`` must be a non-negative
        ``int``.  No other types are accepted so that the caller is explicit
        about the scaling.
        """
        if not isinstance(scaled, int) or isinstance(scaled, bool):
            raise TypeError("scaled must be an int")
        if not isinstance(places, int) or isinstance(places, bool):
            raise TypeError("places must be an int")
        if places < 0:
            raise ValueError("places must be non-negative")
        self._scaled = scaled
        self._places = places

    @classmethod
    def from_string(cls, text: str, places: int) -> "FixedDecimal":
        """Parse a decimal string into a value with exactly ``places`` digits.

        The string may have an optional sign, an integer part, and a
        fractional part.  It must not contain exponents or whitespace.  More
        fractional digits than ``places`` are allowed only if the extra digits
        are zeros; otherwise :class:`InvalidOperation` is raised.  Fewer
        fractional digits are padded with zeros.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a str")
        if not isinstance(places, int) or isinstance(places, bool):
            raise TypeError("places must be an int")
        if places < 0:
            raise ValueError("places must be non-negative")

        s = text
        sign = 1
        if s.startswith("+"):
            s = s[1:]
        elif s.startswith("-"):
            sign = -1
            s = s[1:]

        if s == "":
            raise InvalidOperation("empty numeric string")

        if "." in s:
            int_part, frac_part = s.split(".", 1)
        else:
            int_part, frac_part = s, ""

        if int_part == "" and frac_part == "":
            raise InvalidOperation("no digits in numeric string")
        if int_part == "":
            int_part = "0"

        for ch in int_part:
            if ch < "0" or ch > "9":
                raise InvalidOperation(f"invalid character {ch!r} in numeric string")
        for ch in frac_part:
            if ch < "0" or ch > "9":
                raise InvalidOperation(f"invalid character {ch!r} in numeric string")

        if len(frac_part) > places:
            extra = frac_part[places:]
            if any(ch != "0" for ch in extra):
                raise InvalidOperation(
                    "more fractional digits than places and not all zeros"
                )
            frac_part = frac_part[:places]
        else:
            frac_part = frac_part + "0" * (places - len(frac_part))

        digits = int_part + frac_part
        scaled = sign * int(digits)
        return cls(scaled, places)

    @classmethod
    def zero(cls, places: int) -> "FixedDecimal":
        """Return the value zero with the given number of places."""
        return cls(0, places)

    @property
    def places(self) -> int:
        """Number of digits after the decimal point."""
        return self._places

    @property
    def scaled(self) -> int:
        """The underlying integer value (real value times 10**places)."""
        return self._scaled

    def _check_same_places(self, other: "FixedDecimal") -> None:
        if not isinstance(other, FixedDecimal):
            raise TypeError("operand must be a FixedDecimal")
        if self._places != other._places:
            raise InvalidOperation(
                f"places mismatch: {self._places} != {other._places}"
            )

    def __add__(self, other: "FixedDecimal") -> "FixedDecimal":
        self._check_same_places(other)
        return FixedDecimal(self._scaled + other._scaled, self._places)

    def __sub__(self, other: "FixedDecimal") -> "FixedDecimal":
        self._check_same_places(other)
        return FixedDecimal(self._scaled - other._scaled, self._places)

    def __mul__(self, other: "FixedDecimal") -> "FixedDecimal":
        self._check_same_places(other)
        product = self._scaled * other._scaled
        # The product has 2*places fractional digits; divide by 10**places
        # truncating toward zero to bring it back to `places` digits.
        scale = 10 ** self._places
        if product >= 0:
            scaled = product // scale
        else:
            scaled = -((-product) // scale)
        return FixedDecimal(scaled, self._places)

    def __truediv__(self, other: "FixedDecimal") -> "FixedDecimal":
        self._check_same_places(other)
        if other._scaled == 0:
            raise DivisionByZero("division by zero")
        # (a / 10^p) / (b / 10^p) = a / b, so we only need a / b with
        # `places` fractional digits: (a * 10^p) // b, truncating toward zero.
        scale = 10 ** self._places
        numerator = self._scaled * scale
        if numerator >= 0 and other._scaled > 0:
            scaled = numerator // other._scaled
        elif numerator >= 0 and other._scaled < 0:
            scaled = -(numerator // -other._scaled)
        elif numerator < 0 and other._scaled > 0:
            scaled = -((-numerator) // other._scaled)
        else:
            scaled = (-numerator) // -other._scaled
        return FixedDecimal(scaled, self._places)

    def __neg__(self) -> "FixedDecimal":
        return FixedDecimal(-self._scaled, self._places)

    def __abs__(self) -> "FixedDecimal":
        return FixedDecimal(abs(self._scaled), self._places)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FixedDecimal):
            return NotImplemented
        return self._places == other._places and self._scaled == other._scaled

    def __hash__(self) -> int:
        return hash((self._scaled, self._places))

    def __lt__(self, other: "FixedDecimal") -> bool:
        self._check_same_places(other)
        return self._scaled < other._scaled

    def __le__(self, other: "FixedDecimal") -> bool:
        self._check_same_places(other)
        return self._scaled <= other._scaled

    def __gt__(self, other: "FixedDecimal") -> bool:
        self._check_same_places(other)
        return self._scaled > other._scaled

    def __ge__(self, other: "FixedDecimal") -> bool:
        self._check_same_places(other)
        return self._scaled >= other._scaled

    def __str__(self) -> str:
        places = self._places
        scaled = self._scaled
        sign = "-" if scaled < 0 else ""
        digits = str(abs(scaled))
        if places == 0:
            return sign + digits
        if len(digits) <= places:
            digits = "0" * (places - len(digits) + 1) + digits
        int_part = digits[:-places]
        frac_part = digits[-places:]
        return f"{sign}{int_part}.{frac_part}"

    def __repr__(self) -> str:
        return f"FixedDecimal({self._scaled!r}, {self._places!r})"
