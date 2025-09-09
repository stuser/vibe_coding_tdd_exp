from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app


def test_should_return_json_response_with_balances_transfers_and_chart():
    client = TestClient(app)
    payload = {
        "people": ["Alice", "Bob", "Carol"],
        "base_currency": "USD",
        "rates": {"USD": "1", "CHF": "1.10", "EUR": "1.08"},
        "rounding": {"mode": "HALF_UP", "places": 2},
        "expenses": [
            {
                "id": "e1",
                "payer": "Alice",
                "amount": "90",
                "currency": "CHF",
                "participants": ["Alice", "Bob"],
                "note": "Swiss pass",
            },
            {
                "id": "e2",
                "payer": "Bob",
                "amount": "150",
                "currency": "USD",
                "participants": ["Alice", "Bob", "Carol"],
                "note": "Hotel",
            },
            {
                "id": "e3",
                "payer": "Carol",
                "amount": "120",
                "currency": "EUR",
                "participants": ["Alice", "Carol"],
                "note": "Tour",
            },
        ],
        "optimize": "greedy",
    }
    resp = client.post("/api/settle", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["base_currency"] == "USD"
    balances = {b["person"]: Decimal(b["amount"]) for b in data["balances"]}
    assert balances == {
        "Alice": Decimal("-65.30"),
        "Bob": Decimal("50.50"),
        "Carol": Decimal("14.80"),
    }
    transfers = [
        {
            "from": t["from"],
            "to": t["to"],
            "amount": Decimal(str(t["amount"])),
            "currency": t["currency"],
        }
        for t in data["transfers"]
    ]
    assert transfers == [
        {"from": "Alice", "to": "Bob", "amount": Decimal("50.50"), "currency": "USD"},
        {"from": "Alice", "to": "Carol", "amount": Decimal("14.80"), "currency": "USD"},
    ]
    assert data["chart"]["labels"] == ["Alice", "Bob", "Carol"]
    assert data["chart"]["values"] == [b["amount"] for b in data["balances"]]
    chart_values = [Decimal(v) for v in data["chart"]["values"]]
    assert chart_values == [balances[name] for name in data["chart"]["labels"]]


def test_should_return_501_when_optimize_exact_not_implemented():
    client = TestClient(app)
    payload = {
        "people": ["Alice", "Bob", "Carol"],
        "base_currency": "USD",
        "rates": {"USD": "1", "CHF": "1.10", "EUR": "1.08"},
        "rounding": {"mode": "HALF_UP", "places": 2},
        "expenses": [
            {
                "id": "e1",
                "payer": "Alice",
                "amount": "90",
                "currency": "CHF",
                "participants": ["Alice", "Bob"],
                "note": "Swiss pass",
            }
        ],
        "optimize": "exact",
    }
    resp = client.post("/api/settle", json=payload)
    assert resp.status_code == 501
    assert resp.json() == {"detail": "exact mode not implemented"}


def test_should_validate_payload_and_return_422_on_bad_input():
    client = TestClient(app)
    payload = {
        "people": ["Alice", "Bob"],
        "base_currency": "USD",
        "rates": {"USD": "1"},
        "expenses": [
            {
                "id": "e1",
                "payer": "Alice",
                "amount": "0",
                "currency": "USD",
                "participants": ["Alice", "Bob"],
            }
        ],
    }
    resp = client.post("/api/settle", json=payload)
    assert resp.status_code == 422


def test_should_render_index_page_with_chart_js():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Chart" in resp.content
