import type { ApiErrorResolution } from "./types";

export function resolveApiError(body: { detail?: unknown }): ApiErrorResolution | null {
  const d = body.detail;
  if (typeof d === "object" && d !== null && "code" in d) {
    const code = String((d as { code: string }).code);
    const params = (d as { params?: Record<string, string | number> }).params;
    return params ? { code, params } : { code };
  }
  return null;
}
