# Ticket export notes

Exports cover tickets opened between 2026-09-01 and 2026-09-30, one file per team queue.

- Timestamps are UTC, ISO 8601.
- `first_response` is empty when no agent has replied yet; `resolved` is empty for tickets that are still open or pending.
- Priority targets are listed in sla-policy.json and are measured in wall-clock hours, not business hours.
- Statuses are open, pending, resolved and closed. Pending means waiting on the requester.
- Titles are free text typed by the requester or the first responder, so the same problem is sometimes filed twice with different wording.
