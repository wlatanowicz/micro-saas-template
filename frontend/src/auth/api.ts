import type { AuthConfig, MessageResponse, TokenResponse } from "./types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

export function apiBase(): string {
  return (apiBaseUrl || "").replace(/\/$/, "");
}

export function formatApiError(body: { detail?: unknown }): string {
  const d = body.detail;
  if (typeof d === "string") {
    return d;
  }
  if (Array.isArray(d)) {
    return d
      .map((err) => {
        if (err && typeof err === "object" && "msg" in err) {
          return String((err as { msg: string }).msg);
        }
        return String(err);
      })
      .join("; ");
  }
  return "Request failed";
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

export async function signInRequest(
  email: string,
  password: string,
): Promise<{ ok: true; data: TokenResponse } | { ok: false; error: string }> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/signin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await parseJson<TokenResponse>(r);
  if (!r.ok) {
    return { ok: false, error: formatApiError(body as { detail?: unknown }) };
  }
  return { ok: true, data: body as TokenResponse };
}

export async function registerSendCode(
  email: string,
): Promise<{ ok: true } | { ok: false; error: string }> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/register/send-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const body = await parseJson<MessageResponse>(r);
  if (!r.ok) {
    return { ok: false, error: formatApiError(body as { detail?: unknown }) };
  }
  return { ok: true };
}

export async function registerVerifyCode(
  email: string,
  code: string,
): Promise<{ ok: true } | { ok: false; error: string }> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/register/verify-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code }),
  });
  const body = await parseJson<MessageResponse>(r);
  if (!r.ok) {
    return { ok: false, error: formatApiError(body as { detail?: unknown }) };
  }
  return { ok: true };
}

export async function registerComplete(
  email: string,
  code: string,
  password: string,
  passwordConfirm: string,
): Promise<{ ok: true; data: TokenResponse } | { ok: false; error: string }> {
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
    return { ok: false, error: formatApiError(body as { detail?: unknown }) };
  }
  return { ok: true, data: body as TokenResponse };
}

export async function recoverySendCode(
  email: string,
): Promise<{ ok: true } | { ok: false; error: string }> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/password-recovery/send-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const body = await parseJson<MessageResponse>(r);
  if (!r.ok) {
    return { ok: false, error: formatApiError(body as { detail?: unknown }) };
  }
  return { ok: true };
}

export async function recoveryVerifyCode(
  email: string,
  code: string,
): Promise<{ ok: true } | { ok: false; error: string }> {
  const base = apiBase();
  const r = await fetch(`${base}/api/auth/password-recovery/verify-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code }),
  });
  const body = await parseJson<MessageResponse>(r);
  if (!r.ok) {
    return { ok: false, error: formatApiError(body as { detail?: unknown }) };
  }
  return { ok: true };
}

export async function recoveryComplete(
  email: string,
  code: string,
  password: string,
  passwordConfirm: string,
): Promise<{ ok: true; data: TokenResponse } | { ok: false; error: string }> {
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
    return { ok: false, error: formatApiError(body as { detail?: unknown }) };
  }
  return { ok: true, data: body as TokenResponse };
}

export async function loadMe(token: string): Promise<Response> {
  const base = apiBase();
  return fetch(`${base}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function parseOAuthHash(): { accessToken?: string; authError?: string } {
  const hash = window.location.hash.replace(/^#/, "");
  if (!hash) {
    return {};
  }
  const params = new URLSearchParams(hash);
  const accessToken = params.get("access_token") ?? undefined;
  const authError = params.get("auth_error") ?? undefined;
  if (accessToken || authError) {
    const path = window.location.pathname + window.location.search;
    window.history.replaceState(null, "", path);
  }
  return { accessToken, authError };
}
