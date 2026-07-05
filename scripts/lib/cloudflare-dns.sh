#!/usr/bin/env bash
# Shared Cloudflare DNS helpers for deploy scripts.
set -euo pipefail

cf_is_ci() {
  [[ "${GITHUB_ACTIONS:-}" == "true" || "${CI:-}" == "true" ]]
}

cf_skip_or_fail() {
  local message="$1"
  if cf_is_ci && [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]]; then
    echo "ERROR: ${message}" >&2
    exit 1
  fi
  echo "${message}; skipping DNS update."
  exit 0
}

cf_require_token() {
  if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
    echo "CLOUDFLARE_API_TOKEN not set; skipping Cloudflare DNS update."
    exit 0
  fi
}

cf_curl_json() {
  local method="$1"
  local url="$2"
  local data="${3:-}"

  local response http_code body
  if [[ -n "${data}" ]]; then
    response="$(
      curl -sS -X "${method}" \
        -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
        -H "Content-Type: application/json" \
        --data "${data}" \
        -w $'\n__HTTP_CODE__:%{http_code}' \
        "${url}"
    )"
  else
    response="$(
      curl -sS -X "${method}" \
        -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
        -w $'\n__HTTP_CODE__:%{http_code}' \
        "${url}"
    )"
  fi

  http_code="${response##*__HTTP_CODE__:}"
  body="${response%$'\n'__HTTP_CODE__:*}"

  if [[ ! "${http_code}" =~ ^2 ]]; then
    echo "Cloudflare HTTP ${http_code} for ${method} ${url}" >&2
    if [[ -n "${body}" ]]; then
      echo "${body}" | jq -c '.errors // .' >&2 || echo "${body}" >&2
    fi
    exit 1
  fi

  if [[ -z "${body}" ]] || ! echo "${body}" | jq -e . >/dev/null 2>&1; then
    echo "Cloudflare returned invalid JSON for ${method} ${url}" >&2
    exit 1
  fi

  CF_LAST_JSON="${body}"
}

cf_json_success() {
  [[ "$(echo "${CF_LAST_JSON}" | jq -r '.success // false')" == "true" ]]
}

cf_json_errors() {
  echo "${CF_LAST_JSON}" | jq -c '.errors // []'
}

cf_fail_api() {
  local action="$1"
  echo "Cloudflare ${action} failed: $(cf_json_errors)" >&2
  exit 1
}

cf_zone_name_for_id() {
  local zone_id="$1"
  cf_curl_json GET "https://api.cloudflare.com/client/v4/zones/${zone_id}"
  cf_json_success || cf_fail_api "zone lookup"
  echo "${CF_LAST_JSON}" | jq -r '.result.name'
}

cf_lookup_zone_id() {
  local zone_name="$1"
  cf_curl_json GET "https://api.cloudflare.com/client/v4/zones?name=${zone_name}"
  cf_json_success || cf_fail_api "zone lookup for ${zone_name}"
  local count
  count="$(echo "${CF_LAST_JSON}" | jq -r '.result | length')"
  if [[ "${count}" -lt 1 ]]; then
    echo "Cloudflare zone not found for name ${zone_name}" >&2
    exit 1
  fi
  echo "${CF_LAST_JSON}" | jq -r '.result[0].id'
}

cf_try_lookup_zone_id() {
  local zone_name="$1"
  local response http_code body

  response="$(
    curl -sS \
      -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
      -w $'\n__HTTP_CODE__:%{http_code}' \
      "https://api.cloudflare.com/client/v4/zones?name=${zone_name}"
  )"
  http_code="${response##*__HTTP_CODE__:}"
  body="${response%$'\n'__HTTP_CODE__:*}"

  if [[ ! "${http_code}" =~ ^2 ]] || ! echo "${body}" | jq -e '.success == true' >/dev/null 2>&1; then
    return 1
  fi
  if [[ "$(echo "${body}" | jq -r '.result | length')" -lt 1 ]]; then
    return 1
  fi
  echo "${body}" | jq -r '.result[0].id'
}

