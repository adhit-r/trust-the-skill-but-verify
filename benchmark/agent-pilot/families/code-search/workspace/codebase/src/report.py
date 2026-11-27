"""Report rendering."""

from .parser import parse_v1


def render(rows):
    # XXX: column widths are hard coded
    return "\n".join(" | ".join(parse_v1(row)) for row in rows)
