#!/usr/bin/env bash
# Request ACM certificates for the frontend (us-east-1) and API (deploy region),
# add DNS validation CNAMEs in Cloudflare, and print the cert ARNs for GitHub Actions.
#
# Usage: AWS_PROFILE=my-prof ./scripts/provision-acm-certs.sh
#
# Reads defaults from .env.gha when present. Required:
#   FRONTEND_DOMAIN_NAME
#   CLOUDFLARE_API_TOKEN
# Optional (with defaults):
#   API_DOMAIN_NAME          — defaults to api.<FRONTEND_DOMAIN_NAME>
#   AWS_REGION               — deploy region for the API cert (default eu-central-1)
#   CLOUDFLARE_ZONE_ID / CLOUDFLARE_ZONE_NAME
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_FILE="${REPO_ROOT}/.env.gha"
FRONTEND_ACM_REGION="us-east-1"

# shellcheck source=lib/cloudflare-dns.sh
source "${REPO_ROOT}/scripts/lib/cloudflare-dns.sh"

usage() {
  cat <<EOF
Usage: AWS_PROFILE=... $0 [-h]

Request ACM certificates for custom frontend (CloudFront, ${FRONTEND_ACM_REGION}) and API
(API Gateway, deploy region) hostnames, upsert ACM DNS validation CNAMEs in Cloudflare, and
print FRONTEND_ACM_CERT_ARN and API_ACM_CERT_ARN.

Environment (or values from ${OUT_FILE}):
  FRONTEND_DOMAIN_NAME     SPA hostname (required)
  API_DOMAIN_NAME          API hostname (default: api.<frontend-host>)
  AWS_REGION               API cert region (default: eu-central-1)
  CLOUDFLARE_API_TOKEN     Cloudflare API token (required)
  CLOUDFLARE_ZONE_ID       Optional Cloudflare zone id
  CLOUDFLARE_ZONE_NAME     Optional Cloudflare zone name (used when zone id is unset)
EOF
}

while getopts "h" opt; do
  case "$opt" in
    h)
      usage
      exit 0
      ;;
    *) exit 2 ;;
  esac
done

for cmd in aws jq python3 curl; do
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
        val = ""
    else:
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

PROFILE_ARGS=()
if [[ -n "${AWS_PROFILE:-}" ]]; then
  PROFILE_ARGS=(--profile "$AWS_PROFILE")
fi

REGION="${AWS_REGION:-}"
if [[ -z "${REGION}" ]]; then
  REGION="$(aws configure get region "${PROFILE_ARGS[@]}" 2>/dev/null | tr -d '\r' || true)"
fi
REGION="${REGION:-eu-central-1}"

: "${FRONTEND_DOMAIN_NAME:=}"
if [[ -z "${FRONTEND_DOMAIN_NAME}" ]]; then
  echo "FRONTEND_DOMAIN_NAME is required (set it or add it to ${OUT_FILE})." >&2
  exit 1
fi

: "${API_DOMAIN_NAME:=}"
if [[ -z "${API_DOMAIN_NAME}" ]]; then
  API_DOMAIN_NAME="api.${FRONTEND_DOMAIN_NAME}"
fi

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "CLOUDFLARE_API_TOKEN is required for ACM DNS validation CNAMEs." >&2
  exit 1
fi

echo "Caller identity:"
aws sts get-caller-identity "${PROFILE_ARGS[@]}" --output table || {
  echo "AWS credentials failed. Set AWS_PROFILE or configure credentials." >&2
  exit 1
}

