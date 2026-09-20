import { localeResources, SUPPORTED_LOCALES } from "@micro-saas/i18n";
import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

export { SUPPORTED_LOCALES, type SupportedLocale } from "@micro-saas/i18n";

function syncDocumentLang(lng: string) {
  document.documentElement.lang = lng;
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: localeResources,
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
