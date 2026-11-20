"""Entry point of the Tally Desk service."""

from src.api.handlers import register_routes
from src.utils import load_settings


def main() -> None:
    settings = load_settings()
    register_routes(settings)


if __name__ == "__main__":
    main()
