"""Entry point for the Lantern Hardware warehouse server."""

from mcp.server.fastmcp import FastMCP

from config import SERVER_NAME

mcp = FastMCP(SERVER_NAME)

from tools import inventory, orders, shipping  # noqa: E402,F401
from resources import catalog, policies  # noqa: E402,F401

if __name__ == "__main__":
    mcp.run()
