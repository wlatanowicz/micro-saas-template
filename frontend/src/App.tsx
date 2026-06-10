import {
  Alert,
  Badge,
  Button,
  Container,
  Divider,
  Group,
  List,
  Paper,
  PasswordInput,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { useCallback, useEffect, useState } from "react";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const ACCESS_TOKEN_KEY = "access_token";

type Health = { status: string; database_configured: boolean };

type ItemsResponse =
  | { items: { id: number; name: string }[]; detail?: string }
  | null;

type MeUser = { id: string; email: string; status: string };

type TokenResponse = {
  access_token: string;
  token_type: string;
  user: MeUser;
};

type AuthConfig = {
  password: boolean;
  google: boolean;
  facebook: boolean;
};

function parseOAuthHash(): { accessToken?: string; authError?: string } {
  const hash = window.location.hash.replace(/^#/, "");
  if (!hash) {
    return {};
  }
  const params = new URLSearchParams(hash);
  const accessToken = params.get("access_token") ?? undefined;
  const authError = params.get("auth_error") ?? undefined;
  if (accessToken || authError) {
    const path = window.location.pathname + window.location.search;
    window.history.replaceState(null, "", path);
  }
  return { accessToken, authError };
}

function apiBase() {
  return (apiBaseUrl || "").replace(/\/$/, "");
}

function formatApiError(body: { detail?: unknown }): string {
  const d = body.detail;
  if (typeof d === "string") {
    return d;
  }
  if (Array.isArray(d)) {
    return d
      .map((err) => {
        if (err && typeof err === "object" && "msg" in err) {
          return String((err as { msg: string }).msg);
        }
        return String(err);
      })
      .join("; ");
  }
  return "Request failed";
}

export function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [items, setItems] = useState<ItemsResponse>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<MeUser | null>(null);
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);

  const getStoredToken = useCallback((): string | null => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }, []);

  const clearSession = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    setCurrentUser(null);
  }, []);

  const loadMe = useCallback(
    async (token: string) => {
      const base = apiBase();
      if (!base) {
        return;
      }
      const r = await fetch(`${base}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
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

        const configRes = await fetch(`${base}/api/auth/config`);
        if (configRes.ok) {
          setAuthConfig((await configRes.json()) as AuthConfig);
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
          await loadMe(t);
        }
      } catch (e) {
        setConfigError(e instanceof Error ? e.message : "Request failed");
      }
    })();
  }, [getStoredToken, loadMe]);

  const signUp = async () => {
    setAuthError(null);
    setAuthBusy(true);
    const base = apiBase();
    try {
      const r = await fetch(`${base}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      });
      const body = (await r.json().catch(() => ({}))) as
        | TokenResponse
        | { detail?: unknown };
      if (!r.ok) {
        setAuthError(formatApiError(body as { detail?: unknown }));
        return;
      }
      const t = (body as TokenResponse).access_token;
      const u = (body as TokenResponse).user;
      localStorage.setItem(ACCESS_TOKEN_KEY, t);
      setCurrentUser(u);
    } catch (e) {
      setAuthError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setAuthBusy(false);
    }
  };

  const signIn = async () => {
    setAuthError(null);
    setAuthBusy(true);
    const base = apiBase();
    try {
      const r = await fetch(`${base}/api/auth/signin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      });
      const body = (await r.json().catch(() => ({}))) as
        | TokenResponse
        | { detail?: unknown };
      if (!r.ok) {
        setAuthError(formatApiError(body as { detail?: unknown }));
        return;
      }
      const t = (body as TokenResponse).access_token;
      const u = (body as TokenResponse).user;
      localStorage.setItem(ACCESS_TOKEN_KEY, t);
      setCurrentUser(u);
    } catch (e) {
      setAuthError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setAuthBusy(false);
    }
  };

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
                disabled={authBusy}
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
        <Paper withBorder p="md" radius="md" mb="md">
          <Title order={3} size="h4" mb="sm">
            Account
          </Title>
          <Stack gap="md">
            {authError ? (
              <Alert color="red" role="alert">
                {authError}
              </Alert>
            ) : null}
            {methods.google || methods.facebook ? (
              <Stack gap="xs">
                {methods.google ? (
                  <Button
                    component="a"
                    href={`${apiBase()}/api/auth/google`}
                    variant="default"
                    fullWidth
                  >
                    Continue with Google
                  </Button>
                ) : null}
                {methods.facebook ? (
                  <Button
                    component="a"
                    href={`${apiBase()}/api/auth/facebook`}
                    variant="default"
                    fullWidth
                  >
                    Continue with Facebook
                  </Button>
                ) : null}
              </Stack>
            ) : null}
            {methods.password && (methods.google || methods.facebook) ? (
              <Divider label="or" labelPosition="center" />
            ) : null}
            {methods.password ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                }}
              >
                <Stack gap="sm">
                  <TextInput
                    label="Email"
                    type="email"
                    name="email"
                    autoComplete="email"
                    value={authEmail}
                    onChange={(e) => {
                      setAuthEmail(e.target.value);
                    }}
                    required
                    disabled={authBusy}
                  />
                  <PasswordInput
                    label="Password"
                    name="password"
                    autoComplete="current-password"
                    value={authPassword}
                    onChange={(e) => {
                      setAuthPassword(e.target.value);
                    }}
                    required
                    disabled={authBusy}
                  />
                  <Group gap="sm">
                    <Button type="button" onClick={signIn} loading={authBusy}>
                      Sign in
                    </Button>
                    <Button
                      type="button"
                      variant="default"
                      onClick={signUp}
                      loading={authBusy}
                    >
                      Sign up
                    </Button>
                  </Group>
                </Stack>
              </form>
            ) : null}
          </Stack>
        </Paper>
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
