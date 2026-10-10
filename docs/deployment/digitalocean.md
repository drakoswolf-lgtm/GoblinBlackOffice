# DigitalOcean private beta deployment

Target stack: DigitalOcean App Platform + managed PostgreSQL + Spaces.

## Pinned private-beta shape

- App Platform region: Toronto (`tor`)
- Web service: 1 shared vCPU / 1 GiB fixed container (`apps-s-1vcpu-1gb-fixed`)
- PostgreSQL region: Toronto (`tor1`), smallest managed single-node PostgreSQL plan
- Spaces region: Toronto (`tor1`), Standard Storage, private bucket
- App spec: `.do/app.yaml`
- Health check: `/health`

Expected base monthly cost at the current published rates:

- App Platform 1 GiB fixed container: US$10.00/month
- Managed PostgreSQL 1 GiB / 1 vCPU: US$15.15/month
- Spaces Standard subscription: US$5.00/month
- Expected base total: US$30.15/month before unusual excess transfer/storage

The app spec intentionally has `deploy_on_push: false` until database and secret configuration are complete. Do not enable automatic deploys before the release gate passes.

## Temporary zero-cost-data internal beta

For a first human smoke test, the existing App Platform service can run **without** managed PostgreSQL or Spaces. This mode is intentionally disposable:

- set `GBO_INTERNAL_SMOKE_TEST=1` and omit `DATABASE_URL` to explicitly permit a disposable, owner-only in-memory Black Office store;
- leave `SPACES_BUCKET`, `SPACES_ACCESS_KEY_ID`, and `SPACES_SECRET_ACCESS_KEY` unset to use local receipt-image storage;
- `SPACES_ENDPOINT_URL` / `SPACES_REGION` may remain present as future-storage metadata without forcing the S3 backend;
- set `WEB_CONCURRENCY=1` so every request reaches the same in-memory store;
- keep `GBO_AUTH_REQUIRED=1`, `GBO_SECRET`, and `GBO_INVITE_TOKEN` configured in production;
- data and locally stored receipt images may disappear on restart, rebuild, or redeploy.

This mode is suitable for an owner-operated walkthrough of splash → onboarding → job → receipt → labour → invoice → payment. It is **not** suitable for external beta users or any test where persistence is expected.

## Required application settings

Safe values are already present in `.do/app.yaml` where appropriate. The following must be injected as secrets or resource-specific values during provisioning:

- `GBO_SECRET=<long random secret>`
- `GBO_INVITE_TOKEN=<private beta invite code>`
- `DATABASE_URL=<managed PostgreSQL private connection string>`
- `SPACES_BUCKET=<private bucket name>`
- `SPACES_ACCESS_KEY_ID=<secret>`
- `SPACES_SECRET_ACCESS_KEY=<secret>`

`GBO_INVITE_TOKEN` is optional at the application level, but required for the private beta. When present, account creation refuses registrations without the matching invite code. Store it as an encrypted runtime value and rotate it if it is shared outside the intended beta group.

The spec supplies:

- `GBO_AUTH_REQUIRED=1`
- `GBO_ENV=production`
- `GBO_TRUST_PROXY_PROTO=1` (only on DigitalOcean App Platform's trusted ingress)
- `SPACES_REGION=tor1`
- `SPACES_ENDPOINT_URL=https://tor1.digitaloceanspaces.com`
- `WEB_CONCURRENCY=1` (owner-only ephemeral smoke, also safe with PostgreSQL)
- `WEB_THREADS=4`

`GBO_ENV=production` also enables same-origin protection for state-changing browser requests. POST/PUT/PATCH/DELETE requests must present same-origin `Origin`, `Referer`, or Fetch Metadata evidence; cross-site writes are rejected before application logic runs.

App Platform supplies `PORT` from the configured `http_port` (8080).

**HTTPS / POST regression:** DigitalOcean terminates TLS at ingress and forwards the original scheme in `X-Forwarded-Proto`, stripping client-supplied values. `GBO_TRUST_PROXY_PROTO=1` tells the Flask apps to trust only the forwarded scheme, not forwarded IP or Host. Without this setting, secure browser form submissions can be misidentified as cross-site (HTTPS Origin versus internal HTTP request). Do **not** enable this flag on a directly exposed Gunicorn server. Verify legitimate HTTPS POST succeeds and mismatched Origin is still rejected.

**Deployment guard:** when `GBO_ENV=production`, startup refuses disabled authentication, missing session secret, missing invite code, or missing `DATABASE_URL` unless the explicit owner-only smoke flag is set. In-memory mode refuses worker counts other than one. A production SQL connection must use PostgreSQL. These errors are intentional: a green health check must not disguise an exposed or split-brain beta.

Remove `GBO_INTERNAL_SMOKE_TEST` and configure managed PostgreSQL before admitting external testers. A successful internal smoke test does not establish persistence across redeployments.

## Provisioning order

1. Create the smallest managed PostgreSQL cluster in `tor1`.
2. Create a private Spaces Standard bucket in `tor1`.
3. Create a limited Spaces access key with read/write/delete access to that bucket only.
4. Create the App Platform app from `.do/app.yaml`.
5. Add `DATABASE_URL`, `GBO_SECRET`, `GBO_INVITE_TOKEN`, `SPACES_BUCKET`, `SPACES_ACCESS_KEY_ID`, and `SPACES_SECRET_ACCESS_KEY` as encrypted runtime values.
6. Deploy once. The application upgrades the connected database to the current Alembic schema revision before opening SQL-backed stores.
7. Complete the release gate below.
8. Only after the smoke tests pass, enable deploy-on-push for `main`.

## App Platform

Build from the repository `Dockerfile`. Health check path: `/health`.

The application must be HTTPS-only in beta because authenticated sessions use Secure cookies when `GBO_AUTH_REQUIRED=1`.

## PostgreSQL

Use managed PostgreSQL, not the App Platform development database. `DATABASE_URL` switches both the shared Black Office records and Ledgergut receipt archive to durable SQL storage.

Schema changes are versioned with Alembic. Both SQL store initializers call the migration runner before opening durable storage, so a fresh database is upgraded to the current head automatically. The initial revision creates `office_records`, `ledgergut_receipts`, their tenant indexes, and Alembic's own version table.

For an explicit operator-run migration, set `DATABASE_URL` and run `alembic -c alembic.ini upgrade head` from the project root. New schema changes must be added as revisions rather than reintroducing `metadata.create_all()` in production storage paths.

## Spaces

Keep the bucket private. Receipt images are stored beneath `receipts/<business_id>/...`. Do not make the bucket public merely to simplify preview URLs; signed retrieval can be added when the receipt-view surface needs it.

## Release gate

Before enabling beta users:

1. `/health` returns 200.
2. Registration rejects a wrong beta invite code and succeeds with the configured code.
3. Login works over HTTPS.
4. A cross-site POST to a state-changing route is rejected.
5. Confirm the PostgreSQL database reports the expected Alembic head revision.
6. Create a client and project.
7. Draft and confirm an agreement; verify PDF output.
8. Upload and save a receipt; restart/redeploy the app and confirm the receipt remains.
9. Draft and approve an invoice; verify PDF output and unresolved-tax warning.
10. Confirm one account cannot read another business's records.
