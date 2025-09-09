from decimal import Decimal

from app.domain.settle import compute_balances, suggest_transfers_greedy


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
