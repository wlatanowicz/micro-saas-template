import * as SecureStore from "expo-secure-store";

const ACCESS_TOKEN_KEY = "access_token";
const LANGUAGE_KEY = "app_language";

export async function getAccessToken(): Promise<string | null> {
  return SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
}

export async function setAccessToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, token);
}

export async function clearAccessToken(): Promise<void> {
  await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
}

export async function getSavedLanguage(): Promise<string | null> {
  return SecureStore.getItemAsync(LANGUAGE_KEY);
}

export async function setSavedLanguage(locale: string): Promise<void> {
  await SecureStore.setItemAsync(LANGUAGE_KEY, locale);
}