cf_resolve_zone_for_fqdn() {
  local fqdn="${1%.}"

  if [[ -n "${CLOUDFLARE_ZONE_ID:-}" ]]; then
    CF_ZONE_ID="${CLOUDFLARE_ZONE_ID}"
    CF_ZONE_NAME="$(cf_zone_name_for_id "${CF_ZONE_ID}")"
  elif [[ -n "${CLOUDFLARE_ZONE_NAME:-}" ]]; then
    CF_ZONE_NAME="${CLOUDFLARE_ZONE_NAME}"
    CF_ZONE_ID="$(cf_lookup_zone_id "${CF_ZONE_NAME}")"
  else
    CF_ZONE_NAME=""
    CF_ZONE_ID=""
  fi

  if [[ -n "${CF_ZONE_ID}" ]]; then
    if [[ "${fqdn}" == "${CF_ZONE_NAME}" || "${fqdn}" == *".${CF_ZONE_NAME}" ]]; then
      CF_RECORD_FQDN="${fqdn}"
      CF_RECORD_NAME="${fqdn%.${CF_ZONE_NAME}}"
      [[ "${CF_RECORD_NAME}" == "${fqdn}" ]] && CF_RECORD_NAME="@"
      return 0
    fi
  fi

  local domain="${fqdn}"
  while [[ "${domain}" == *.* ]]; do
    local zone_id
    zone_id="$(cf_try_lookup_zone_id "${domain}" || true)"
    if [[ -n "${zone_id}" ]]; then
      CF_ZONE_ID="${zone_id}"
      CF_ZONE_NAME="${domain}"
      CF_RECORD_FQDN="${fqdn}"
      CF_RECORD_NAME="${fqdn%.${domain}}"
      [[ "${CF_RECORD_NAME}" == "${fqdn}" ]] && CF_RECORD_NAME="@"
      return 0
    fi
    domain="${domain#*.}"
  done

  echo "Cloudflare: could not resolve zone for ${fqdn}; set CLOUDFLARE_ZONE_ID or CLOUDFLARE_ZONE_NAME." >&2
  exit 1
}

cf_list_cname_record_id() {
  local zone_id="$1"
  local record_fqdn="$2"
  local response http_code body

  response="$(
    curl -sS -G \
      -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
      -H "Content-Type: application/json" \
      --data-urlencode "type=CNAME" \
      --data-urlencode "name=${record_fqdn}" \
      -w $'\n__HTTP_CODE__:%{http_code}' \
      "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records"
  )"
  http_code="${response##*__HTTP_CODE__:}"
  body="${response%$'\n'__HTTP_CODE__:*}"

  if [[ ! "${http_code}" =~ ^2 ]]; then
    echo "Cloudflare HTTP ${http_code} listing CNAME ${record_fqdn}" >&2
    exit 1
  fi

  CF_LAST_JSON="${body}"
  cf_json_success || cf_fail_api "list DNS records for ${record_fqdn}"
  echo "${CF_LAST_JSON}" | jq -r '.result[0].id // empty'
}

cf_verify_cname() {
  local zone_id="$1"
  local record_fqdn="$2"
  local expected_target="${3%.}"

  local record_id content
  record_id="$(cf_list_cname_record_id "${zone_id}" "${record_fqdn}")"
  if [[ -z "${record_id}" ]]; then
    echo "Cloudflare verification failed: CNAME ${record_fqdn} not found after upsert." >&2
    exit 1
  fi

  cf_curl_json GET "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records/${record_id}"
  cf_json_success || cf_fail_api "read DNS record ${record_id}"
  content="$(echo "${CF_LAST_JSON}" | jq -r '.result.content // empty' | sed 's/\.$//')"
  if [[ "${content}" != "${expected_target}" ]]; then
    echo "Cloudflare verification failed: CNAME ${record_fqdn} points to ${content}, expected ${expected_target}." >&2
    exit 1
  fi
}

cf_ensure_cname() {
  local record_fqdn="$1"
  local target="${2%.}"

  cf_require_token
  cf_resolve_zone_for_fqdn "${record_fqdn}"

  local zone_id="${CF_ZONE_ID}"
  local zone_name="${CF_ZONE_NAME}"
  local record_name="${CF_RECORD_NAME}"

  echo "Cloudflare zone ${zone_name} (${zone_id}): ensuring CNAME ${record_fqdn} -> ${target}..."

  local record_id action
  record_id="$(cf_list_cname_record_id "${zone_id}" "${record_fqdn}")"
  if [[ -n "${record_id}" ]]; then
    action="updated"
    cf_curl_json PATCH "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records/${record_id}" \
      "$(jq -n --arg content "${target}" '{type: "CNAME", content: $content, proxied: false}')"
  else
    action="created"
    cf_curl_json POST "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records" \
      "$(jq -n \
        --arg name "${record_name}" \
        --arg content "${target}" \
        '{type: "CNAME", name: $name, content: $content, ttl: 300, proxied: false}')"
  fi

  cf_json_success || cf_fail_api "DNS upsert for ${record_fqdn}"

  local result_id result_content
  result_id="$(echo "${CF_LAST_JSON}" | jq -r '.result.id // empty')"
  result_content="$(echo "${CF_LAST_JSON}" | jq -r '.result.content // empty' | sed 's/\.$//')"
  if [[ -z "${result_id}" || "${result_content}" != "${target}" ]]; then
    echo "Cloudflare DNS upsert returned unexpected result: $(echo "${CF_LAST_JSON}" | jq -c '.')" >&2
    exit 1
  fi

  cf_verify_cname "${zone_id}" "${record_fqdn}" "${target}"
  echo "Cloudflare DNS ${action}: ${record_fqdn} -> ${target} (record ${result_id})."
}
