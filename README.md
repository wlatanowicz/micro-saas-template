# Micro-SaaS template

Monorepo template for small SaaS products: **FastAPI** on **AWS Lambda** (HTTP API + **Mangum**), **SQLModel** + **Alembic** against an **existing database** (nothing provisioned in AWS for data), and a **Vite + React** SPA on **S3** + **CloudFront**. CI/CD mirrors the **water_meter**-style flow (Serverless v3, OIDC, S3 deploy, CloudFront invalidation, optional Cloudflare DNS).

## Layout

- `backend/` — Serverless stack, FastAPI app, Alembic migrations
- `frontend/` — React SPA (`VITE_API_BASE_URL` injected at build time)
- `scripts/` — Deploy frontend to S3 + invalidate CloudFront; optional Cloudflare CNAME update

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python toolchain and lockfile-driven installs)
- Node.js 22+ and npm (Serverless CLI + frontend build)
- Python 3.11 (matches `serverless.yml` runtime; uv will install/use it via `setup-uv` in CI)
- AWS account, ACM certificate in **us-east-1** for the CloudFront custom hostname
- PostgreSQL (or compatible) URL for `DATABASE_URL` if you use the API routes that touch the DB

## First-time checklist (new product from this template)

1. In `backend/serverless.yml`, set `service:` to your stack name prefix (default stack is `{service}-{stage}`).
2. Set `custom.frontendDomainNames` (or override with env `FRONTEND_DOMAIN_NAME` on deploy).
3. Set a real `FRONTEND_ACM_CERT_ARN` (us-east-1) when deploying; the placeholder ARN in the file will not work in AWS.
4. Copy `frontend/.env.example` to `frontend/.env` for local dev and set `VITE_API_BASE_URL` to your API URL (or local server).
5. Configure GitHub **Actions** secrets and variables (below).

## Local backend

Dependencies live in [`backend/pyproject.toml`](backend/pyproject.toml) and [`backend/uv.lock`](backend/uv.lock). Runtime third-party deps are the `[project]` section; **Alembic** and test tooling are in the **dev** group (not bundled into Lambda).

```bash
cd backend
uv sync --all-groups
export DATABASE_URL='postgresql://user:pass@host:5432/dbname'   # optional for /api/items
uv run pytest
uv run ruff check src tests
PYTHONPATH=. uv run uvicorn src.main:app --reload --port 8000
```

## Database migrations

Migrations are **not** applied automatically in deploy (to avoid surprising a shared database).

```bash
cd backend
uv sync --all-groups
export DATABASE_URL='postgresql://...'
uv run alembic upgrade head
```

For a new migration after changing models:

```bash
uv run alembic revision --autogenerate -m "describe change"
```

## Local frontend

```bash
cd frontend
npm install
cp .env.example .env
# set VITE_API_BASE_URL=http://127.0.0.1:8000 in .env
npm run dev
```

## Deploy (CLI)

From `backend/` (requires AWS credentials and env vars as in CI):

```bash
npm ci
uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements-lambda.txt
export DATABASE_URL='postgresql://...'
export FRONTEND_ACM_CERT_ARN='arn:aws:acm:us-east-1:...:certificate/...'
export FRONTEND_DOMAIN_NAME='app.yourdomain.com'   # optional if defaults in serverless.yml are fine
npx serverless@3 deploy --stage prod --region eu-central-1
```

Or use `npm run deploy` from `backend/`, which runs **`predeploy`** and regenerates `requirements-lambda.txt` automatically.

Then from repo root:

```bash
bash scripts/deploy-frontend.sh prod eu-central-1
bash scripts/update-cloudflare-frontend-cname.sh prod eu-central-1   # if Cloudflare token + zone are set
```

Scripts accept an optional third argument: **CloudFormation stack name** (default `{service}-{stage}` from `backend/serverless.yml`).

## GitHub Actions

### `CI` (`.github/workflows/ci.yml`)

Runs on every push and pull request: **uv** (`uv sync`, tests, Ruff), exports `requirements-lambda.txt`, Serverless `print`, frontend build.

### `Deploy` (`.github/workflows/deploy.yml`)

Runs on pushes to `main` and on `workflow_dispatch`.

| Type | Name | Purpose |
|------|------|---------|
| Secret | `AWS_ROLE_TO_ASSUME` | IAM role ARN for OIDC (`sts:AssumeRoleWithWebIdentity` from GitHub) |
| Secret | `DATABASE_URL` | Passed to Lambda as `DATABASE_URL` |
| Secret | `FRONTEND_ACM_CERT_ARN` | ACM cert ARN (us-east-1) for CloudFront |
| Variable | `AWS_REGION` | Optional; default `eu-central-1` |
| Secret | `CLOUDFLARE_API_TOKEN` | Optional; DNS:Edit for zone |
| Secret | `CLOUDFLARE_ZONE_ID` | Optional; or use `CLOUDFLARE_ZONE_NAME` |
| Secret | `CLOUDFLARE_ZONE_NAME` | Optional; e.g. `example.com` |

OIDC trust and IAM permissions for deploy are documented in **[docs/github-actions-aws-oidc.md](docs/github-actions-aws-oidc.md)**.

Set the CloudFront **hostname** in `backend/serverless.yml` (`custom.frontendDomainNames` / `FRONTEND_DOMAIN_NAME` when exporting for a manual deploy). The deploy workflow does not set `FRONTEND_DOMAIN_NAME` by default so an empty GitHub variable cannot override your file defaults.

## Lambda packaging notes

- **uv** produces `backend/requirements-lambda.txt` for **`serverless-python-requirements`** (`uv export --frozen --no-dev --no-emit-project --no-hashes`). That file is gitignored; CI and `npm run predeploy` create it before deploy. Application code is packaged by Serverless separately; the export lists only third-party runtime deps (Alembic stays in the dev group only).
- `serverless-python-requirements` bundles those dependencies; `slim: true` keeps the zip smaller. On macOS, `dockerizePip: non-linux` uses Docker for Linux-compatible wheels when needed.
- Lambda runtime already includes `boto3`; it is listed under `noDeploy` to avoid duplication.

After changing Python dependencies, run **`uv lock`** in `backend/` and commit the updated **`uv.lock`**.

GitHub Actions installs **Python via `actions/setup-python`** before **`setup-uv`**, because **`serverless-python-requirements`** shells out to **`python3.11 -m pip`**, and uv’s standalone interpreters may not ship with the `pip` module.

## License

Use freely for your own products; add a license file if you open-source the template.
