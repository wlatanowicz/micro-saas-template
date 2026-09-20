import type { OAuthCallbackResult } from "./types";

function paramsFromSearch(search: string): OAuthCallbackResult {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const accessToken = params.get("access_token") ?? undefined;
  const authErrorCode = params.get("auth_error_code") ?? undefined;
  return { accessToken, authErrorCode };
}

export function parseOAuthCallbackUrl(url: string): OAuthCallbackResult {
  try {
    const parsed = new URL(url);
    const fromQuery = paramsFromSearch(parsed.search);
    if (fromQuery.accessToken || fromQuery.authErrorCode) {
      return fromQuery;
    }
    const hash = parsed.hash.replace(/^#/, "");
    if (hash) {
      return paramsFromSearch(hash);
    }
    return {};
  } catch {
    const hashIndex = url.indexOf("#");
    const queryIndex = url.indexOf("?");
    if (queryIndex >= 0 && (hashIndex < 0 || queryIndex < hashIndex)) {
      const end = hashIndex >= 0 ? hashIndex : url.length;
      return paramsFromSearch(url.slice(queryIndex, end));
    }
    if (hashIndex >= 0) {
      return paramsFromSearch(url.slice(hashIndex + 1));
    }
    return {};
  }
}
