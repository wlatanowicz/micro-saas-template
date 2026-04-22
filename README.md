# Micro-SaaS template

Monorepo template for small SaaS products: **FastAPI** on **AWS Lambda** (HTTP API + **Mangum**), **SQLModel** + **Alembic** against an **existing database** (nothing provisioned in AWS for data), and a **Vite + React** SPA on **S3** + **CloudFront**. CI/CD mirrors the **water_meter**-style flow (Serverless v3, OIDC, S3 deploy, CloudFront invalidation, optional Cloudflare DNS).

## Layout

- `backend/` — Serverless stack, FastAPI app, Alembic migrations
- `frontend/` — React SPA (`VITE_API_BASE_URL` injected at build time)
- `scripts/` — Deploy frontend to S3 + invalidate CloudFront; invoke migration Lambda; optional Cloudflare CNAME update; **`collect-gha-env.sh`** builds **`.env.gha`** for GitHub Actions from AWS + prompts; **`push-gha-env.sh`** uploads **`.env.gha`** to repo Actions secrets/variables via **`gh`**

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python toolchain and lockfile-driven installs)
- Node.js 22+ and npm (Serverless CLI + frontend build)
- Python 3.11 (matches `serverless.yml` runtime; uv will install/use it via `setup-uv` in CI)
- AWS account; optional **ACM certificate in us-east-1** only if you use a **custom frontend hostname** on CloudFront
- PostgreSQL (or compatible) URL for `DATABASE_URL` if you use the API routes that touch the DB

## First-time checklist (new product from this template)

1. In `backend/serverless.yml`, set `service:` to your stack name prefix (default stack is `{service}-{stage}`).
2. Optional: set **`FRONTEND_DOMAIN_NAME`** and **`FRONTEND_ACM_CERT_ARN`** (us-east-1) together when deploying. The certificate’s SAN must include that hostname; otherwise CloudFront returns an invalid CNAME error. If you omit either, the stack uses the default **\*.cloudfront.net** URL only.
3. Set **`DATABASE_URL`** for deploy (GitHub secret and/or local env). The **migration** Lambda uses it to reach your database. For **private RDS**, set **`LAMBDA_VPC_SUBNET_IDS`** and **`LAMBDA_VPC_SECURITY_GROUP_IDS`** (comma-separated). **`collect-gha-env.sh`** fills both from the selected instance: subnets from the DB subnet group, security groups from **`VpcSecurityGroups`** (the same SGs the database already uses). Lambdas are placed in those SGs; add a **self-referencing inbound rule** on that SG for PostgreSQL (or allow the SG as source) if it does not already allow clients in the same group.
4. Copy `frontend/.env.example` to `frontend/.env` for local dev and set `VITE_API_BASE_URL` to your API URL (or local server).
5. Configure GitHub **Actions** secrets and variables (below). Grant the OIDC role **`lambda:InvokeFunction`** on the **`migrate`** function (see [docs/github-actions-aws-oidc.md](docs/github-actions-aws-oidc.md)).

## Local backend

Dependencies live in [`backend/pyproject.toml`](backend/pyproject.toml) and [`backend/uv.lock`](backend/uv.lock). Runtime deps include **Alembic** (used by the **`migrate`** Lambda). Test tooling stays in the **dev** dependency group.

```bash
cd backend
uv sync --all-groups
export DATABASE_URL='postgresql://user:pass@host:5432/dbname'   # optional for /api/items
uv run pytest
uv run ruff check src tests
PYTHONPATH=. uv run uvicorn src.main:app --reload --port 8000
```

## Database migrations

**Deploy workflow:** after `serverless deploy`, GitHub Actions runs **`scripts/invoke-migrate-lambda.sh`**, which invokes the **`migrate`** Lambda. That function runs **`alembic upgrade head`** programmatically (`command.upgrade`). The stack output **`MigrateLambdaName`** is the function to call.

**Local / manual:**

```bash
cd backend
uv sync --all-groups
export DATABASE_URL='postgresql://...'
uv run alembic upgrade head
```

After a successful deploy (CLI), from repo root:

```bash
bash scripts/invoke-migrate-lambda.sh prod eu-central-1
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
# Optional: private RDS — same subnets + SGs as the RDS instance (from collect-gha-env or by hand):
# export LAMBDA_VPC_SUBNET_IDS='subnet-aaa,subnet-bbb'
# export LAMBDA_VPC_SECURITY_GROUP_IDS='sg-rds...'
# export RDS_VPC_ID='vpc-...'   # optional; informational in .env.gha
# Optional custom SPA hostname (set BOTH, cert must cover the hostname in us-east-1):
# export FRONTEND_ACM_CERT_ARN='arn:aws:acm:us-east-1:...:certificate/...'
# export FRONTEND_DOMAIN_NAME='app.yourdomain.com'
npx serverless@3 deploy --stage prod --region eu-central-1
```

Or use `npm run deploy` from `backend/`, which runs **`predeploy`** and regenerates `requirements-lambda.txt` automatically.

For **VPC Lambdas**, set subnets and security groups in **`backend/lambda-vpc.config.json`** (copy **`backend/lambda-vpc.config.example.json`**). **`backend/serverless.yml`** uses **`provider.vpc: ${file(./lambda-vpc.config.json), file(./lambda-vpc.no-vpc.json)}`**: if the config file is missing, **`lambda-vpc.no-vpc.json`** is the boolean **`false`**, which turns VPC off (Serverless previously dropped **`VpcConfig`** when a resolver returned **`{}`**, because **`SubnetIds` / `SecurityGroupIds`** were undefined). Alternatively, replace that **`provider.vpc`** line with a **literal** YAML block (`subnetIds` / `securityGroupIds` lists); comma-separated strings in env cannot become YAML lists without a script or plugin.

