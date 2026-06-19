import type { TFunction } from "i18next";

export type ApiErrorParams = Record<string, string | number>;

export function translateApiError(
  t: TFunction,
  code: string,
  params?: ApiErrorParams | null,
): string {
  const key = `errors.api.${code}`;
  const translated = t(key, params ?? {});
  if (translated !== key) {
    return translated;
  }
  return t("errors.requestFailed");
}
