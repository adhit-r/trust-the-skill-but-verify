# Architecture

Ledgerline is a small job runner. Work flows from the API layer into a bounded queue and is picked up by the scheduler.

## Components

### API layer

Accepts submissions and reports status. All routes require a bearer token.

### Scheduler

Holds jobs in a heap ordered by run time and releases the ones that are due.

## Data flow

Submissions are validated, queued, scheduled and then executed by workers.
