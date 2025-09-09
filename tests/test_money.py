from decimal import Decimal

from app.domain.money import to_base


def test_should_convert_amount_to_base_currency():
    # CHF 90 * 1.10 = USD 99
    amount = Decimal("90")
    rates = {"CHF": Decimal("1.10")}
    assert to_base(amount, "CHF", rates) == Decimal("99")


def test_should_use_decimal_without_precision_loss():
    # 0.1 + 0.2 should be exact with Decimal
    a = Decimal("0.1")
    b = Decimal("0.2")
    c = a + b
    assert c == Decimal("0.3")
