import type { AuthConfig, Health, ItemsResponse, MeUser } from "@micro-saas/api-client";
import { translateApiError } from "@micro-saas/i18n";
import { StatusBar } from "expo-status-bar";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "./api";
import { AuthPanel } from "./auth/AuthPanel";
import { LanguageSelector } from "./i18n/LanguageSelector";
import { clearAccessToken, getAccessToken } from "./session";
import { useAppTheme } from "./theme";
import { AppButton, Card, ErrorBanner } from "./ui";

export function HomeScreen() {
  const { t } = useTranslation();
  const theme = useAppTheme();
  const [health, setHealth] = useState<Health | null>(null);
  const [items, setItems] = useState<ItemsResponse | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<MeUser | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);

  const clearSession = useCallback(() => {
    void clearAccessToken();
    setCurrentUser(null);
  }, []);

  const restoreSession = useCallback(
    async (token: string) => {
      const r = await api.loadMe(token);
      if (!r.ok) {
        if (r.status === 401 || r.status === 403) {
          clearSession();
        }
        return;
      }
      setCurrentUser(r.data);
    },
    [clearSession],
  );

  useEffect(() => {
    if (!process.env.EXPO_PUBLIC_API_BASE_URL) {
      setConfigError(t("errors.apiBaseNotSet"));
      return;
    }

    void (async () => {
      try {
        const h = await api.fetchHealth();
        if (!h.ok) {
          throw new Error(t("errors.healthCheckFailed", { status: h.status }));
        }
        setHealth(h.data);

        const config = await api.fetchAuthConfig();
        if (config) {
          setAuthConfig(config);
        }

        const i = await api.fetchItems();
        if (!i.ok) {
          throw new Error(t("errors.itemsRequestFailed", { status: i.status }));
        }
        setItems(i.data);

        const tkn = await getAccessToken();
        if (tkn) {
          await restoreSession(tkn);
        }
      } catch (e) {
        setConfigError(e instanceof Error ? e.message : t("errors.requestFailed"));
      }
    })();
  }, [restoreSession, t]);

  const methods: AuthConfig = authConfig ?? {
    password: true,
    google: false,
    facebook: false,
  };

  const itemsDetailMessage = items?.detail_code
    ? translateApiError(t, items.detail_code)
    : null;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.bg }}>
      <StatusBar style="auto" />
      <ScrollView contentContainerStyle={{ padding: theme.pad, paddingBottom: 40 }}>
        <View
          style={{
            flexDirection: "row",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 12,
            marginBottom: 12,
            flexWrap: "wrap",
          }}
        >
          <Text style={{ color: theme.text, fontSize: 28, fontWeight: "700", flexShrink: 1 }}>
            {t("app.title")}
          </Text>
          <View style={{ gap: 8, alignItems: "flex-end" }}>
            <LanguageSelector />
            {currentUser ? (
              <View style={{ alignItems: "flex-end", gap: 6 }}>
                <Text style={{ color: theme.text, fontWeight: "600" }}>{currentUser.email}</Text>
                <View
                  style={{
                    borderRadius: 8,
                    backgroundColor: theme.card,
                    borderWidth: 1,
                    borderColor: theme.border,
                    paddingHorizontal: 8,
                    paddingVertical: 4,
                  }}
                >
                  <Text style={{ color: theme.text, fontSize: 12 }}>{currentUser.status}</Text>
                </View>
                <AppButton label={t("app.signOut")} variant="subtle" onPress={clearSession} />
              </View>
            ) : (
              <Text style={{ color: theme.dimmed, fontSize: 13 }}>{t("app.notSignedIn")}</Text>
            )}
          </View>
        </View>

        <Text style={{ color: theme.dimmed, marginBottom: 16 }}>{t("app.subtitle")}</Text>

        {configError ? <ErrorBanner message={configError} /> : null}

        {!configError && !currentUser && health ? (
          <AuthPanel
            authConfig={methods}
            initialError={authError}
            onSession={(user) => {
              setCurrentUser(user);
              setAuthError(null);
            }}
          />
        ) : null}

        {!configError && health ? (
          <Card>
            <Text style={{ color: theme.text, fontSize: 18, fontWeight: "700", marginBottom: 8 }}>
              {t("api.title")}
            </Text>
            <Text style={{ color: theme.text }}>
              {t("api.status")} {health.status}
              {"\n"}
              {t("api.databaseConfigured")} {String(health.database_configured)}
            </Text>
          </Card>
        ) : null}

        {!configError && items ? (
          <Card>
            <Text style={{ color: theme.text, fontSize: 18, fontWeight: "700", marginBottom: 8 }}>
              {t("items.title")}
            </Text>
            {itemsDetailMessage ? (
              <Text style={{ color: theme.text, marginBottom: 8 }}>{itemsDetailMessage}</Text>
            ) : null}
            {items.items.length === 0 ? (
              <Text style={{ color: theme.dimmed }}>{t("items.empty")}</Text>
            ) : (
              <View style={{ gap: 6 }}>
                {items.items.map((it) => (
                  <Text key={it.id} style={{ color: theme.text }}>
                    #{it.id} — {it.name}
                  </Text>
                ))}
              </View>
            )}
          </Card>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}
