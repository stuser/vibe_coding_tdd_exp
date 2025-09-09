from decimal import Decimal

from app.domain.settle import compute_balances, suggest_transfers_greedy
from app.utils.errors import InvalidAmountError, MissingRateError


def test_should_compute_balances_for_mixed_currencies():
    people = ["Alice", "Bob", "Carol"]
    rates = {"USD": Decimal("1"), "CHF": Decimal("1.10"), "EUR": Decimal("1.08")}
    expenses = [
        dict(
            id="e1",
            payer="Alice",
            amount=Decimal("90"),
            currency="CHF",
            participants=["Alice", "Bob"],
        ),
        dict(
            id="e2",
            payer="Bob",
            amount=Decimal("150"),
            currency="USD",
            participants=["Alice", "Bob", "Carol"],
        ),
        dict(
            id="e3",
            payer="Carol",
            amount=Decimal("120"),
            currency="EUR",
            participants=["Alice", "Carol"],
        ),
    ]

    balances = compute_balances(people, rates, expenses)

    assert balances["Alice"] == Decimal("-65.30")
    assert balances["Bob"] == Decimal("50.50")
    assert balances["Carol"] == Decimal("14.80")
    assert sum(balances.values()) == Decimal("0.00")


def test_should_suggest_minimum_transfers_for_three_people():
    balances = {"Alice": Decimal("-65.30"), "Bob": Decimal("50.50"), "Carol": Decimal("14.80")}
    transfers = suggest_transfers_greedy(balances)
    assert transfers == [
        {"from": "Alice", "to": "Bob", "amount": Decimal("50.50")},
        {"from": "Alice", "to": "Carol", "amount": Decimal("14.80")},
    ]


def test_should_return_zero_transfers_when_all_balances_zero():
    balances = {"A": Decimal("0.00"), "B": Decimal("0.00")}
    assert suggest_transfers_greedy(balances) == []


def test_should_handle_multiple_creditors_and_debtors_greedily():
    balances = {
        "A": Decimal("-30.00"),
        "B": Decimal("-20.00"),
        "C": Decimal("25.00"),
        "D": Decimal("25.00"),
    }
    transfers = suggest_transfers_greedy(balances)
    # Expect three transfers max (non-zero people 4 -> <= 3), greedy specific pairing
    assert len(transfers) <= 3
    # Amounts should settle exactly
    total_from = {}
    total_to = {}
    for t in transfers:
        total_from[t["from"]] = total_from.get(t["from"], Decimal("0")) + t["amount"]
        total_to[t["to"]] = total_to.get(t["to"], Decimal("0")) + t["amount"]
    assert total_from.get("A", Decimal("0")) + total_from.get("B", Decimal("0")) == Decimal("50.00")
    assert total_to.get("C", Decimal("0")) + total_to.get("D", Decimal("0")) == Decimal("50.00")


def test_should_reject_negative_or_zero_amounts():
    people = ["A", "B"]
    rates = {"USD": Decimal("1")}
    expenses = [
        dict(id="e1", payer="A", amount=Decimal("0"), currency="USD", participants=["A", "B"])
    ]
    try:
        compute_balances(people, rates, expenses)
    except InvalidAmountError:
        pass
    else:
        assert False, "Expected InvalidAmountError"


def test_should_error_when_missing_rate_for_currency():
    people = ["A", "B"]
    rates = {"USD": Decimal("1")}
    expenses = [
        dict(id="e1", payer="A", amount=Decimal("10"), currency="CHF", participants=["A"])  # CHF missing
    ]
    try:
        compute_balances(people, rates, expenses)
    except MissingRateError:
        pass
    else:
        assert False, "Expected MissingRateError"


def test_should_round_output_balances_to_two_decimals_and_sum_zero():
    people = ["A", "B", "C"]
    rates = {"USD": Decimal("1")}
    expenses = [
        dict(id="e1", payer="A", amount=Decimal("100"), currency="USD", participants=["A", "B", "C"])
    ]
    bal = compute_balances(people, rates, expenses)
    # Two decimals
    assert all(str(v).count(".") <= 1 and len(str(v).split(".")[-1]) <= 2 for v in bal.values())
    # Sum zero
    assert sum(bal.values()) == Decimal("0.00")


def test_should_not_charge_non_participants():
    people = ["Alice", "Bob", "Carol"]
    rates = {"USD": Decimal("1")}
    expenses = [
        dict(id="e1", payer="Alice", amount=Decimal("90"), currency="USD", participants=["Alice", "Bob"])
    ]
    bal = compute_balances(people, rates, expenses)
    # Carol did not participate; should not be charged and not credited
    assert bal["Carol"] == Decimal("0.00")


def test_should_allow_subset_participation_per_expense():
    people = ["Alice", "Bob", "Carol"]
    rates = {"USD": Decimal("1")}
    expenses = [
        dict(id="e1", payer="Alice", amount=Decimal("60"), currency="USD", participants=["Alice", "Bob"]),
        dict(id="e2", payer="Bob", amount=Decimal("30"), currency="USD", participants=["Bob", "Carol"]),
    ]
    bal = compute_balances(people, rates, expenses)
    # First expense: A,B share 30 each; payer A credited 60, so A +60 -30 = +30; B -30
    # Second expense: B,C share 15 each; B +30 -15 = +15; C -15
    # Final: A +30, B (-30 + 15) = -15, C -15 -> sum zero => after rounding {A: +30.00, B: -15.00, C: -15.00}
    assert bal == {"Alice": Decimal("30.00"), "Bob": Decimal("-15.00"), "Carol": Decimal("-15.00")}
