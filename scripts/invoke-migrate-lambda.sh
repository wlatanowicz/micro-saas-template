#!/usr/bin/env bash
# Invoke the migration Lambda (Alembic upgrade head) after a successful deploy.
# Usage: ./scripts/invoke-migrate-lambda.sh <stage> <region> [stack_name]
set -euo pipefail

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

MIGRATE_FN="$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='MigrateLambdaName'].OutputValue" \
  --output text)"

if [[ -z "${MIGRATE_FN}" || "${MIGRATE_FN}" == "None" ]]; then
  echo "Could not read MigrateLambdaName from stack ${STACK_NAME}."
  exit 1
fi

OUT="$(mktemp)"
cleanup() {
  rm -f "${OUT}"
}
trap cleanup EXIT

echo "Invoking migration Lambda ${MIGRATE_FN}..."
aws lambda invoke \
  --function-name "${MIGRATE_FN}" \
  --region "${REGION}" \
  --cli-binary-format raw-in-base64-out \
  --invocation-type RequestResponse \
  --payload "{}" \
  "${OUT}" >/dev/null

cat "${OUT}"
echo ""

if jq -e 'has("errorMessage") and .errorMessage != null' "${OUT}" >/dev/null 2>&1; then
  echo "Migration Lambda failed."
  exit 1
fi

if ! jq -e '.ok == true' "${OUT}" >/dev/null 2>&1; then
  echo "Unexpected response (expected ok: true)."
  exit 1
fi

echo "Migrations finished successfully."
