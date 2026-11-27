"""HTTP handlers for the desk API."""

ROUTES = {"/tickets": "list_tickets", "/tickets/new": "create_ticket"}


def register_routes(settings: dict) -> list[str]:
    return sorted(ROUTES)
