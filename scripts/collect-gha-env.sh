#!/usr/bin/env bash
# Build .env.gha from AWS (AWS_PROFILE) + interactive prompts for GitHub Actions secrets/variables.
# Usage: AWS_PROFILE=my-prof ./scripts/collect-gha-env.sh
# Options: -n  print to stdout only (do not write .env.gha)
#          -h  help
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_FILE="${REPO_ROOT}/.env.gha"
DRY_RUN=false

while getopts "nh" opt; do
  case "$opt" in
    n) DRY_RUN=true ;;
    h)
      echo "Usage: AWS_PROFILE=... $0 [-n] [-h]"
      echo "  -n  dry-run: print env file to stdout, do not write ${OUT_FILE}"
      echo "  -h  help"
      exit 0
      ;;
    *) exit 2 ;;
  esac
done

for cmd in aws jq python3; do
  command -v "$cmd" >/dev/null || {
    echo "Missing required command: $cmd" >&2
    exit 1
  }
done

load_existing_env_gha() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  echo "Loading defaults from existing ${f}"
  # shellcheck disable=SC1090
  source /dev/stdin <<<"$(python3 - "$f" <<'PY'
import pathlib
import re
import shlex
import sys

p = pathlib.Path(sys.argv[1])
key_ok = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
out = []
for raw in p.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    if "=" not in line:
        continue
    k, _, v = line.partition("=")
    k = k.strip()
    if not key_ok.match(k):
        continue
    v = v.strip()
    if not v:
        out.append(f"export {k}=''")
        continue
    try:
        parts = shlex.split(v, posix=True)
        val = parts[0] if parts else ""
    except ValueError:
        val = ""
    out.append(f"export {k}={shlex.quote(val)}")
print("\n".join(out))
PY
)"
}

load_existing_env_gha "$OUT_FILE"

if [[ -n "${AWS_PROFILE:-}" ]]; then
  export AWS_PROFILE
  echo "Using AWS_PROFILE=${AWS_PROFILE}"
else
  echo "AWS_PROFILE is not set; using default credential chain." >&2
fi

echo "Caller identity:"
aws sts get-caller-identity --output table || {
  echo "AWS credentials failed. Set AWS_PROFILE or configure credentials." >&2
  exit 1
}

PROFILE_ARGS=()
if [[ -n "${AWS_PROFILE:-}" ]]; then
  PROFILE_ARGS=(--profile "$AWS_PROFILE")
fi

REGION="${AWS_REGION:-}"
if [[ -z "${REGION}" ]]; then
  REGION="$(aws configure get region "${PROFILE_ARGS[@]}" 2>/dev/null | tr -d '\r' || true)"
fi
if [[ -z "${REGION}" ]]; then
  read -rp "AWS region for RDS / deploy (e.g. eu-central-1): " REGION
fi
REGION="${REGION:-eu-central-1}"

build_database_url_from_rds() {
  local identifier="$1"
  local dbname="$2"
  local json
  json="$(aws rds describe-db-instances "${PROFILE_ARGS[@]}" --region "$REGION" \
    --db-instance-identifier "$identifier" --output json)"
  local addr port user engine
  addr="$(jq -r '.DBInstances[0].Endpoint.Address' <<< "$json")"
  port="$(jq -r '.DBInstances[0].Endpoint.Port' <<< "$json")"
  user="$(jq -r '.DBInstances[0].MasterUsername' <<< "$json")"
  engine="$(jq -r '.DBInstances[0].Engine' <<< "$json")"
  if [[ "$engine" != postgres* ]]; then
    echo "Warning: engine is ${engine}; this template expects PostgreSQL. Adjust DATABASE_URL manually if needed." >&2
  fi
  export _COLLECT_DB_USER="$user"
  export _COLLECT_DB_ADDR="$addr"
  export _COLLECT_DB_PORT="$port"
  export _COLLECT_DB_NAME="$dbname"
  python3 -c "
from urllib.parse import quote
import os
user = quote(os.environ['_COLLECT_DB_USER'], safe='')
password = quote(os.environ['_COLLECT_DB_PASS'], safe='')
dbname = quote(os.environ['_COLLECT_DB_NAME'], safe='')
addr = os.environ['_COLLECT_DB_ADDR']
port = os.environ['_COLLECT_DB_PORT']
print(f'postgresql://{user}:{password}@{addr}:{port}/{dbname}')
"
  unset _COLLECT_DB_USER _COLLECT_DB_ADDR _COLLECT_DB_PORT _COLLECT_DB_NAME
}

