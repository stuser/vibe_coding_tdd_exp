from decimal import Decimal

from app.domain.share import split_shares


def test_should_split_equally_when_no_weights():
    total = Decimal("99")
    participants = ["Alice", "Bob"]
    shares = split_shares(total, participants)
    assert shares == {"Alice": Decimal("49.5"), "Bob": Decimal("49.5")}


def test_should_split_by_relative_weights():
    # total 100, weights 1,2 -> 33.333..., 66.666...
    total = Decimal("100")
    participants = ["Alice", "Bob"]
    weights = [Decimal("1"), Decimal("2")]
    shares = split_shares(total, participants, weights)
    assert shares["Alice"] == Decimal("33.33333333333333333333333333")
    assert shares["Bob"] == Decimal("66.66666666666666666666666667")
