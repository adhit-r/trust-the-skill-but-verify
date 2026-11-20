"""HTTP routes."""

from billing.invoice import invoice_total
from auth.session import build_cookie


def list_invoices(store):
    return list(store.values())


def get_invoice(store, invoice_id):
    return store[invoice_id]


def login(user_id):
    return build_cookie(user_id)


def total_for(lines, rate):
    return invoice_total(lines, rate)
