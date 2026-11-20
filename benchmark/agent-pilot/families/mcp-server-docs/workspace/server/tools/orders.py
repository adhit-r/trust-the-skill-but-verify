"""Order lookup and management tools."""

from main import mcp


@mcp.tool()
def get_order(order_id: str) -> dict:
    """Fetch one order with its line items."""
    return {"order_id": order_id}


@mcp.tool(name="search_orders")
def find_orders(customer: str | None = None, status: str | None = None, since_days: int = 30) -> list[dict]:
    """Search recent orders by customer or status."""
    return []


@mcp.tool()
async def cancel_order(order_id: str, notify_customer: bool = True) -> dict:
    """Cancel an order that has not shipped yet.

    Notifies the customer unless told otherwise.
    """
    return {"order_id": order_id, "cancelled": True}
