export type MeUser = { id: string; email: string; status: string };

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user: MeUser;
};

export type AuthConfig = {
  password: boolean;
  google: boolean;
  facebook: boolean;
};

export type AuthView = "signin" | "signup" | "recovery";

export type MessageResponse = { message: string };

export type Health = { status: string; database_configured: boolean };

export type Item = { id: number; name: string };

export type ItemsResponse = {
  items: Item[];
  detail?: string;
  detail_code?: string;
};

export type ApiErrorResolution = {
  code: string;
  params?: Record<string, string | number>;
};

export type ApiFailure = {
  ok: false;
  errorCode: string;
  errorParams?: Record<string, string | number>;
  status: number;
};

export type ApiSuccess<T> = { ok: true; data: T; status: number };

export type OAuthCallbackResult = {
  accessToken?: string;
  authErrorCode?: string;
};

export type OAuthProvider = "google" | "facebook";

export type ApiClientConfig = {
  getBaseUrl: () => string;
};
