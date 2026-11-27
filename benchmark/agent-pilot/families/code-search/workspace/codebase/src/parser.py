"""Document parsing helpers."""

legacy_mode = False


def parse_v1(text):
    # FIXME: does not handle quoted commas
    return text.split(",")


def parse_document(text):
    if legacy_mode:
        return parse_v1(text)
    # TODO: support nested sections
    return [line for line in text.splitlines() if line]
