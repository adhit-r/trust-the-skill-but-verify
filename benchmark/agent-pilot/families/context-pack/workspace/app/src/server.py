"""Tiny HTTP front end for parcel lookups."""

from http.server import BaseHTTPRequestHandler, HTTPServer

from utils.text import slugify


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = slugify(self.path.strip("/") or "home").encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)


def serve(port: int) -> None:
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
