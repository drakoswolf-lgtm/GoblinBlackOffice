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
- `SPACES_REGION=tor1`
- `SPACES_ENDPOINT_URL=https://tor1.digitaloceanspaces.com`
- `WEB_CONCURRENCY=2`
- `WEB_THREADS=4`

`GBO_ENV=production` also enables same-origin protection for state-changing browser requests. POST/PUT/PATCH/DELETE requests must present same-origin `Origin`, `Referer`, or Fetch Metadata evidence; cross-site writes are rejected before application logic runs.

App Platform supplies `PORT` from the configured `http_port` (8080).

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
