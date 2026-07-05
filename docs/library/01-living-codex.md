# Scroll 001 — The Living Codex

> **Status:** Active — Working Reference
> **Last Updated:** 2026-07-05

---

The Living Codex is the master index of Goblin Black Office: its agents,
documents, and the canonical links between them.  It is a living document and
should be updated whenever a new goblin, workflow, or foundational scroll is
added.

---

## Registered Goblins

| ID | Display Name | Department | Status | Canonical Document |
|----|--------------|-----------|--------|-------------------|
| `aeterna_skyeward` | Aeterna Skyeward | Scheduling & Planning | Planned | [Character Bible](02-character-bible.md) |
| `ledgergut` | Ledgergut | Finance & Accounting | Draft | [GBO-001](../goblins/GBO-001-ledgergut-workflow.md) |
| `squarmish` | Squarmish | Finance & Invoicing | Draft | [GBO-002](../goblins/GBO-002-squarmish-invoice-workflow.md) |
| `signor` | Signor | Document Management | Planned | [Character Bible](02-character-bible.md) |
| `packrat_mcduffel` | Packrat McDuffel | Records & Storage | Planned | [Character Bible](02-character-bible.md) |
| `patch` | Patch | Operations | Planned | [Character Bible](02-character-bible.md) |
| `grimscratch` | Grimscratch | Audit & Compliance | Planned | [Character Bible](02-character-bible.md) |

The authoritative source for this table is `app/core/goblin_registry.py`.

---

## Workflow Documents

| Scroll | Agent | Status |
|--------|-------|--------|
| [GBO-001: Ledgergut Receipt Intelligence Workflow](../goblins/GBO-001-ledgergut-workflow.md) | Ledgergut | Draft v0.2 |
| [GBO-002: Squarmish Invoice Workflow](../goblins/GBO-002-squarmish-invoice-workflow.md) | Squarmish | Draft v0.1 |

---

## Library Documents

| Document | Purpose |
|----------|---------|
| [Scroll 001 — Living Codex](01-living-codex.md) | Master index of agents, scrolls, and documents (this file) |
| [Scroll 002 — Character Bible](02-character-bible.md) | Canonical character and role definitions for all goblins |

---

## Status Definitions

| Status | Meaning |
|--------|---------|
| `planned` | Goblin is defined and registered; no workflow document or implementation yet |
| `draft` | Workflow document exists; no production code yet |
| `active` | Implementation is live and in use |
| `retired` | Goblin has been decommissioned |

---

## Architecture Notes

- The goblin registry (`app/core/goblin_registry.py`) is the canonical
  source of truth for all agent identifiers, departments, and ownership.
- No API endpoints are exposed in the current version.
- No AI orchestration is wired up in the current version.
- Each goblin's `canonical_doc_path` points to the most specific
  reference document available for that agent.
