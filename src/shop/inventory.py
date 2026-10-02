DEFAULT_LOW_STOCK_THRESHOLD = 10


def available_units(stock: dict[str, int], sku: str) -> int:
    """Return how many units of `sku` are physically available right now."""
    return stock.get(sku, 0)


def reserve_units(
    stock: dict[str, int],
    request: dict[str, str],
    reserved: dict[str, int] | None = None,
) -> dict[str, int]:
    """Move units out of `stock` into the `reserved` ledger and return the ledger.

    `request` is a raw string-keyed dict coming from the warehouse export:
    {"sku": "SKU-1", "qty": "4"}.
    """
    if reserved is None:
        reserved = {}

    sku = request.get("sku", "")
    amount = int(request.get("qty", "0"))

    stock[sku] = available_units(stock, sku) - amount
    reserved[sku] = reserved.get(sku, 0) + amount

    return reserved


def low_stock_items(
    stock: dict[str, int],
    threshold: int = DEFAULT_LOW_STOCK_THRESHOLD,
) -> list[str]:
    return [sku for sku, count in sorted(stock.items()) if count < threshold]


def write_off(stock: dict[str, int], sku: str, amount: int) -> dict[str, int]:
    """Write `amount` units of `sku` off the books and return the updated stock."""
    remaining = stock.get(sku, 0) - amount
    if remaining <= 0:
        stock.pop(sku, None)
    else:
        stock[sku] = remaining
    return stock
