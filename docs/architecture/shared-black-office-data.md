# Shared Black Office Data Architecture

## Governing rule

**The Black Office owns the data. The goblins work with it.**

A goblin may create, inspect, enrich, or act on records within its specialty,
but clients, projects, agreements, expenses, invoices, and payments are Office
records rather than goblin-private records.

## Core record chain

`Business -> Client -> Project -> Agreement -> Expense -> Invoice -> Payment`

The chain is relational, not strictly linear. A project may have multiple
agreements, expenses, invoices, and payments. Expenses can exist before a
project assignment and can later be classified by Ledgergut or Æterna.

## Specialist responsibilities

- **Æterna** receives human intent, resolves context, and routes work.
- **Ledgergut** creates and enriches Expense records from receipts and other
  evidence of spending.
- **SigNor** creates and manages Agreement records, including scope,
  assumptions, exclusions, pricing, and changes.
- **Squarmish** creates and manages Invoice records using agreed scope,
  completed work, and billable expenses.
- Future goblins consume the same Office records rather than duplicating them.

## Persistence boundary

Goblin workflows must not depend directly on JSON files, PostgreSQL, object
storage, or any other persistence technology. They operate through shared store
interfaces in `app.core.storage`.

This allows:

1. local/test storage without cloud dependencies;
2. PostgreSQL in production;
3. object storage for receipt/document binaries;
4. migration without rewriting specialist business logic.

## Migration policy

Ledgergut's existing JSON-backed receipt store remains operational during the
transition. New shared models are introduced first. Ledgergut is then adapted
to emit shared Expense records while preserving its existing receipt workflow
and tests. The JSON store is retired only after the production persistence
implementation and migration path are verified.

## Multi-tenant rule

Every business-owned production record carries `business_id`. Queries and
mutations must be scoped to the authenticated business before commercial beta.
No goblin may infer or bypass tenant scope.
