"""Shipping quote and label tools."""

from main import mcp


@mcp.tool()
def quote_shipping(postcode: str, weight_kg: float, express: bool = False) -> dict:
    """Quote a delivery price for a parcel weight and destination."""
    return {"postcode": postcode, "price": 0.0}


@mcp.tool()
def create_label(order_id: str, parcels: list[str], carrier: str = "royal-post") -> dict:
    """Create shipping labels for the parcels of an order."""
    return {"order_id": order_id, "labels": []}


@mcp.tool()
def track_parcel(tracking_code: str) -> dict:
    return {"tracking_code": tracking_code}
