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

import { AuthPanel } from "./auth/AuthPanel";
import { apiBase, fetchAuthConfig, loadMe, parseOAuthHash } from "./auth/api";
import type { AuthConfig, MeUser } from "./auth/types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const ACCESS_TOKEN_KEY = "access_token";

type Health = { status: string; database_configured: boolean };

type ItemsResponse =
  | { items: { id: number; name: string }[]; detail?: string }
  | null;

export function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [items, setItems] = useState<ItemsResponse>(null);
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
      setConfigError("VITE_API_BASE_URL is not set. Configure it for local dev or deploy.");
      return;
    }

    const base = apiBase();

    void (async () => {
      try {
        const oauthResult = parseOAuthHash();
        if (oauthResult.authError) {
          setAuthError(decodeURIComponent(oauthResult.authError));
        }

        const h = await fetch(`${base}/health`);
        if (!h.ok) {
          throw new Error(`Health check failed: ${h.status}`);
        }
        setHealth((await h.json()) as Health);

        const config = await fetchAuthConfig();
        if (config) {
          setAuthConfig(config);
        }

        const i = await fetch(`${base}/api/items`);
        if (!i.ok) {
          throw new Error(`Items request failed: ${i.status}`);
        }
        setItems((await i.json()) as ItemsResponse);

        const t = oauthResult.accessToken ?? getStoredToken();
        if (t) {
          if (oauthResult.accessToken) {
            localStorage.setItem(ACCESS_TOKEN_KEY, t);
          }
          await restoreSession(t);
        }
      } catch (e) {
        setConfigError(e instanceof Error ? e.message : "Request failed");
      }
    })();
  }, [getStoredToken, restoreSession]);

  const methods: AuthConfig = authConfig ?? {
    password: true,
    google: false,
    facebook: false,
  };

  return (
    <Container size="sm" py="xl">
      <Group justify="space-between" align="flex-start" mb="md" wrap="wrap">
        <Title order={1}>Micro-SaaS template</Title>
        <Group gap="xs" aria-live="polite">
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
                Sign out
              </Button>
            </>
          ) : (
            <Text c="dimmed" size="sm">
              Not signed in
            </Text>
          )}
        </Group>
      </Group>

      <Text c="dimmed" mb="lg">
        React frontend talking to the FastAPI Lambda API.
      </Text>

      {configError ? (
        <Alert color="red" title="Configuration error" mb="md">
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
            API
          </Title>
          <Text>
            Status: {health.status}
            <br />
            Database configured: {String(health.database_configured)}
          </Text>
        </Paper>
      ) : null}

      {!configError && items ? (
        <Paper withBorder p="md" radius="md">
          <Title order={3} size="h4" mb="sm">
            Items
          </Title>
          {items.detail ? <Text mb="sm">{items.detail}</Text> : null}
          {items.items.length === 0 ? (
            <Text c="dimmed">No items yet.</Text>
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
