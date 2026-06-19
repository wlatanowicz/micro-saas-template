import { Select } from "@mantine/core";
import { useTranslation } from "react-i18next";

import i18n, { SUPPORTED_LOCALES, type SupportedLocale } from "./index";

const LOCALE_LABEL_KEYS: Record<SupportedLocale, string> = {
  en: "language.en",
  pl: "language.pl",
  uk: "language.uk",
  de: "language.de",
};

export function LanguageSelector() {
  const { t } = useTranslation();
  const current = i18n.language.split("-")[0] as SupportedLocale;
  const value = SUPPORTED_LOCALES.includes(current) ? current : "en";

  return (
    <Select
      aria-label={t("language.label")}
      data={SUPPORTED_LOCALES.map((locale) => ({
        value: locale,
        label: t(LOCALE_LABEL_KEYS[locale]),
      }))}
      value={value}
      onChange={(next) => {
        if (next) {
          void i18n.changeLanguage(next);
        }
      }}
      size="xs"
      w={140}
    />
  );
}
