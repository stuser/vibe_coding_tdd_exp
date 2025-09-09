from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Mapping

from .errors import (
    InvalidAmountError,
    InvalidParticipantsError,
    InvalidWeightsError,
    MissingRateError,
)


def ensure_positive_amount(amount: Decimal) -> None:
    if amount <= 0:
        raise InvalidAmountError("amount must be > 0")


def validate_currency_present(currency: str, rates: Mapping[str, Decimal]) -> None:
    if currency not in rates:
        raise MissingRateError(f"missing rate for currency: {currency}")
    if rates[currency] <= 0:
        raise MissingRateError(f"invalid rate for currency: {currency}")


def validate_participants_subset(participants: Iterable[str], people: Iterable[str]) -> None:
    pset = set(participants)
    if not pset.issubset(set(people)):
        raise InvalidParticipantsError("participants must be subset of people")
    if len(pset) == 0:
        raise InvalidParticipantsError("participants must not be empty")


def validate_weights(weights: Iterable[Decimal] | None, participants_count: int) -> None:
    if weights is None:
        return
    ws = list(weights)
    if len(ws) != participants_count:
        raise InvalidWeightsError("weights length must match participants count")
    if any(Decimal(w) <= 0 for w in ws):
        raise InvalidWeightsError("weights entries must be > 0")
