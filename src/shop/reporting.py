from datetime import UTC, datetime

from shop.inventory import low_stock_items
from shop.money import format_kopecks

REPORT_HEADER = "Stock report"
DEFAULT_LOW_STOCK_THRESHOLD = 10


def build_stock_report(
    stock: dict[str, int],
    prices: dict[str, int],
    threshold: int = DEFAULT_LOW_STOCK_THRESHOLD,
) -> str:
    generated_at = datetime.now(UTC).isoformat()
    total_value = 0

    lines = [REPORT_HEADER, f"generated_at={generated_at}"]

    for sku, count in sorted(stock.items()):
        unit_price = prices.get(sku, 0)
        value = count * unit_price
        total_value += value

        lines.append(f"{sku}: {count} x {format_kopecks(unit_price)} = {format_kopecks(value)}")

    low = low_stock_items(stock, threshold)
    low_text = ", ".join(low) if low else "none"

    lines.append(f"low stock: {low_text}")
    lines.append(f"total value: {format_kopecks(total_value)}")

    return "\n".join(lines)


def stock_health(
    count: int,
    incoming: int,
    sold_last_week: int,
    threshold: int = DEFAULT_LOW_STOCK_THRESHOLD,
) -> str:
    daily = sold_last_week // 7 if sold_last_week else 0

    if count <= 0:
        return "out_of_stock"

    if count < threshold:
        if incoming > 0:
            return "incoming_low"
        return "low"

    if count < threshold * 3:
        if daily == 0:
            return "unknown_demand"
        if count < daily * 3:
            return "reorder_soon"
        return "ok"

    if count < daily * 3:
        return "reorder_soon"

    return "ok"
