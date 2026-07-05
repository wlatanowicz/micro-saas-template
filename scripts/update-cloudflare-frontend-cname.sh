#!/usr/bin/env bash
# Point the stack's frontend custom domain (CloudFront alias) at the distribution's
# *.cloudfront.net hostname via Cloudflare DNS (proxied CNAME — traffic flows through the Cloudflare edge).
set -euo pipefail

# Usage: ./scripts/update-cloudflare-frontend-cname.sh <stage> <region> [stack_name]

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

echo "Reading CloudFormation outputs from ${STACK_NAME} in ${REGION} for Cloudflare DNS..."
CLOUDFRONT_DOMAIN="$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendCloudFrontDomainName'].OutputValue" \
  --output text)"

FRONTEND_CUSTOM_DOMAIN="$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendCustomDomainName'].OutputValue" \
  --output text)"

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "CLOUDFLARE_API_TOKEN not set; skipping Cloudflare DNS update."
  exit 0
fi

if [[ -z "${FRONTEND_CUSTOM_DOMAIN}" || "${FRONTEND_CUSTOM_DOMAIN}" == "None" ]]; then
  cf_skip_or_fail "Cloudflare: FrontendCustomDomainName output missing"
fi

if [[ -z "${CLOUDFRONT_DOMAIN}" || "${CLOUDFRONT_DOMAIN}" == "None" ]]; then
  cf_skip_or_fail "Cloudflare: CloudFront domain output missing"
fi

cf_ensure_cname "${FRONTEND_CUSTOM_DOMAIN}" "${CLOUDFRONT_DOMAIN}" true