acm_find_or_request_cert() {
  local region="$1"
  local domain="$2"
  local arn status

  arn="$(aws acm list-certificates "${PROFILE_ARGS[@]}" --region "${region}" \
    --certificate-statuses ISSUED PENDING_VALIDATION \
    --query "CertificateSummaryList[?DomainName=='${domain}'].CertificateArn | [0]" \
    --output text 2>/dev/null || true)"

  if [[ -n "${arn}" && "${arn}" != "None" ]]; then
    status="$(aws acm describe-certificate "${PROFILE_ARGS[@]}" --region "${region}" \
      --certificate-arn "${arn}" \
      --query 'Certificate.Status' \
      --output text)"
    echo "Using existing ACM certificate (${status}) for ${domain} in ${region}: ${arn}" >&2
    printf '%s' "${arn}"
    return 0
  fi

  arn="$(aws acm request-certificate "${PROFILE_ARGS[@]}" --region "${region}" \
    --domain-name "${domain}" \
    --validation-method DNS \
    --query CertificateArn \
    --output text)"
  echo "Requested ACM certificate for ${domain} in ${region}: ${arn}" >&2
  printf '%s' "${arn}"
}

acm_wait_for_validation_records() {
  local region="$1"
  local cert_arn="$2"
  local attempt records_json count

  for attempt in $(seq 1 30); do
    records_json="$(aws acm describe-certificate "${PROFILE_ARGS[@]}" --region "${region}" \
      --certificate-arn "${cert_arn}" \
      --query 'Certificate.DomainValidationOptions[?ResourceRecord!=`null`].ResourceRecord' \
      --output json)"
    count="$(jq 'length' <<< "${records_json}")"
    if [[ "${count}" -gt 0 ]]; then
      printf '%s' "${records_json}"
      return 0
    fi
    sleep 2
  done

  echo "Timed out waiting for ACM validation records on ${cert_arn} in ${region}." >&2
  exit 1
}

acm_sync_validation_cnames() {
  local region="$1"
  local cert_arn="$2"
  local domain="$3"
  local status records_json

  status="$(aws acm describe-certificate "${PROFILE_ARGS[@]}" --region "${region}" \
    --certificate-arn "${cert_arn}" \
    --query 'Certificate.Status' \
    --output text)"

  if [[ "${status}" == "ISSUED" ]]; then
    echo "Certificate for ${domain} in ${region} is already ISSUED; skipping validation CNAMEs."
    return 0
  fi

  echo "Ensuring Cloudflare validation CNAMEs for ${domain} in ${region} (status: ${status})..."
  records_json="$(acm_wait_for_validation_records "${region}" "${cert_arn}")"

  while IFS=$'\t' read -r record_name record_value; do
    [[ -n "${record_name}" && -n "${record_value}" ]] || continue
    cf_ensure_cname "${record_name%.}" "${record_value%.}"
  done < <(jq -r '.[] | [.Name, .Value] | @tsv' <<< "${records_json}")
}

echo ""
echo "=== Frontend ACM (${FRONTEND_ACM_REGION}) for ${FRONTEND_DOMAIN_NAME} ==="
FRONTEND_ACM_CERT_ARN="$(acm_find_or_request_cert "${FRONTEND_ACM_REGION}" "${FRONTEND_DOMAIN_NAME}")"
acm_sync_validation_cnames "${FRONTEND_ACM_REGION}" "${FRONTEND_ACM_CERT_ARN}" "${FRONTEND_DOMAIN_NAME}"

echo ""
echo "=== API ACM (${REGION}) for ${API_DOMAIN_NAME} ==="
API_ACM_CERT_ARN="$(acm_find_or_request_cert "${REGION}" "${API_DOMAIN_NAME}")"
acm_sync_validation_cnames "${REGION}" "${API_ACM_CERT_ARN}" "${API_DOMAIN_NAME}"

echo ""
echo "=== GitHub Actions secrets (or export for local deploy) ==="
echo "FRONTEND_ACM_CERT_ARN=${FRONTEND_ACM_CERT_ARN}"
echo "API_ACM_CERT_ARN=${API_ACM_CERT_ARN}"
echo ""
echo "ACM may take a few minutes to reach ISSUED after DNS propagates. Re-run deploy once both certs are ISSUED."
