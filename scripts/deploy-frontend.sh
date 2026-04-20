#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/deploy-frontend.sh <stage> <region> [stack_name]
# Stack name defaults to "<service from backend/serverless.yml>-<stage>".

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

echo "Reading CloudFormation outputs from ${STACK_NAME} in ${REGION}..."
API_URL="$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue" \
  --output text)"

BUCKET_NAME="$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)"

CLOUDFRONT_DOMAIN="$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendCloudFrontDomainName'].OutputValue" \
  --output text)"

CLOUDFRONT_DISTRIBUTION_ID="$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendCloudFrontDistributionId'].OutputValue" \
  --output text)"

if [[ -z "${API_URL}" || -z "${BUCKET_NAME}" ]]; then
  echo "Could not read HttpApiUrl or FrontendBucketName from stack outputs."
  exit 1
fi

echo "Building frontend with API URL: ${API_URL}"
pushd "${REPO_ROOT}/frontend" >/dev/null
VITE_API_BASE_URL="${API_URL}" npm run build
popd >/dev/null

echo "Uploading frontend to s3://${BUCKET_NAME}..."
aws s3 sync "${REPO_ROOT}/frontend/dist" "s3://${BUCKET_NAME}" --delete --region "${REGION}"

if [[ -z "${CLOUDFRONT_DISTRIBUTION_ID}" || "${CLOUDFRONT_DISTRIBUTION_ID}" == "None" ]]; then
  if [[ -n "${CLOUDFRONT_DOMAIN}" && "${CLOUDFRONT_DOMAIN}" != "None" ]]; then
    echo "CloudFront distribution ID output missing, looking up by domain..."
    CLOUDFRONT_DISTRIBUTION_ID="$(aws cloudfront list-distributions \
      --query "DistributionList.Items[?DomainName=='${CLOUDFRONT_DOMAIN}'].Id | [0]" \
      --output text)"
  fi
fi

if [[ -n "${CLOUDFRONT_DISTRIBUTION_ID}" && "${CLOUDFRONT_DISTRIBUTION_ID}" != "None" ]]; then
  echo "Creating CloudFront invalidation for distribution ${CLOUDFRONT_DISTRIBUTION_ID}..."
  aws cloudfront create-invalidation \
    --distribution-id "${CLOUDFRONT_DISTRIBUTION_ID}" \
    --paths "/*" >/dev/null
  echo "CloudFront invalidation requested."
fi

echo "Frontend deployed."
echo "S3 website URL:"
echo "http://${BUCKET_NAME}.s3-website.${REGION}.amazonaws.com"
if [[ -n "${CLOUDFRONT_DOMAIN}" && "${CLOUDFRONT_DOMAIN}" != "None" ]]; then
  echo "CloudFront URL:"
  echo "https://${CLOUDFRONT_DOMAIN}"
fi
