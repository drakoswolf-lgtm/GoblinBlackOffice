# Scroll 001 — The Living Codex

> **Status:** Active — Working Reference
> **Last Updated:** 2026-07-06

---

The Living Codex is the master index of Goblin Black Office: its agents,
documents, and the canonical links between them.  It is a living document and
should be updated whenever a new goblin, workflow, or foundational scroll is
added.

---

## Registered Goblins

| ID | Display Name | Department | Status | Canonical Document |
|----|--------------|-----------|--------|-------------------|
| `aeterna_skyeward` | Æterna SkyeWard | Architecture & Strategy | Planned | [Character Bible](02-character-bible.md) |
| `ledgergut` | Ledgergut | Finance & Records | Draft | [GBO-001](../goblins/GBO-001-ledgergut-workflow.md) |
| `squarmish` | Squarmish | Billing & Revenue | Draft | [GBO-002](../goblins/GBO-002-squarmish-invoice-workflow.md) |
| `signor` | SigNor the Immutable | Contracts & Governance | Planned | [Scroll 005](05-department-head-character-bible.md) |
| `packrat_mcduffel` | Packrat McDuffel | Logistics & Planning | Planned | [Scroll 005](05-department-head-character-bible.md) |
| `patch` | Patch | Operations & Engineering | Planned | [Scroll 005](05-department-head-character-bible.md) |
| `grimscratch` | Grimscratch | Compliance & Risk | Planned | [Scroll 005](05-department-head-character-bible.md) |

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
| [Scroll 005 — Department Head Character Bible](05-department-head-character-bible.md) | Canonical personalities, visual identities, and philosophies for Department Heads |
| [Scroll 006 — Specialists of the Black Office](06-specialists-of-the-black-office.md) | Canonical identities, speech patterns, and philosophy for Specialists |

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
- Specialists are documented in [Scroll 006](06-specialists-of-the-black-office.md)
  as first-class canon, but they remain outside the registered goblin table
  and the department registry.
- No API endpoints are exposed in the current version.
- No AI orchestration is wired up in the current version.
- Each goblin's `canonical_doc_path` points to the most specific
  reference document available for that agent.
