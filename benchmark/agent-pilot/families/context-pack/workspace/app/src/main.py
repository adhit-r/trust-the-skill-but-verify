"""Entry point for the parcel tracker service."""

from config import load_config
from server import serve
from utils.dates import days_between


def main() -> None:
    config = load_config()
    print(f"Tracking since {config['start']} ({days_between(config['start'], config['end'])} days)")
    serve(config["port"])


if __name__ == "__main__":
    main()
