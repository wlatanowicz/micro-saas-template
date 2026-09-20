import de from "./locales/de.json";
import en from "./locales/en.json";
import pl from "./locales/pl.json";
import uk from "./locales/uk.json";

export const SUPPORTED_LOCALES = ["en", "pl", "uk", "de"] as const;
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

export const localeResources = {
  en: { translation: en },
  pl: { translation: pl },
  uk: { translation: uk },
  de: { translation: de },
};
