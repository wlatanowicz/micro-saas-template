import { resolveApiError } from "./errors";
import type {
  ApiClientConfig,
  ApiFailure,
  ApiSuccess,
  AuthConfig,
  Health,
  ItemsResponse,
  MeUser,
  MessageResponse,
  OAuthProvider,
  TokenResponse,
} from "./types";

async function parseJson<T>(r: Response): Promise<T | { detail?: unknown }> {
  return (await r.json().catch(() => ({}))) as T | { detail?: unknown };
}

function failureFromBody(body: { detail?: unknown }, status: number): ApiFailure {
  const resolved = resolveApiError(body);
  if (resolved) {
    return {
      ok: false,
      errorCode: resolved.code,
      errorParams: resolved.params,
      status,
    };
  }
  return { ok: false, errorCode: "request_validation_error", status };
}

export function createApiClient(config: ApiClientConfig) {
  function apiBase(): string {
    return (config.getBaseUrl() || "").replace(/\/$/, "");
  }

  async function postJson<T>(
    path: string,
    payload: unknown,
  ): Promise<ApiSuccess<T> | ApiFailure> {
    const r = await fetch(`${apiBase()}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await parseJson<T>(r);
    if (!r.ok) {
      return failureFromBody(body as { detail?: unknown }, r.status);
    }
    return { ok: true, data: body as T, status: r.status };
  }

  async function postEmpty(
    path: string,
    payload: unknown,
  ): Promise<{ ok: true; status: number } | ApiFailure> {
    const result = await postJson<MessageResponse>(path, payload);
    if (!result.ok) {
      return result;
    }
    return { ok: true, status: result.status };
  }

  async function fetchAuthConfig(): Promise<AuthConfig | null> {
    const base = apiBase();
    if (!base) {
      return null;
    }
    const r = await fetch(`${base}/api/auth/config`);
    if (!r.ok) {
      return null;
    }
    return (await r.json()) as AuthConfig;
  }

  async function fetchHealth(): Promise<ApiSuccess<Health> | ApiFailure> {
    const r = await fetch(`${apiBase()}/health`);
    const body = await parseJson<Health>(r);
    if (!r.ok) {
      return failureFromBody(body as { detail?: unknown }, r.status);
    }
    return { ok: true, data: body as Health, status: r.status };
  }

  async function fetchItems(): Promise<ApiSuccess<ItemsResponse> | ApiFailure> {
    const r = await fetch(`${apiBase()}/api/items`);
    const body = await parseJson<ItemsResponse>(r);
    if (!r.ok) {
      return failureFromBody(body as { detail?: unknown }, r.status);
    }
    return { ok: true, data: body as ItemsResponse, status: r.status };
  }

  function signInRequest(email: string, password: string) {
    return postJson<TokenResponse>("/api/auth/signin", { email, password });
  }

  function registerSendCode(email: string) {
    return postEmpty("/api/auth/register/send-code", { email });
  }

  function registerVerifyCode(email: string, code: string) {
    return postEmpty("/api/auth/register/verify-code", { email, code });
  }

  function registerComplete(
    email: string,
    code: string,
    password: string,
    passwordConfirm: string,
  ) {
    return postJson<TokenResponse>("/api/auth/register/complete", {
      email,
      code,
      password,
      password_confirm: passwordConfirm,
    });
  }

  function recoverySendCode(email: string) {
    return postEmpty("/api/auth/password-recovery/send-code", { email });
  }

  function recoveryVerifyCode(email: string, code: string) {
    return postEmpty("/api/auth/password-recovery/verify-code", { email, code });
  }

  function recoveryComplete(
    email: string,
    code: string,
    password: string,
    passwordConfirm: string,
  ) {
    return postJson<TokenResponse>("/api/auth/password-recovery/complete", {
      email,
      code,
      password,
      password_confirm: passwordConfirm,
    });
  }

  async function loadMe(token: string): Promise<ApiSuccess<MeUser> | ApiFailure> {
    const r = await fetch(`${apiBase()}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const body = await parseJson<MeUser>(r);
    if (!r.ok) {
      return failureFromBody(body as { detail?: unknown }, r.status);
    }
    return { ok: true, data: body as MeUser, status: r.status };
  }

  function oauthStartUrl(provider: OAuthProvider, redirectUri?: string): string {
    const url = new URL(`${apiBase()}/api/auth/${provider}`);
    if (redirectUri) {
      url.searchParams.set("redirect_uri", redirectUri);
    }
    return url.toString();
  }

  return {
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
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