In **GitHub Actions**, set **`LAMBDA_VPC_SUBNET_IDS`** and **`LAMBDA_VPC_SECURITY_GROUP_IDS`** as **Variables** or **Secrets** (comma-separated); **Deploy** runs **`node scripts/write-lambda-vpc-config.js`**, which writes or deletes **`lambda-vpc.config.json`**. Check the **Materialize Lambda VPC config** log (**Wrote …** vs **No backend/…**).

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

Runs on pushes to `main` and on `workflow_dispatch`: deploy backend → **run migrations Lambda** → deploy frontend → optional Cloudflare DNS.

| Type | Name | Purpose |
|------|------|---------|
| Secret | `AWS_ROLE_TO_ASSUME` | IAM role ARN for OIDC (`sts:AssumeRoleWithWebIdentity` from GitHub) |
| Secret | `DATABASE_URL` | Passed to Lambdas (`api`, **`migrate`**). Required for migration step if the database should be updated on deploy. |
| Secret | `FRONTEND_ACM_CERT_ARN` | Optional; ACM cert ARN (us-east-1). Required with `FRONTEND_DOMAIN_NAME` if you use a custom SPA domain. |
| Variable | `AWS_REGION` | Optional; default `eu-central-1` |
| Variable | `FRONTEND_DOMAIN_NAME` | Optional; custom SPA hostname. Use with `FRONTEND_ACM_CERT_ARN`; leave unset for default CloudFront URL only. |
| Variable | `RDS_VPC_ID` | Optional; informational (VPC of the RDS subnet group). Not read by Serverless. |
| Variable or secret | `LAMBDA_VPC_SUBNET_IDS` | Optional; comma-separated subnet ids for Lambdas in a VPC (same subnets as RDS). Variables take precedence over a secret with the same name. |
| Variable or secret | `LAMBDA_VPC_SECURITY_GROUP_IDS` | Optional; comma-separated security group ids—typically the **same** SGs attached to the RDS instance (`collect-gha-env.sh` fills this from **`VpcSecurityGroups`**). |
| Secret | `CLOUDFLARE_API_TOKEN` | Optional; DNS:Edit for zone |
| Secret | `CLOUDFLARE_ZONE_ID` | Optional; or use `CLOUDFLARE_ZONE_NAME` |
| Secret | `CLOUDFLARE_ZONE_NAME` | Optional; e.g. `example.com` |

OIDC trust and IAM permissions for deploy are documented in **[docs/github-actions-aws-oidc.md](docs/github-actions-aws-oidc.md)**.

### Bootstrap GitHub secrets from AWS

With credentials available (e.g. **`AWS_PROFILE`**), run:

```bash
AWS_PROFILE=your-profile ./scripts/collect-gha-env.sh
```

The script prints **`sts get-caller-identity`**, lists **RDS** instances in the configured region (endpoint, identifier) and **ISSUED ACM** certs in **us-east-1**, and prompts for **database name**, **password**, **OIDC role ARN**, optional **frontend domain** / **Cloudflare** values. When you build **`DATABASE_URL`** from an RDS instance, it fills **`RDS_VPC_ID`**, **`LAMBDA_VPC_SUBNET_IDS`**, and **`LAMBDA_VPC_SECURITY_GROUP_IDS`** (all RDS **`VpcSecurityGroups`**). It writes **`.env.gha`** at the repo root (gitignored) with **`shlex`-safe** quoting. If **`.env.gha` already exists**, its values are loaded first and used as defaults (press **Enter** to keep each field, **`k`** to keep **DATABASE_URL** / ACM). Use **`./scripts/collect-gha-env.sh -n`** to print the file to stdout only.

Requires **AWS CLI**, **jq**, and **Python 3**. The generated **`.env.gha`** uses **`# --- Secrets ---`** and **`# --- Variables ---`** section headers; **`push-gha-env.sh`** uploads every non-empty line under each block to GitHub **secrets** or **variables**. Run **`./scripts/push-gha-env.sh`** (needs **`gh`** and **Python 3**; **`gh`** with **repo** scope). Use **`./scripts/push-gha-env.sh -n`** first to preview. The **master password** and **OIDC role ARN** are always prompted (not returned by AWS APIs).

Optional custom CloudFront hostname is controlled only by environment variables **`FRONTEND_DOMAIN_NAME`** and **`FRONTEND_ACM_CERT_ARN`** (both required together). The deploy workflow passes the repository variable `FRONTEND_DOMAIN_NAME` when set.

## Lambda packaging notes

- **uv** produces `backend/requirements-lambda.txt` for **`serverless-python-requirements`** (`uv export --frozen --no-dev --no-emit-project --no-hashes`). That file is gitignored; CI and `npm run predeploy` create it before deploy. **`package.individually: true`**: the **`api`** function excludes `alembic/` and **`migrate_handler.py`**; the **`migrate`** function ships `alembic/` + `alembic.ini` plus app models. Both bundles still include shared runtime wheels (including Alembic) from the same export.
- `serverless-python-requirements` bundles those dependencies; `slim: true` keeps the zip smaller. On macOS, `dockerizePip: non-linux` uses Docker for Linux-compatible wheels when needed.
- Lambda runtime already includes `boto3`; it is listed under `noDeploy` to avoid duplication.

After changing Python dependencies, run **`uv lock`** in `backend/` and commit the updated **`uv.lock`**.

GitHub Actions installs **Python via `actions/setup-python`** before **`setup-uv`**, because **`serverless-python-requirements`** shells out to **`python3.11 -m pip`**, and uv’s standalone interpreters may not ship with the `pip` module.

## License

Use freely for your own products; add a license file if you open-source the template.
