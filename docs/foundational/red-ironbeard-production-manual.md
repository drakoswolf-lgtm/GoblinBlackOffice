# Red Ironbeard's Production Manual

> **Status:** Canonical — Active  
> **Document Owner:** Red Ironbeard (Production Foreman)  
> **Last Updated:** 2026-07-05  
> **Classification:** Instructional (defines how to build)

---

## 1. Project Architecture

Build and change work must preserve this documentation-first structure:

- `README.md` is the entrypoint.
- `docs/foundational/` holds canonical governance documents.
- `docs/goblins/` holds workflow scrolls.
- New implementation code must be organized to mirror scroll boundaries.

## 2. Folder Conventions

- Foundational canon: `docs/foundational/`
- Scroll specs: `docs/goblins/`
- Future chronicles: `docs/chronicles/` (create when first chronicle is added)
- Avoid duplicate canonical definitions across files.

## 3. Naming Conventions

- Scroll files: `GBO-###-slug.md`
- Canonical docs: lowercase kebab-case filenames
- New goblin IDs must remain stable after first publication.

## 4. Coding Standards

- Keep changes small and scoped to the intended behavior.
- Prefer clear domain names that match codified terminology.
- Avoid hardcoded collar assumptions in shared logic.

## 5. Testing Requirements

- If test tooling exists, run it before and after changes.
- For doc-only changes, verify internal links and section consistency.
- New feature work must include validation steps in PR notes.

## 6. Review Checklist

- Canonical references updated?
- Scope limited to requested change?
- Terminology aligned with Codex?
- Character-impacting changes aligned with Character Bible?
- Security, performance, and migration impacts noted?

## 7. Acceptance Criteria

No feature is complete unless:

1. Behavior/spec change is implemented or documented.
2. At least one canonical document is updated.
3. Review checklist items are satisfied.

## 8. Migration Rules

- Preserve existing scroll IDs and canonical entity names.
- Any schema/shape change must include compatibility notes.
- Document deprecations before removals.

## 9. Branch Strategy

- One branch per scroll or tightly related unit of work.
- Keep branches short-lived and rebased/updated frequently.
- Do not mix unrelated features in one branch.

## 10. Commit Message Conventions

- Format: `<scope>: <imperative summary>`
- Examples: `docs: add foundational codex`, `workflow: revise squarmish tax notes`
- Keep messages explicit about changed canonical surface.

## 11. Pull Request Template

Every PR description should include:

1. **Summary**
2. **Scroll/Feature Scope**
3. **Canonical Docs Updated**
4. **Validation Performed**
5. **Risks / Follow-ups**

## 12. Scroll Implementation Workflow

1. Read applicable Foundational Scrolls first.
2. Define delta in a single scroll-focused change set.
3. Update implementation/spec content.
4. Update at least one canonical document.
5. Validate and open for review.

Future scrolls must reference Foundational Scrolls for canonical definitions instead of duplicating those definitions.

## 13. Definition of Done

Done means all are true:

- Requested scope implemented.
- Canonical documentation updated.
- Validation completed.
- Review passed with no unresolved blocking issues.

## 14. Performance Expectations

- Favor data structures and flows that scale with increased workflow volume.
- Document known bottlenecks as they are discovered.
- Avoid unnecessary repeated processing in core flows.

## 15. Security Expectations

- No secrets in repository content.
- Validate external input assumptions in design and code.
- Record security-relevant decisions in canonical docs when they change behavior.

## 16. Documentation Requirements

- Architecture changes update the Codex.
- Character changes update the Character Bible.
- Engineering/process changes update this Production Manual.
- Every merged feature updates at least one canonical document.

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-05 | Established baseline production standards for Goblin Black Office. |
