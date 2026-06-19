import {
  Alert,
  Badge,
  Button,
  Container,
  Group,
  List,
  Paper,
  Text,
  Title,
} from "@mantine/core";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { AuthPanel } from "./auth/AuthPanel";
import { apiBase, fetchAuthConfig, loadMe, parseOAuthHash } from "./auth/api";
import type { AuthConfig, MeUser } from "./auth/types";
import { LanguageSelector } from "./i18n/LanguageSelector";
import { translateApiError } from "./i18n/translateApiError";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const ACCESS_TOKEN_KEY = "access_token";

type Health = { status: string; database_configured: boolean };

type ItemsResponse = {
  items: { id: number; name: string }[];
  detail?: string;
  detail_code?: string;
};

export function App() {
  const { t } = useTranslation();
  const [health, setHealth] = useState<Health | null>(null);
  const [items, setItems] = useState<ItemsResponse | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<MeUser | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);

  const getStoredToken = useCallback((): string | null => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }, []);

  const clearSession = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    setCurrentUser(null);
  }, []);

  const restoreSession = useCallback(
    async (token: string) => {
      const base = apiBase();
      if (!base) {
        return;
      }
      const r = await loadMe(token);
      if (!r.ok) {
        if (r.status === 401 || r.status === 403) {
          clearSession();
        }
        return;
      }
      setCurrentUser((await r.json()) as MeUser);
    },
    [clearSession],
  );

  useEffect(() => {
    if (!apiBaseUrl) {
      setConfigError(t("errors.apiBaseNotSet"));
      return;
    }

    const base = apiBase();

    void (async () => {
      try {
        const oauthResult = parseOAuthHash();
        if (oauthResult.authErrorCode) {
          setAuthError(translateApiError(t, oauthResult.authErrorCode));
        }

        const h = await fetch(`${base}/health`);
        if (!h.ok) {
          throw new Error(t("errors.healthCheckFailed", { status: h.status }));
        }
        setHealth((await h.json()) as Health);

        const config = await fetchAuthConfig();
        if (config) {
          setAuthConfig(config);
        }

        const i = await fetch(`${base}/api/items`);
        if (!i.ok) {
          throw new Error(t("errors.itemsRequestFailed", { status: i.status }));
        }
        setItems((await i.json()) as ItemsResponse);

        const tkn = oauthResult.accessToken ?? getStoredToken();
        if (tkn) {
          if (oauthResult.accessToken) {
            localStorage.setItem(ACCESS_TOKEN_KEY, tkn);
          }
          await restoreSession(tkn);
        }
      } catch (e) {
        setConfigError(e instanceof Error ? e.message : t("errors.requestFailed"));
      }
    })();
  }, [getStoredToken, restoreSession, t]);

  const methods: AuthConfig = authConfig ?? {
    password: true,
    google: false,
    facebook: false,
  };

  const itemsDetailMessage = items?.detail_code
    ? translateApiError(t, items.detail_code)
    : null;

  return (
    <Container size="sm" py="xl">
      <Group justify="space-between" align="flex-start" mb="md" wrap="wrap">
        <Title order={1}>{t("app.title")}</Title>
        <Group gap="xs" aria-live="polite">
          <LanguageSelector />
          {currentUser ? (
            <>
              <Text fw={600}>{currentUser.email}</Text>
              <Badge variant="light">{currentUser.status}</Badge>
              <Button
                variant="subtle"
                size="compact-sm"
                onClick={clearSession}
                disabled={false}
              >
                {t("app.signOut")}
              </Button>
            </>
          ) : (
            <Text c="dimmed" size="sm">
              {t("app.notSignedIn")}
            </Text>
          )}
        </Group>
      </Group>

      <Text c="dimmed" mb="lg">
        {t("app.subtitle")}
      </Text>

      {configError ? (
        <Alert color="red" title={t("errors.configuration")} mb="md">
          {configError}
        </Alert>
      ) : null}

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
        <Paper withBorder p="md" radius="md" mb="md">
          <Title order={3} size="h4" mb="sm">
            {t("api.title")}
          </Title>
          <Text>
            {t("api.status")} {health.status}
            <br />
            {t("api.databaseConfigured")} {String(health.database_configured)}
          </Text>
        </Paper>
      ) : null}

      {!configError && items ? (
        <Paper withBorder p="md" radius="md">
          <Title order={3} size="h4" mb="sm">
            {t("items.title")}
          </Title>
          {itemsDetailMessage ? <Text mb="sm">{itemsDetailMessage}</Text> : null}
          {items.items.length === 0 ? (
            <Text c="dimmed">{t("items.empty")}</Text>
          ) : (
            <List>
              {items.items.map((it) => (
                <List.Item key={it.id}>
                  #{it.id} — {it.name}
                </List.Item>
              ))}
            </List>
          )}
        </Paper>
      ) : null}
    </Container>
  );
}
