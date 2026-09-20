import { describe, expect, it, vi } from "vitest";

import { createApiClient } from "./client";
import { resolveApiError } from "./errors";
import { parseOAuthCallbackUrl } from "./oauth";

describe("resolveApiError", () => {
  it("reads nested detail.code and params", () => {
    expect(
      resolveApiError({
        detail: { code: "auth_invalid_credentials", params: { method: "password" } },
      }),
    ).toEqual({
      code: "auth_invalid_credentials",
      params: { method: "password" },
    });
  });

  it("returns null when detail is a string", () => {
    expect(resolveApiError({ detail: "nope" })).toBeNull();
  });
});

describe("parseOAuthCallbackUrl", () => {
  it("reads hash tokens used by the web SPA", () => {
    expect(
      parseOAuthCallbackUrl("http://localhost:5173/#access_token=abc&token_type=bearer"),
    ).toEqual({ accessToken: "abc" });
  });

  it("reads query tokens used by native redirects", () => {
    expect(
      parseOAuthCallbackUrl("micro-saas://oauth?access_token=xyz&token_type=bearer"),
    ).toEqual({ accessToken: "xyz" });
  });

  it("reads auth_error_code from either location", () => {
    expect(parseOAuthCallbackUrl("http://localhost:5173/#auth_error_code=invalid_oauth_state")).toEqual({
      authErrorCode: "invalid_oauth_state",
    });
    expect(parseOAuthCallbackUrl("exp://127.0.0.1:8081/--/?auth_error_code=oauth_email_not_available")).toEqual(
      {
        authErrorCode: "oauth_email_not_available",
      },
    );
  });
});

describe("createApiClient", () => {
  it("posts JSON and maps API error bodies", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: { code: "auth_invalid_credentials" } }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = createApiClient({ getBaseUrl: () => "http://api.example.com/" });
    const result = await client.signInRequest("a@b.c", "secret");

    expect(fetchMock).toHaveBeenCalledWith("http://api.example.com/api/auth/signin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "a@b.c", password: "secret" }),
    });
    expect(result).toEqual({
      ok: false,
      errorCode: "auth_invalid_credentials",
      status: 401,
    });

    vi.unstubAllGlobals();
  });

  it("builds OAuth start URLs with an optional native redirect", () => {
    const client = createApiClient({ getBaseUrl: () => "http://127.0.0.1:8000" });
    expect(client.oauthStartUrl("google")).toBe("http://127.0.0.1:8000/api/auth/google");
    expect(client.oauthStartUrl("facebook", "micro-saas://oauth")).toBe(
      "http://127.0.0.1:8000/api/auth/facebook?redirect_uri=micro-saas%3A%2F%2Foauth",
    );
  });
});
