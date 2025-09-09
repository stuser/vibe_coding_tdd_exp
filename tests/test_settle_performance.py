import random
import time
from decimal import Decimal

from app.domain.settle import suggest_transfers_greedy


def old_suggest_transfers_greedy(balances, places=2):
    from app.domain.settle import _quantize

    cents = {p: _quantize(a, places) for p, a in balances.items()}
    creditors = [(p, +amt) for p, amt in cents.items() if amt > 0]
    debtors = [(p, -amt) for p, amt in cents.items() if amt < 0]
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)
    transfers = []
    while creditors and debtors:
        c_name, c_amt = creditors[0]
        d_name, d_amt = debtors[0]
        x = min(c_amt, d_amt)
        if x > 0:
            transfers.append({"from": d_name, "to": c_name, "amount": x})
        if c_amt > d_amt:
            creditors[0] = (c_name, c_amt - x)
            debtors.pop(0)
        elif d_amt > c_amt:
            debtors[0] = (d_name, d_amt - x)
            creditors.pop(0)
        else:
            creditors.pop(0)
            debtors.pop(0)
        creditors.sort(key=lambda y: y[1], reverse=True)
        debtors.sort(key=lambda y: y[1], reverse=True)
    return transfers


def test_heap_greedy_is_faster():
    random.seed(0)
    N = 1000
    balances = {f"p{i}": Decimal(random.randint(-1000, 1000)) for i in range(N)}
    s = sum(balances.values())
    balances["p0"] -= s

    start = time.perf_counter()
    old_suggest_transfers_greedy(balances.copy())
    old_time = time.perf_counter() - start

    start = time.perf_counter()
    suggest_transfers_greedy(balances.copy())
    new_time = time.perf_counter() - start

    assert new_time < old_time
