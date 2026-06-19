import type { AuthConfig, MessageResponse, TokenResponse } from "./types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

export type ApiErrorResolution = {
  code: string;
  params?: Record<string, string | number>;
};

export function apiBase(): string {
  return (apiBaseUrl || "").replace(/\/$/, "");
}

export function resolveApiError(body: { detail?: unknown }): ApiErrorResolution | null {
  const d = body.detail;
  if (typeof d === "object" && d !== null && "code" in d) {
    const code = String((d as { code: string }).code);
    const params = (d as { params?: Record<string, string | number> }).params;
    return params ? { code, params } : { code };
  }
  return null;
}

async function parseJson<T>(r: Response): Promise<T | { detail?: unknown }> {
  return (await r.json().catch(() => ({}))) as T | { detail?: unknown };
}

export async function fetchAuthConfig(): Promise<AuthConfig | null> {
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

type ApiFailure = { ok: false; errorCode: string; errorParams?: Record<string, string | number> };
type ApiSuccess<T> = { ok: true; data: T };

function failureFromBody(body: { detail?: unknown }): ApiFailure {
  const resolved = resolveApiError(body);
  if (resolved) {
    return {
      ok: false,
      errorCode: resolved.code,
      errorParams: resolved.params,
    };
  }
  return { ok: false, errorCode: "request_validation_error" };
}

export async function signInRequest(
  email: string,
  password: string,
): Promise<ApiSuccess<TokenResponse> | ApiFailure> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/signin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await parseJson<TokenResponse>(r);
  if (!r.ok) {
    return failureFromBody(body as { detail?: unknown });
  }
  return { ok: true, data: body as TokenResponse };
}

export async function registerSendCode(
  email: string,
): Promise<{ ok: true } | ApiFailure> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/register/send-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const body = await parseJson<MessageResponse>(r);
  if (!r.ok) {
    return failureFromBody(body as { detail?: unknown });
  }
  return { ok: true };
}

export async function registerVerifyCode(
  email: string,
  code: string,
): Promise<{ ok: true } | ApiFailure> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/register/verify-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code }),
  });
  const body = await parseJson<MessageResponse>(r);
  if (!r.ok) {
    return failureFromBody(body as { detail?: unknown });
  }
  return { ok: true };
}

export async function registerComplete(
  email: string,
  code: string,
  password: string,
  passwordConfirm: string,
): Promise<ApiSuccess<TokenResponse> | ApiFailure> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/register/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      code,
      password,
      password_confirm: passwordConfirm,
    }),
  });
  const body = await parseJson<TokenResponse>(r);
  if (!r.ok) {
    return failureFromBody(body as { detail?: unknown });
  }
  return { ok: true, data: body as TokenResponse };
}

export async function recoverySendCode(
  email: string,
): Promise<{ ok: true } | ApiFailure> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/password-recovery/send-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const body = await parseJson<MessageResponse>(r);
  if (!r.ok) {
    return failureFromBody(body as { detail?: unknown });
  }
  return { ok: true };
}

export async function recoveryVerifyCode(
  email: string,
  code: string,
): Promise<{ ok: true } | ApiFailure> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/password-recovery/verify-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code }),
  });
  const body = await parseJson<MessageResponse>(r);
  if (!r.ok) {
    return failureFromBody(body as { detail?: unknown });
  }
  return { ok: true };
}

export async function recoveryComplete(
  email: string,
  code: string,
  password: string,
  passwordConfirm: string,
): Promise<ApiSuccess<TokenResponse> | ApiFailure> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/password-recovery/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      code,
      password,
      password_confirm: passwordConfirm,
    }),
  });
  const body = await parseJson<TokenResponse>(r);
  if (!r.ok) {
    return failureFromBody(body as { detail?: unknown });
  }
  return { ok: true, data: body as TokenResponse };
}

export async function loadMe(token: string): Promise<Response> {
  const base = apiBase();
  return fetch(`${base}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function parseOAuthHash(): { accessToken?: string; authErrorCode?: string } {
  const hash = window.location.hash.replace(/^#/, "");
  if (!hash) {
    return {};
  }
  const params = new URLSearchParams(hash);
  const accessToken = params.get("access_token") ?? undefined;
  const authErrorCode = params.get("auth_error_code") ?? undefined;
  if (accessToken || authErrorCode) {
    const path = window.location.pathname + window.location.search;
    window.history.replaceState(null, "", path);
  }
  return { accessToken, authErrorCode };
}
