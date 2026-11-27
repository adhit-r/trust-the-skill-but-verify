"""Stock lookup and adjustment tools."""

from main import mcp


@mcp.tool()
def get_stock(sku: str, warehouse: str = "main") -> dict:
    """Return the on-hand quantity for a SKU in one warehouse."""
    return {"sku": sku, "warehouse": warehouse, "on_hand": 0}


@mcp.tool()
def adjust_stock(sku: str, delta: int, reason: str, warehouse: str = "main") -> dict:
    """Apply a signed stock adjustment and record the reason."""
    return {"sku": sku, "delta": delta, "reason": reason}


@mcp.tool()
def list_low_stock(threshold: int = 10, limit: int = 25) -> list[dict]:
    """List SKUs at or below the reorder threshold."""
    return []


def normalise_sku(sku: str) -> str:
    return sku.strip().upper()
