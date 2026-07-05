#!/usr/bin/env bash
# Point the stack's API custom domain at the regional API Gateway hostname via Cloudflare DNS
# (CNAME, DNS only — TLS terminates at API Gateway).
set -euo pipefail

# Usage: ./scripts/update-cloudflare-api-cname.sh <stage> <region> [stack_name]

STAGE="${1:-prod}"
REGION="${2:-eu-central-1}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib/cloudflare-dns.sh
source "${REPO_ROOT}/scripts/lib/cloudflare-dns.sh"

if [[ -n "${3:-}" ]]; then
  STACK_NAME="$3"
else
  SERVICE_NAME="$(
    grep -m1 -E '^service:' "${REPO_ROOT}/backend/serverless.yml" |
      sed 's/^service:[[:space:]]*//' |
      tr -d "\"'"
  )"
  STACK_NAME="${SERVICE_NAME}-${STAGE}"
fi

echo "Reading CloudFormation outputs from ${STACK_NAME} in ${REGION} for API Cloudflare DNS..."
API_CUSTOM_DOMAIN="$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiCustomDomainName'].OutputValue" \
  --output text)"

API_CUSTOM_TARGET="$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiCustomDomainTarget'].OutputValue" \
  --output text)"

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "CLOUDFLARE_API_TOKEN not set; skipping Cloudflare DNS update."
  exit 0
fi

if [[ -z "${API_CUSTOM_DOMAIN}" || "${API_CUSTOM_DOMAIN}" == "None" ]]; then
  cf_skip_or_fail "Cloudflare: ApiCustomDomainName output missing"
fi

if [[ -z "${API_CUSTOM_TARGET}" || "${API_CUSTOM_TARGET}" == "None" ]]; then
  cf_skip_or_fail "Cloudflare: ApiCustomDomainTarget output missing"
fi

cf_ensure_cname "${API_CUSTOM_DOMAIN}" "${API_CUSTOM_TARGET}"
