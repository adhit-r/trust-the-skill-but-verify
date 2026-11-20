"""Regional tax lookup."""

RATES = {
    "NW": "0.08",
    "SE": "0.065",
    "CE": "0.07",
}


def tax_rate(region):
    return RATES[region]


def is_exempt(customer):
    return customer.get("exempt", False)
