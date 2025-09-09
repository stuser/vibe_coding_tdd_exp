from __future__ import annotations

import heapq
from collections.abc import Iterable, Mapping
from decimal import ROUND_HALF_UP, Decimal

from ..utils.validation import (
    ensure_positive_amount,
    validate_currency_present,
    validate_participants_subset,
    validate_weights,
)
from .money import to_base
from .share import split_shares


def _quantize(amount: Decimal, places: int = 2) -> Decimal:
    q = Decimal(10) ** -places
    return amount.quantize(q, rounding=ROUND_HALF_UP)


def compute_balances(
    people: Iterable[str],
    rates: Mapping[str, Decimal],
    expenses: Iterable[Mapping],
    places: int = 2,
) -> dict[str, Decimal]:
    balances: dict[str, Decimal] = {p: Decimal("0") for p in people}

    for e in expenses:
        payer = e["payer"]
        amount = Decimal(e["amount"])  # accept Decimal or str
        currency = e["currency"]
        participants = list(e["participants"])  # type: ignore[index]

        ensure_positive_amount(amount)
        validate_currency_present(currency, rates)
        validate_participants_subset(participants, people)
        validate_weights(e.get("weights"), len(participants))

        base_amount = to_base(amount, currency, rates)
        shares = split_shares(base_amount, participants, e.get("weights"))

        # payer pays upfront
        balances[payer] = balances.get(payer, Decimal("0")) + base_amount
        # each participant owes their share
        for person, share in shares.items():
            balances[person] = balances.get(person, Decimal("0")) - share

    # Round to requested places for output consistency
    rounded = {p: _quantize(a, places) for p, a in balances.items()}

    # Adjust last cent to make the sum exactly zero (largest remainder method)
    total = sum(rounded.values())
    if total != Decimal("0").quantize(Decimal(10) ** -places):
        # Shift the discrepancy to the person with the largest absolute remainder pre-rounding
        remainders = {p: balances[p] - rounded[p] for p in rounded}
        # pick the one whose adjustment brings total to zero
        # If total > 0, reduce someone slightly:
        # take from a creditor -> choose max positive remainder
        # If total < 0, increase someone slightly:
        # give to a debtor -> choose most negative remainder
        if total > 0:
            target = max(remainders, key=lambda k: remainders[k])
            rounded[target] -= total
        else:
            target = min(remainders, key=lambda k: remainders[k])
            rounded[target] -= total

    return rounded


def suggest_transfers_greedy(
    balances: Mapping[str, Decimal],
    places: int = 2,
) -> list[dict[str, Decimal | str]]:
    # Round balances to cents for transfer computation
    cents = {p: _quantize(a, places) for p, a in balances.items()}
    # use negative amounts to turn heapq into a max-heap
    creditors: list[tuple[Decimal, str]] = [(-amt, p) for p, amt in cents.items() if amt > 0]
    debtors: list[tuple[Decimal, str]] = [(amt, p) for p, amt in cents.items() if amt < 0]

    heapq.heapify(creditors)
    heapq.heapify(debtors)

    transfers: list[dict[str, Decimal | str]] = []

    while creditors and debtors:
        c_amt_neg, c_name = heapq.heappop(creditors)
        d_amt_neg, d_name = heapq.heappop(debtors)

        c_amt = -c_amt_neg
        d_amt = -d_amt_neg
        x = min(c_amt, d_amt)

        if x > 0:
            transfers.append({"from": d_name, "to": c_name, "amount": _quantize(x, places)})

        c_remaining = c_amt - x
        d_remaining = d_amt - x

        if c_remaining > 0:
            heapq.heappush(creditors, (-c_remaining, c_name))
        if d_remaining > 0:
            heapq.heappush(debtors, (-d_remaining, d_name))

    return transfers
