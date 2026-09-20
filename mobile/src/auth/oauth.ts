import * as AuthSession from "expo-auth-session";
import * as WebBrowser from "expo-web-browser";
import { parseOAuthCallbackUrl, type OAuthCallbackResult, type OAuthProvider } from "@micro-saas/api-client";

import { api } from "../api";

WebBrowser.maybeCompleteAuthSession();

export function oauthRedirectUri(): string {
  return AuthSession.makeRedirectUri({ scheme: "micro-saas", path: "oauth" });
}

export async function startOAuth(provider: OAuthProvider): Promise<OAuthCallbackResult> {
  const redirectUri = oauthRedirectUri();
  const result = await WebBrowser.openAuthSessionAsync(api.oauthStartUrl(provider, redirectUri), redirectUri);
  if (result.type !== "success" || !("url" in result) || !result.url) {
    return {};
  }
  return parseOAuthCallbackUrl(result.url);
}
