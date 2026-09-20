import { createApiClient } from "@micro-saas/api-client";

export const api = createApiClient({
  getBaseUrl: () => process.env.EXPO_PUBLIC_API_BASE_URL ?? "",
});
