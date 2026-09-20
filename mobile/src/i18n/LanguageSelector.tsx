import { SUPPORTED_LOCALES, type SupportedLocale } from "@micro-saas/i18n";
import { Pressable, Text, View } from "react-native";
import { useTranslation } from "react-i18next";

import i18n from "../i18n";
import { useAppTheme } from "../theme";

const LOCALE_LABEL_KEYS: Record<SupportedLocale, string> = {
  en: "language.en",
  pl: "language.pl",
  uk: "language.uk",
  de: "language.de",
};

export function LanguageSelector() {
  const { t } = useTranslation();
  const theme = useAppTheme();
  const current = i18n.language.split("-")[0] as SupportedLocale;
  const value = SUPPORTED_LOCALES.includes(current) ? current : "en";

  return (
    <View accessibilityLabel={t("language.label")} style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
      {SUPPORTED_LOCALES.map((locale) => {
        const selected = locale === value;
        return (
          <Pressable
            key={locale}
            onPress={() => {
              void i18n.changeLanguage(locale);
            }}
            style={{
              borderWidth: 1,
              borderColor: selected ? theme.primary : theme.border,
              backgroundColor: selected ? theme.primary : theme.card,
              borderRadius: 8,
              paddingHorizontal: 8,
              paddingVertical: 6,
            }}
          >
            <Text style={{ color: selected ? "#FFFFFF" : theme.text, fontSize: 12 }}>
              {t(LOCALE_LABEL_KEYS[locale])}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}
