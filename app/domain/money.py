from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, getcontext

# High precision for all internal money calculations
getcontext().prec = 28


def to_base(amount: Decimal, currency: str, rates: Mapping[str, Decimal]) -> Decimal:
    """
    Convert an amount in a given currency to the base currency using provided rates.
    Rates represent: 1 unit of currency = rates[currency] units of base.
    """
    return amount * rates[currency]
