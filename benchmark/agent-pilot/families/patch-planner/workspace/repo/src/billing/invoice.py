"""Invoice totals."""

from decimal import Decimal, ROUND_HALF_UP


def invoice_total(lines, tax_rate):
    subtotal = sum(Decimal(str(price)) * qty for price, qty in lines)
    tax = subtotal * Decimal(str(tax_rate))
    return (subtotal + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_total(amount, currency):
    return f"{amount} {currency}"


def apply_discount(total, percent):
    return total - (total * Decimal(percent) / 100)
