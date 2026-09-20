import { createApiClient, parseOAuthCallbackUrl } from "@micro-saas/api-client";

const client = createApiClient({
  getBaseUrl: () => import.meta.env.VITE_API_BASE_URL ?? "",
});

export const {
  apiBase,
  fetchAuthConfig,
  fetchHealth,
  fetchItems,
  signInRequest,
  registerSendCode,
  registerVerifyCode,
  registerComplete,
  recoverySendCode,
  recoveryVerifyCode,
  recoveryComplete,
  loadMe,
  oauthStartUrl,
} = client;

export function parseOAuthHash(): { accessToken?: string; authErrorCode?: string } {
  const result = parseOAuthCallbackUrl(window.location.href);
  if (result.accessToken || result.authErrorCode) {
    const path = window.location.pathname + window.location.search;
    window.history.replaceState(null, "", path);
  }
  return result;
}
