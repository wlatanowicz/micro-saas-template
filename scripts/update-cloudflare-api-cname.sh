#!/usr/bin/env bash
# Point the stack's API custom domain at the regional API Gateway hostname via Cloudflare DNS
# (CNAME, DNS only — TLS terminates at API Gateway).
set -euo pipefail

# Usage: ./scripts/update-cloudflare-api-cname.sh <stage> <region> [stack_name]

STAGE="${1:-prod}"
REGION="${2:-eu-central-1}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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

zone_id="${CLOUDFLARE_ZONE_ID:-}"
if [[ -z "${zone_id}" && -n "${CLOUDFLARE_ZONE_NAME:-}" ]]; then
  zone_json="$(curl -sS -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    "https://api.cloudflare.com/client/v4/zones?name=${CLOUDFLARE_ZONE_NAME}")"
  zone_id="$(echo "${zone_json}" | jq -r '.result[0].id // empty')"
fi

if [[ -z "${zone_id}" ]]; then
  echo "Cloudflare: set CLOUDFLARE_ZONE_ID or CLOUDFLARE_ZONE_NAME; skipping DNS update."
  exit 0
fi

if [[ -z "${API_CUSTOM_DOMAIN}" || "${API_CUSTOM_DOMAIN}" == "None" ]]; then
  echo "Cloudflare: ApiCustomDomainName output missing; skipping DNS update."
  exit 0
fi

if [[ -z "${API_CUSTOM_TARGET}" || "${API_CUSTOM_TARGET}" == "None" ]]; then
  echo "Cloudflare: ApiCustomDomainTarget output missing; skipping DNS update."
  exit 0
fi

cf_target="${API_CUSTOM_TARGET%.}"
record_name="${API_CUSTOM_DOMAIN%.}"
echo "Cloudflare: ensuring CNAME ${record_name} -> ${cf_target}..."
list_json="$(curl -sS -G -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data-urlencode "type=CNAME" \
  --data-urlencode "name=${record_name}" \
  "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records")"
if [[ "$(echo "${list_json}" | jq -r '.success')" != "true" ]]; then
  echo "Cloudflare list DNS records failed: $(echo "${list_json}" | jq -c '.errors // .')"
  exit 1
fi
record_id="$(echo "${list_json}" | jq -r '.result[0].id // empty')"
patch_body="$(jq -n --arg c "${cf_target}" '{content: $c, proxied: false}')"
if [[ -n "${record_id}" ]]; then
  upd_json="$(curl -sS -X PATCH \
    -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    -H "Content-Type: application/json" \
    --data "${patch_body}" \
    "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records/${record_id}")"
else
  post_body="$(jq -n \
    --arg name "${record_name}" \
    --arg content "${cf_target}" \
    '{type: "CNAME", name: $name, content: $content, ttl: 300, proxied: false}')"
  upd_json="$(curl -sS -X POST \
    -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    -H "Content-Type: application/json" \
    --data "${post_body}" \
    "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records")"
fi
if [[ "$(echo "${upd_json}" | jq -r '.success')" != "true" ]]; then
  echo "Cloudflare DNS update failed: $(echo "${upd_json}" | jq -c '.errors // .')"
  exit 1
fi
echo "Cloudflare API DNS updated."
