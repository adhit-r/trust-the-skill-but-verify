"""Policy documents exposed as resources."""

from main import mcp


@mcp.resource("policy://returns", mime_type="text/markdown")
def returns_policy() -> str:
    """The returns policy shown to customers."""
    return "# Returns"


@mcp.resource("policy://shipping/{region}", mime_type="text/markdown")
def shipping_policy(region: str) -> str:
    """Shipping policy for a region."""
    return "# Shipping"
