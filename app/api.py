from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.domain.models import Balance, SettleRequest, SettleResponse, Transfer
from app.domain.settle import compute_balances, suggest_transfers_greedy
from app.utils.errors import ValidationError

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
            mode=payload.rounding.mode,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    # Build transfers
    if payload.optimize != "greedy":
        raise HTTPException(status_code=501, detail="exact mode not implemented")
    transfers_raw = suggest_transfers_greedy(balances_map, places=payload.rounding.places)

    balances = [Balance(person=p, amount=a) for p, a in balances_map.items()]
    transfers = [
        Transfer(**t, currency=payload.base_currency)
        for t in transfers_raw
    ]

    labels = [b.person for b in balances]
    values = [float(b.amount) for b in balances]

    return SettleResponse(
        base_currency=payload.base_currency,
        balances=balances,
        transfers=transfers,
        chart={"labels": labels, "values": values},
    )
