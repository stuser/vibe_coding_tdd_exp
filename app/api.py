from __future__ import annotations

from decimal import Decimal
from fastapi import APIRouter, HTTPException

from .domain.models import Balance, SettleRequest, SettleResponse, Transfer
from .domain.settle import compute_balances, suggest_transfers_greedy
from .utils.errors import ValidationError

router = APIRouter()


@router.post("/api/settle", response_model=SettleResponse)
def settle(payload: SettleRequest) -> SettleResponse:
    # Prepare balances in base currency with rounding policy
    try:
        balances_map = compute_balances(
            people=payload.people,
            rates=payload.rates,
            expenses=[e.model_dump() for e in payload.expenses],
            places=payload.rounding.places,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    # Build transfers
    if payload.optimize == "greedy":
        transfers_raw = suggest_transfers_greedy(balances_map, places=payload.rounding.places)
    else:
        # Optional exact mode not implemented; default to greedy for now
        transfers_raw = suggest_transfers_greedy(balances_map, places=payload.rounding.places)

    balances = [Balance(person=p, amount=a) for p, a in balances_map.items()]
    transfers = [
        Transfer.model_validate(
            {
                "from": t["from"],
                "to": t["to"],
                "amount": t["amount"],
                "currency": payload.base_currency,
            }
        )
        for t in transfers_raw
    ]

    labels = [b.person for b in balances]
    quant = Decimal("1").scaleb(-payload.rounding.places)
    values = [str(b.amount.quantize(quant)) for b in balances]

    return SettleResponse(
        base_currency=payload.base_currency,
        balances=balances,
        transfers=transfers,
        chart={"labels": labels, "values": values},
    )
