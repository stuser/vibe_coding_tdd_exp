from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal


def split_shares(
    total: Decimal, participants: Iterable[str], weights: Iterable[Decimal] | None = None
) -> dict[str, Decimal]:
    people = list(participants)
    if not people:
        return {}

    if weights is None:
        n = Decimal(len(people))
        per = total / n
        return {p: per for p in people}

    ws = [Decimal(w) for w in weights]
    if len(ws) != len(people):
        raise ValueError("weights length must match participants")
    total_w = sum(ws, start=Decimal(0))
    if total_w <= 0:
        raise ValueError("weights must be positive")
    return {p: (total * w / total_w) for p, w in zip(people, ws, strict=False)}
