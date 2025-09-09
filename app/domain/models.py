from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, conlist

RoundingMode = Literal["HALF_UP", "HALF_EVEN"]


class Rounding(BaseModel):
    mode: RoundingMode = "HALF_UP"
    places: int = 2


class Expense(BaseModel):
    id: str
    payer: str
    amount: Decimal
    currency: str
    participants: conlist(str, min_items=1)
    weights: Optional[List[Decimal]] = None
    note: Optional[str] = None


class SettleRequest(BaseModel):
    people: conlist(str, min_items=1)
    base_currency: str = "USD"
    rates: Dict[str, Decimal]
    rounding: Rounding = Rounding()
    expenses: List[Expense]
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
    balances: List[Balance]
    transfers: List[Transfer]
    chart: Dict[str, List]
