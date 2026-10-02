"""Order checkout, part 2.

How to work through this file:

1. The single red test below is done for you - it shows what RED looks like.
2. Run `./scripts/check-part2.sh` and read the failure.
3. Write one assertion per rule from `src/shop/specs/checkout.md` into the empty
   tests: a failing test first, then the code that makes it pass.
4. Never edit a finished assertion, never `skip`, never weaken a test.

Run one test at a time while you work:

    uv run pytest tests/test_checkout.py -k tier -x
"""

from shop.checkout import calculate_order_total, validate_order


def line(sku: str = "SKU-1", qty: str = "1", unit_price_kopecks: str = "10000") -> dict[str, str]:
    """Build one order line the way the warehouse export delivers it."""
    return {"sku": sku, "qty": qty, "unit_price_kopecks": unit_price_kopecks}


def test_smoke_single_line_without_delivery() -> None:
    """One line, no promo code, no delivery. Works out to 100.00 rub + 20% VAT."""
    assert validate_order([line()]) is None
    assert calculate_order_total([line()]) == 12_000


def test_empty_order_is_rejected() -> None:
    """Spec 3, rule 1: an order without lines cannot be processed."""
    assert validate_order([]) is not None
    assert calculate_order_total([]) is None


def test_empty_sku_is_rejected() -> None:
    """Spec 3, rule 2: a blank article code is not allowed."""
    assert validate_order([line(sku="")]) is not None
    assert calculate_order_total([line(sku="")]) is None


def test_missing_line_key_is_rejected() -> None:
    """Spec 3, rule 3: every required key must be present."""
    bad = [{"sku": "SKU-1", "qty": "1"}]
    assert validate_order(bad) is not None
    assert calculate_order_total(bad) is None


def test_non_numeric_quantity_is_rejected() -> None:
    """Spec 3, rule 4: `qty` must be a whole number."""
    assert validate_order([line(qty="abc")]) is not None
    assert calculate_order_total([line(qty="abc")]) is None


def test_zero_quantity_is_rejected() -> None:
    """Spec 3, rule 5: `qty` must be greater than zero."""
    assert validate_order([line(qty="0")]) is not None
    assert calculate_order_total([line(qty="0")]) is None


def test_non_numeric_price_is_rejected() -> None:
    """Spec 3, rule 6: `unit_price_kopecks` must be a whole number."""
    assert validate_order([line(unit_price_kopecks="abc")]) is not None
    assert calculate_order_total([line(unit_price_kopecks="abc")]) is None


def test_negative_price_is_rejected() -> None:
    """Spec 3, rule 7: a price may not be negative."""
    assert validate_order([line(unit_price_kopecks="-1")]) is not None
    assert calculate_order_total([line(unit_price_kopecks="-1")]) is None


def test_duplicate_sku_is_rejected() -> None:
    """Spec 3, rule 8: the same article may appear only once."""
    bad = [line(sku="SKU-1", qty="2"), line(sku="SKU-1", qty="3")]
    assert validate_order(bad) is not None
    assert calculate_order_total(bad) is None


def test_unknown_promo_code_is_rejected() -> None:
    """Spec 3, rule 9: only codes from PROMO_CODES exist."""
    assert validate_order([line()], promo_code="BAD") is not None
    assert calculate_order_total([line()], promo_code="BAD") is None


def test_unsupported_city_is_rejected() -> None:
    """Spec 3, rule 10: only cities from SUPPORTED_CITIES are served."""
    assert validate_order([line()], shipping_city="ldn") is not None
    assert calculate_order_total([line()], shipping_city="ldn") is None


def test_valid_order_passes_validation() -> None:
    """Spec 3: a good order gets None back instead of a reason."""
    assert validate_order([line(sku="SKU-1", qty="2", unit_price_kopecks="3000")]) is None
    assert calculate_order_total([line(sku="SKU-1", qty="2", unit_price_kopecks="3000")]) == 7_200


def test_no_discount_below_first_tier() -> None:
    """Spec 4, steps 1-2: 9 units are below every threshold."""
    assert calculate_order_total([line(qty="9", unit_price_kopecks="1000")]) == 10_800


def test_tier_discount_at_first_threshold() -> None:
    """Spec 4, steps 2-5: 10 units give 5%. Compare with example 2."""
    assert calculate_order_total([line(qty="10", unit_price_kopecks="1990")]) == 22_686


def test_tier_discount_at_highest_threshold() -> None:
    """Spec 4, steps 2-5: 50 units give 15%, not 5% + 10%."""
    assert calculate_order_total([line(qty="50", unit_price_kopecks="1990")]) == 101_490


def test_promo_code_beats_tier_discount() -> None:
    """Spec 4, steps 3-4: the bigger percentage wins, the two do not add up."""
    assert calculate_order_total([line(qty="10", unit_price_kopecks="1000")], promo_code="WELCOME10") == 10_800


def test_discount_is_capped_at_thirty_percent() -> None:
    """Spec 4, step 5: VIP35 gives 35%, but the cap is 30%. Compare with example 4."""
    assert calculate_order_total([line(qty="100", unit_price_kopecks="10000")], promo_code="VIP35", shipping_city="spb") == 840_000


def test_delivery_is_charged_for_small_order() -> None:
    """Spec 4, steps 7-10: a city adds SHIPPING_KOPEKS and VAT is charged on it."""
    assert calculate_order_total([line()], shipping_city="msk") == 70_800


def test_free_delivery_uses_discounted_subtotal() -> None:
    """Spec 4, step 7: the threshold is checked against the sum after the discount."""
    assert calculate_order_total([line(sku="SKU-1", qty="1", unit_price_kopecks="500000")], shipping_city="msk") == 600_000


def test_vat_is_charged_on_the_discounted_sum() -> None:
    """Spec 4, steps 8-10: base = discounted subtotal + delivery."""
    assert calculate_order_total([line(qty="10", unit_price_kopecks="10000")], shipping_city="msk") == 172_800
