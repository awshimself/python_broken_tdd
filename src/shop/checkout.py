"""Order checkout.

The rules live in `src/shop/specs/checkout.md` - read it first.
Both functions below are stubs: their signature is final, the bodies are yours.
Do not change the constants: the tests rely on them.
"""

from shop.money import percent_of

PROMO_CODES = {"WELCOME10": 10, "SUMMER15": 15, "VIP35": 35}
SUPPORTED_CITIES = ("msk", "spb")
MAX_DISCOUNT_PERCENT = 30
VAT_PERCENT = 20
SHIPPING_KOPEKS = 49_000
FREE_DELIVERY_FROM_KOPEKS = 500_000
TIER_DISCOUNTS = ((10, 5), (25, 10), (50, 15))
REQUIRED_LINE_KEYS = ("sku", "qty", "unit_price_kopecks")


def validate_order(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> str | None:
    """Return a human readable reason why the order is invalid, or None if it is fine."""
    if not lines:
        return "Order is empty."

    seen_skus: set[str] = set()
    for index, line in enumerate(lines, start=1):
        if not all(key in line for key in REQUIRED_LINE_KEYS):
            return f"Line {index} is missing a required key."

        sku = line.get("sku")
        if not isinstance(sku, str) or not sku.strip():
            return f"Line {index} has an empty sku."
        if sku in seen_skus:
            return f"Duplicate sku: {sku}."
        seen_skus.add(sku)

        qty_raw = line.get("qty")
        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            return f"Line {index} has a non-numeric quantity."
        if qty <= 0:
            return f"Line {index} quantity must be greater than zero."

        price_raw = line.get("unit_price_kopecks")
        try:
            unit_price = int(price_raw)
        except (TypeError, ValueError):
            return f"Line {index} has a non-numeric unit price."
        if unit_price < 0:
            return f"Line {index} price cannot be negative."

    if promo_code and promo_code not in PROMO_CODES:
        return "Unknown promo code."

    if shipping_city and shipping_city not in SUPPORTED_CITIES:
        return "Unsupported shipping city."

    return None


def calculate_order_total(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> int | None:
    """Return the order total in kopecks, or None if the order is invalid."""
    reason = validate_order(lines, promo_code, shipping_city)
    if reason is not None:
        return None

    subtotal = 0
    total_qty = 0
    for line in lines:
        qty = int(line["qty"])
        unit_price = int(line["unit_price_kopecks"])
        subtotal += qty * unit_price
        total_qty += qty

    tier_percent = 0
    for threshold, percent in TIER_DISCOUNTS:
        if total_qty >= threshold:
            tier_percent = percent

    promo_percent = PROMO_CODES.get(promo_code, 0) if promo_code else 0
    discount_percent = max(tier_percent, promo_percent)
    if discount_percent > MAX_DISCOUNT_PERCENT:
        discount_percent = MAX_DISCOUNT_PERCENT

    discount = percent_of(subtotal, discount_percent)
    discounted_subtotal = subtotal - discount

    shipping = 0
    if shipping_city and discounted_subtotal < FREE_DELIVERY_FROM_KOPEKS:
        shipping = SHIPPING_KOPEKS

    base = discounted_subtotal + shipping
    vat = percent_of(base, VAT_PERCENT)
    total = base + vat
    return total
