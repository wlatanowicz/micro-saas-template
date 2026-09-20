import { localeResources, SUPPORTED_LOCALES, type SupportedLocale } from "@micro-saas/i18n";
import * as Localization from "expo-localization";
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import { getSavedLanguage, setSavedLanguage } from "./session";

export { SUPPORTED_LOCALES, type SupportedLocale };

function deviceLocale(): SupportedLocale {
  const code = Localization.getLocales()[0]?.languageCode ?? "en";
  return SUPPORTED_LOCALES.includes(code as SupportedLocale) ? (code as SupportedLocale) : "en";
}

void i18n.use(initReactI18next).init({
  resources: localeResources,
  lng: deviceLocale(),
  fallbackLng: "en",
  supportedLngs: [...SUPPORTED_LOCALES],
  interpolation: {
    escapeValue: false,
  },
});

void getSavedLanguage().then((saved) => {
  if (saved && SUPPORTED_LOCALES.includes(saved as SupportedLocale)) {
    void i18n.changeLanguage(saved);
  }
});

i18n.on("languageChanged", (lng) => {
  void setSavedLanguage(lng);
});

export default i18n;
