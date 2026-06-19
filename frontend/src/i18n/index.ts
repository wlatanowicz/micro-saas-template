import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import de from "./locales/de.json";
import en from "./locales/en.json";
import pl from "./locales/pl.json";
import uk from "./locales/uk.json";

export const SUPPORTED_LOCALES = ["en", "pl", "uk", "de"] as const;
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

function syncDocumentLang(lng: string) {
  document.documentElement.lang = lng;
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      pl: { translation: pl },
      uk: { translation: uk },
      de: { translation: de },
    },
    fallbackLng: "en",
    supportedLngs: [...SUPPORTED_LOCALES],
    detection: {
      order: ["localStorage", "navigator"],
      caches: ["localStorage"],
    },
    interpolation: {
      escapeValue: false,
    },
  });

syncDocumentLang(i18n.language);
i18n.on("languageChanged", syncDocumentLang);

export default i18n;
