from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

RoundingMode = Literal["HALF_UP", "HALF_EVEN"]


class Rounding(BaseModel):
    mode: RoundingMode = "HALF_UP"
    places: int = 2


class Expense(BaseModel):
    id: str
    payer: str
    amount: Decimal
    currency: str
    participants: list[str] = Field(min_length=1)
    weights: list[Decimal] | None = None
    note: str | None = None


class SettleRequest(BaseModel):
    people: list[str] = Field(min_length=1)
    base_currency: str = "USD"
    rates: dict[str, Decimal]
    rounding: Rounding = Rounding()
    expenses: list[Expense]
    optimize: Literal["greedy", "exact"] = "greedy"


class Balance(BaseModel):
    person: str
    amount: Decimal  # signed, in base


class Transfer(BaseModel):
    from_: str = Field(serialization_alias="from", validation_alias="from")
    to: str
    amount: Decimal
    currency: str


class SettleResponse(BaseModel):
    base_currency: str
    balances: list[Balance]
    transfers: list[Transfer]
    chart: dict[str, list]
