# Shared Black Office Data Architecture

## Governing rule

**The Black Office owns the data. The goblins work with it.**

A goblin may create, inspect, enrich, or act on records within its specialty,
but clients, projects, agreements, estimates, material plans, shopping-list
items, expenses, work logs, invoices, and payments are Office records rather
than goblin-private records.

## Core record graph

The product is project-centered rather than a chain of isolated specialist
workflows.

`Business -> Client -> Project`

A Project may own or link:

`Agreement`
`Estimate`
`MaterialPlan`
`ShoppingListItem`
`Expense`
`WorkLog`
`ChangeOrder`
`Invoice`
`Payment`

The records are relational, not strictly linear. A project may have multiple
agreements, estimates, expenses, work logs, invoices, and payments. Expenses
can exist before a project assignment and can later be classified by Ledgergut
or Æterna.

The primary product lifecycle is defined in
`docs/product/golden-job-lifecycle.md`.

## Specialist responsibilities

- **Æterna** receives human intent, resolves context, routes work, exposes
  approvals, and keeps unresolved ambiguity visible.
- **SigNor** creates and manages Agreement and ChangeOrder records, including
  scope, assumptions, exclusions, pricing basis, and changes.
- **Packrat McDuffel** manages MaterialPlan and ShoppingListItem state, keeping
  required, acquired, substituted, returned, and remaining quantities distinct.
- **Ledgergut** creates and enriches Expense records from receipts and other
  evidence of spending and may propose matches against shopping-list items.
- **Patch** manages WorkLog and operational state, including factual labour,
  blockers, dependencies, changed scope, and completion evidence.
- **Squarmish** creates and manages Invoice records using agreed scope,
  completed work, actual labour, confirmed billable expenses, and approved
  changes.
- **Grimscratch** records risk/compliance flags and advisory holds without
  autonomously making legal or regulatory determinations.

## Estimate vs actual rule

Estimated and actual values are different facts and must never overwrite each
other.

Examples:
- estimated labour hours vs actual labour hours;
- expected material cost vs receipt-backed material cost;
- required material quantity vs acquired quantity;
- estimated project total vs invoiced / paid total.

System-derived estimates and material suggestions remain visibly derived until
a human confirms or promotes them.

## Receipt-to-shopping-list rule

Receipt evidence may update project material state only when the relationship is
clear enough to support it.

Ledgergut may suggest a match between a receipt line and a ShoppingListItem.
Clear matches can update acquired quantity and actual cost. Ambiguous matches
must remain pending human confirmation rather than silently changing project
state.

## Payment rule

Payments are Office records linked to invoices and projects.

The Office must support both:
- processor-backed payments when a configured provider is available;
- externally received / manually recorded payments.

No payment provider account, paid service, or financial commitment is activated
without explicit human authorization.

## Persistence boundary

Goblin workflows must not depend directly on JSON files, PostgreSQL, object
storage, payment processors, or any other persistence/integration technology.
They operate through shared domain and store interfaces.

This allows:

1. local/test storage without cloud dependencies;
2. PostgreSQL in production;
3. object storage for receipt/document binaries;
4. optional payment integrations;
5. migration without rewriting specialist business logic.

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
