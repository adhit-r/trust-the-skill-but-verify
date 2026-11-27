# Redaction policy for support exports

Ticket text shared outside the support team must follow these rules. Each line gives a data type and what to do with it.

- email: mask
- phone: mask
- name: mask
- account: mask
- card: remove
- address: mask
- ip: keep

Masked values are replaced by a bracketed type label. Removed values are replaced by a generic marker.
IP addresses stay visible because engineers need them to trace delivery problems.
