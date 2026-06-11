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
