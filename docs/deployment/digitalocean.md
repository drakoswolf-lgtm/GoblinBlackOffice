# DigitalOcean private beta deployment

Target stack: DigitalOcean App Platform + managed PostgreSQL + Spaces.

## Required application settings

- `GBO_AUTH_REQUIRED=1`
- `GBO_SECRET=<long random secret>`
- `DATABASE_URL=<managed PostgreSQL connection string>`
- `SPACES_ENDPOINT_URL=<regional Spaces endpoint, e.g. https://sfo3.digitaloceanspaces.com>`
- `SPACES_BUCKET=<private bucket name>`
- `SPACES_ACCESS_KEY_ID=<secret>`
- `SPACES_SECRET_ACCESS_KEY=<secret>`
- `SPACES_REGION=<region slug>`
- `PORT=8080` (App Platform normally supplies this)

Optional tuning:

- `WEB_CONCURRENCY=2`
- `WEB_THREADS=4`

## App Platform

Build from the repository `Dockerfile`. Health check path: `/health`.

The application must be HTTPS-only in beta because authenticated sessions use Secure cookies when `GBO_AUTH_REQUIRED=1`.

## PostgreSQL

Use managed PostgreSQL, not the App Platform development database. `DATABASE_URL` switches both the shared Black Office records and Ledgergut receipt archive to durable SQL storage.

Current schema creation uses SQLAlchemy `metadata.create_all()`. Before public/commercial launch, replace this transitional behavior with managed migrations (Alembic or equivalent).

## Spaces

Keep the bucket private. Receipt images are stored beneath `receipts/<business_id>/...`. Do not make the bucket public merely to simplify preview URLs; signed retrieval can be added when the receipt-view surface needs it.

## Release gate

Before enabling beta users:

1. `/health` returns 200.
2. Registration and login work over HTTPS.
3. Create a client and project.
4. Draft and confirm an agreement; verify PDF output.
5. Upload and save a receipt; restart/redeploy the app and confirm the receipt remains.
6. Draft and approve an invoice; verify PDF output and unresolved-tax warning.
7. Confirm one account cannot read another business's records.
