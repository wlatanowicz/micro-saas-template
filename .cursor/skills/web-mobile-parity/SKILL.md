---
name: web-mobile-parity
description: >-
  Keep the Vite web SPA and Expo mobile app in feature parity. Use when adding
  or changing user-facing features, auth flows, API contracts, i18n keys, or
  client fetch helpers in this template.
---

# Web / mobile parity

This template ships two clients that must stay consistent: `frontend/` (Vite + Mantine) and `mobile/` (Expo + React Native). Shared logic lives in npm workspaces.

## When this applies

- New or changed screens, auth, session handling, health/items, or other user-facing behavior
- API request/response shapes, error codes, or auth (including OAuth)
- i18n keys or locale JSON
- Fetch helpers, token handling contracts (not storage)

## Required order

1. Update `@micro-saas/api-client` and/or `@micro-saas/i18n` first.
2. Wire **both** UIs to the shared change (`frontend/` and `mobile/`).
3. If the backend contract changes, update FastAPI routes/tests in the same change set.

Do **not** duplicate types, locale files, or `fetch` wrappers inside an app. Import the workspace packages.

## What stays app-specific

- UI kits: Mantine on web, React Native primitives on mobile
- Token storage: `localStorage` vs `expo-secure-store`
- API base URL: `VITE_API_BASE_URL` vs `EXPO_PUBLIC_API_BASE_URL`
- i18n init: browser language detector vs `expo-localization`
- OAuth start: `<a href>` vs `expo-auth-session` / `expo-web-browser` (both must call `oauthStartUrl` and parse tokens with `parseOAuthCallbackUrl`)

Screens, copy keys, enabled auth methods, and API usage must match even when widgets differ.

## OAuth

Web keeps hash redirects to `AUTH_FRONTEND_URL`. Native clients pass `redirect_uri` (schemes in `AUTH_OAUTH_NATIVE_SCHEMES`, default `micro-saas,exp`) and receive query params. Do not add a second OAuth protocol.