: "${DATABASE_URL:=}"

echo ""
echo "=== DATABASE_URL ==="
SKIP_DB_WIZARD=false
if [[ -n "${DATABASE_URL}" ]]; then
  echo "DATABASE_URL already set (${#DATABASE_URL} characters from .env.gha)."
  read -rp "Keep [k], rebuild from RDS [r], or manual URL [m] [k]: " db_choice
  db_choice="${db_choice:-k}"
  case "${db_choice}" in
    r | R) SKIP_DB_WIZARD=false ;;
    m | M)
      read -rp "DATABASE_URL [Enter to keep current]: " NEW_DB_URL
      DATABASE_URL="${NEW_DB_URL:-$DATABASE_URL}"
      SKIP_DB_WIZARD=true
      ;;
    *)
      SKIP_DB_WIZARD=true
      ;;
  esac
fi

if ! $SKIP_DB_WIZARD; then
  RDS_JSON="$(aws rds describe-db-instances "${PROFILE_ARGS[@]}" --region "$REGION" --output json 2>/dev/null || echo '{"DBInstances":[]}')"
  RDS_COUNT="$(jq '.DBInstances | length' <<< "$RDS_JSON")"

  if [[ "$RDS_COUNT" -eq 0 ]]; then
    echo "No RDS instances in ${REGION}."
    read -rp "Paste DATABASE_URL [Enter to keep existing / leave unchanged]: " NEW_DB_URL
    DATABASE_URL="${NEW_DB_URL:-$DATABASE_URL}"
  else
    echo "RDS instances in ${REGION}:"
    RDS_IDS=()
    while IFS= read -r line; do
      [[ -n "$line" ]] && RDS_IDS+=("$line")
    done < <(jq -r '.DBInstances[].DBInstanceIdentifier' <<< "$RDS_JSON")
    for ((idx = 0; idx < ${#RDS_IDS[@]}; idx++)); do
      ep="$(jq -r --arg id "${RDS_IDS[$idx]}" '.DBInstances[] | select(.DBInstanceIdentifier==$id) | .Endpoint.Address' <<< "$RDS_JSON")"
      echo "  [$idx] ${RDS_IDS[$idx]}  (${ep})"
    done
    read -rp "Select index [0-$((${#RDS_IDS[@]} - 1))], 'm' manual URL: " pick
    if [[ "$pick" == "m" ]]; then
      read -rp "DATABASE_URL [Enter to keep existing]: " NEW_DB_URL
      DATABASE_URL="${NEW_DB_URL:-$DATABASE_URL}"
    else
      if ! [[ "$pick" =~ ^[0-9]+$ ]] || [[ "$pick" -lt 0 ]] || [[ "$pick" -ge ${#RDS_IDS[@]} ]]; then
        echo "Invalid selection." >&2
        exit 1
      fi
      RID="${RDS_IDS[$pick]}"
      default_db="postgres"
      read -rp "Database name [${default_db}]: " dbname
      dbname="${dbname:-$default_db}"
      read -rsp "Database password (master user; input hidden): " dbpass
      echo ""
      if [[ -z "$dbpass" ]]; then
        echo "Password empty; keeping or setting DATABASE_URL manually." >&2
        read -rp "DATABASE_URL [Enter to keep existing]: " NEW_DB_URL
        DATABASE_URL="${NEW_DB_URL:-$DATABASE_URL}"
      else
        export _COLLECT_DB_PASS="$dbpass"
        DATABASE_URL="$(build_database_url_from_rds "$RID" "$dbname")"
        unset _COLLECT_DB_PASS
      fi
    fi
  fi
fi

echo ""
echo "=== ACM certificate (us-east-1, for CloudFront custom domain) ==="
: "${FRONTEND_ACM_CERT_ARN:=}"
[[ -n "${FRONTEND_ACM_CERT_ARN}" ]] && echo "Current FRONTEND_ACM_CERT_ARN from .env.gha is set (${#FRONTEND_ACM_CERT_ARN} chars)."
CERT_JSON="$(aws acm list-certificates "${PROFILE_ARGS[@]}" --region us-east-1 \
  --certificate-statuses ISSUED \
  --query 'CertificateSummaryList' --output json 2>/dev/null || echo '[]')"
CERT_COUNT="$(jq 'length' <<< "$CERT_JSON")"

if [[ "$CERT_COUNT" -eq 0 ]]; then
  echo "No ISSUED certificates in us-east-1."
  read -rp "FRONTEND_ACM_CERT_ARN [Enter to keep existing / blank]: " NEW_CERT
  FRONTEND_ACM_CERT_ARN="${NEW_CERT:-$FRONTEND_ACM_CERT_ARN}"
else
  echo "ISSUED certificates in us-east-1:"
  CERT_ARNS=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && CERT_ARNS+=("$line")
  done < <(jq -r '.[].CertificateArn' <<< "$CERT_JSON")
  for ((idx = 0; idx < ${#CERT_ARNS[@]}; idx++)); do
    dn="$(jq -r --arg arn "${CERT_ARNS[$idx]}" '.[] | select(.CertificateArn==$arn) | .DomainName' <<< "$CERT_JSON")"
    echo "  [$idx] ${dn}  ${CERT_ARNS[$idx]}"
  done
  read -rp "Select index, 'k' keep existing, 's' clear, 'p' paste ARN [k]: " cpick
  cpick="${cpick:-k}"
  case "$cpick" in
    k | K) ;;
    s | S) FRONTEND_ACM_CERT_ARN="" ;;
    p | P)
      read -rp "FRONTEND_ACM_CERT_ARN: " NEW_CERT
      FRONTEND_ACM_CERT_ARN="${NEW_CERT:-$FRONTEND_ACM_CERT_ARN}"
      ;;
    *)
      if ! [[ "$cpick" =~ ^[0-9]+$ ]] || [[ "$cpick" -lt 0 ]] || [[ "$cpick" -ge ${#CERT_ARNS[@]} ]]; then
        echo "Invalid selection." >&2
        exit 1
      fi
      FRONTEND_ACM_CERT_ARN="${CERT_ARNS[$cpick]}"
      ;;
  esac
fi

echo ""
echo "=== GitHub OIDC deploy role ==="
echo "Create the role per docs/github-actions-aws-oidc.md; paste its ARN."
: "${AWS_ROLE_TO_ASSUME:=}"
read -rp "AWS_ROLE_TO_ASSUME [Enter to keep]: " NEW_ROLE
AWS_ROLE_TO_ASSUME="${NEW_ROLE:-$AWS_ROLE_TO_ASSUME}"

echo ""
echo "=== Optional: custom SPA hostname (must match ACM cert SAN) ==="
: "${FRONTEND_DOMAIN_NAME:=}"
read -rp "FRONTEND_DOMAIN_NAME [Enter to keep]: " NEW_DOM
FRONTEND_DOMAIN_NAME="${NEW_DOM:-$FRONTEND_DOMAIN_NAME}"

echo ""
echo "=== Optional: Cloudflare DNS automation ==="
: "${CLOUDFLARE_API_TOKEN:=}"
: "${CLOUDFLARE_ZONE_ID:=}"
: "${CLOUDFLARE_ZONE_NAME:=}"
read -rp "CLOUDFLARE_API_TOKEN [Enter to keep]: " NEW_CF
CLOUDFLARE_API_TOKEN="${NEW_CF:-$CLOUDFLARE_API_TOKEN}"
read -rp "CLOUDFLARE_ZONE_ID [Enter to keep]: " NEW_CFZ
CLOUDFLARE_ZONE_ID="${NEW_CFZ:-$CLOUDFLARE_ZONE_ID}"
read -rp "CLOUDFLARE_ZONE_NAME [Enter to keep]: " NEW_CFZN
CLOUDFLARE_ZONE_NAME="${NEW_CFZN:-$CLOUDFLARE_ZONE_NAME}"

write_env_file() {
  local target="$1"
  DATABASE_URL="$DATABASE_URL" \
    FRONTEND_ACM_CERT_ARN="$FRONTEND_ACM_CERT_ARN" \
    AWS_ROLE_TO_ASSUME="$AWS_ROLE_TO_ASSUME" \
    CLOUDFLARE_API_TOKEN="$CLOUDFLARE_API_TOKEN" \
    CLOUDFLARE_ZONE_ID="$CLOUDFLARE_ZONE_ID" \
    CLOUDFLARE_ZONE_NAME="$CLOUDFLARE_ZONE_NAME" \
    AWS_REGION="$REGION" \
    FRONTEND_DOMAIN_NAME="${FRONTEND_DOMAIN_NAME:-}" \
    python3 - "$target" <<'PY'
import os
import pathlib
import shlex
import sys

out_arg = sys.argv[1]
lines = [
    "# Generated by scripts/collect-gha-env.sh — do not commit (.gitignore).",
    "#",
    "# GitHub: Settings → Secrets and variables → Actions",
    "#   Secrets: DATABASE_URL, FRONTEND_ACM_CERT_ARN, AWS_ROLE_TO_ASSUME,",
    "#            CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID, CLOUDFLARE_ZONE_NAME",
    "#   Variables: AWS_REGION, FRONTEND_DOMAIN_NAME",
    "#",
    "",
    "# --- Secrets ---",
    f"DATABASE_URL={shlex.quote(os.environ.get('DATABASE_URL', ''))}",
    f"FRONTEND_ACM_CERT_ARN={shlex.quote(os.environ.get('FRONTEND_ACM_CERT_ARN', ''))}",
    f"AWS_ROLE_TO_ASSUME={shlex.quote(os.environ.get('AWS_ROLE_TO_ASSUME', ''))}",
    f"CLOUDFLARE_API_TOKEN={shlex.quote(os.environ.get('CLOUDFLARE_API_TOKEN', ''))}",
    f"CLOUDFLARE_ZONE_ID={shlex.quote(os.environ.get('CLOUDFLARE_ZONE_ID', ''))}",
    f"CLOUDFLARE_ZONE_NAME={shlex.quote(os.environ.get('CLOUDFLARE_ZONE_NAME', ''))}",
    "",
    "# --- Variables ---",
    f"AWS_REGION={shlex.quote(os.environ.get('AWS_REGION', ''))}",
    f"FRONTEND_DOMAIN_NAME={shlex.quote(os.environ.get('FRONTEND_DOMAIN_NAME', ''))}",
    "",
]
text = "\n".join(lines) + "\n"
if out_arg == "-":
    sys.stdout.write(text)
else:
    pathlib.Path(out_arg).write_text(text, encoding="utf-8")
PY
}

if $DRY_RUN; then
  write_env_file -
else
  umask 077
  write_env_file "$OUT_FILE"
  echo ""
  echo "Wrote ${OUT_FILE} (private mode). Copy values into GitHub Actions secrets and variables."
fi
