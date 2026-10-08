# Goblin Black Office Ship Checklist

**Status:** living checklist for clickable beta and private-beta launch.

## Foundation

- [x] Core application architecture
- [x] Authentication / onboarding foundation
- [x] Office Desk
- [x] Ledgergut core workflow
- [x] SigNor core workflow
- [x] Squarmish core workflow
- [x] Shared client / project records
- [x] Human approval states
- [x] Agreement and invoice PDF generation
- [x] SQL persistence
- [x] Alembic migrations
- [x] Private receipt image retrieval
- [x] Production same-origin write protection
- [x] Private-beta invite gating
- [x] Unified Black Office UI foundation

## Canon / brand

- [x] Visual canon documented
- [x] UX model documented
- [x] G4 startup-charge canon documented
- [x] Startup charge keyframe approved
- [x] Closed access door approved
- [x] Correct split-logo opening door approved
- [x] Æterna command portrait approved
- [x] Æterna straight-on advice portrait approved
- [x] App badge approved
- [x] Canon image library stored under `resources/canon/`
- [x] Superseded doubled-logo door excluded
- [x] Canon approval gate established for future image / UI work

## Clickable experience

- [x] Canon assets served by the app
- [x] Splash shell mounted
- [x] LOADING / UPDATING runtime state
- [x] Minimum 5-second presentation
- [x] Load-bearing sticky joke rotation
- [x] Progress-linked charge intensity
- [x] Aquamarine breach transition
- [x] Graphite access-door reveal
- [x] Correct split-logo opening state
- [x] White-flash entry transition
- [x] Returning-user splash into Office Desk
- [x] First-run splash into setup
- [x] Persistent Æterna advice box on Office Desk
- [x] Æterna cobalt/cyan command styling
- [x] Æterna open / close interaction
- [x] Curriculum VitÆ UI canon defined and approved
- [x] Holographic-first Curriculum canon supersedes paper-dossier onboarding
- [x] Curriculum VitÆ onboarding implementation
- [ ] Æterna persistent presence across specialist screens
- [ ] Specialist card / navigation final click-through smoke pass
- [ ] Mobile visual pass on phone-sized viewport
- [ ] Touch-target / overflow check
- [ ] Refresh / return-visit splash behavior check

## Golden job lifecycle

Canonical acceptance path: `docs/product/golden-job-lifecycle.md`.

- [x] Shared Client / Project records
- [x] SigNor Agreement draft
- [x] Ledgergut receipt / Expense foundation
- [x] Squarmish Invoice draft from Agreement + billable Expense
- [x] Agreement / invoice printable PDF foundation
- [x] One-click Office Desk `New job` path
- [x] Connected project workbench for planning, receipts, labour, invoicing, payments, and ledger
- [x] Estimate domain model and persistence
- [ ] Scope-to-editable-estimate service
- [x] MaterialPlan domain model and persistence
- [ ] Scope-to-editable-material-plan service
- [x] Packrat ShoppingListItem domain implementation
- [x] Promote approved material plan into shopping list
- [x] Receipt-line to shopping-list matching
- [x] Real-time acquired / remaining shopping-list state
- [x] Patch WorkLog domain implementation
- [x] Actual labour capture
- [ ] Estimate-vs-actual project view
- [x] ChangeOrder domain implementation / SigNor handoff
- [x] Squarmish invoice from actual labour + confirmed expenses + approved changes
- [ ] Invoice issue / sent state with explicit human approval
- [ ] Outbound email integration
- [x] Payment domain model and manual payment recording
- [ ] Optional Square payment integration
- [x] Paid / partially-paid invoice state
- [x] Running project / business ledger update from payments
- [x] Full end-to-end golden-path automated test
- [ ] Full end-to-end human smoke test in live dev app

## EOD demo gate

- [x] Demo branch created
- [x] Canon resources committed to demo branch
- [x] Draft demo PR opened
- [x] CI green on current code-bearing head
- [ ] Human visual / canon review
- [ ] Mark PR ready
- [ ] Merge clickable build
- [ ] Redeploy existing DigitalOcean app
- [ ] Live smoke test

## Private-beta infrastructure

- [ ] Toronto Managed PostgreSQL
- [ ] Toronto private Spaces bucket
- [ ] Scoped Spaces key
- [ ] Production env / encrypted secrets
- [ ] Redeploy against managed services
- [ ] Persistence smoke test across restart
- [ ] Tenant-isolation smoke test
- [ ] Backup / restore notes
- [ ] Logging / error-reporting review

## Broader launch hardening

- [ ] Password reset
- [ ] Email verification
- [ ] Durable login rate limiting / lockout
- [ ] Multi-user / team roles
- [ ] Agreements: explicit client acceptance workflow
- [ ] Invoices: explicit sent state
- [ ] Payments / processor integration
- [ ] Outbound email
- [ ] Tax configuration
- [ ] Custom domain
- [ ] Production security-header review

## Rule

New images and new UI elements are **pending canon** until explicitly approved. Exploratory work does not enter the canon resource library or production UI until that approval is given.
