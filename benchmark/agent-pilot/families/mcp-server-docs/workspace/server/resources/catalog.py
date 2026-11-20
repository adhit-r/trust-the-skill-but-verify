"""Catalog resources."""

from main import mcp


@mcp.resource("catalog://items")
def list_items() -> str:
    """The full item catalog as JSON."""
    return "[]"


@mcp.resource("catalog://items/{sku}")
def item_detail(sku: str) -> str:
    """Details for one catalog item."""
    return "{}"


@mcp.resource("catalog://categories", mime_type="application/json")
def list_categories() -> str:
    """Category tree used by the catalog."""
    return "{}"
