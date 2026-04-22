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
        const h = await fetch(`${base}/health`);
        if (!h.ok) {
          throw new Error(`Health check failed: ${h.status}`);
        }
        setHealth((await h.json()) as Health);

        const i = await fetch(`${base}/api/items`);
        if (!i.ok) {
          throw new Error(`Items request failed: ${i.status}`);
        }
        setItems((await i.json()) as ItemsResponse);

        const t = getStoredToken();
        if (t) {
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

  return (
    <>
      <header className="app-header">
        <h1>Micro-SaaS template</h1>
        <div className="app-header__user" aria-live="polite">
          {currentUser ? (
            <>
              <strong>{currentUser.email}</strong>
              <span className="user-meta"> {currentUser.status}</span>
              <button
                type="button"
                className="btn-text"
                onClick={clearSession}
                disabled={authBusy}
              >
                Sign out
              </button>
            </>
          ) : (
            <span className="muted">Not signed in</span>
          )}
        </div>
      </header>
      <p>React frontend talking to the FastAPI Lambda API.</p>

      {configError ? (
        <div className="card error" role="alert">
          {configError}
        </div>
      ) : null}

      {!configError && !currentUser && health ? (
        <div className="card">
          <strong>Account</strong>
          {authError ? (
            <p className="error" role="alert">
              {authError}
            </p>
          ) : null}
          <form
            className="auth-form"
            onSubmit={(e) => {
              e.preventDefault();
            }}
          >
            <label>
              Email
              <input
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
            </label>
            <label>
              Password
              <input
                type="password"
                name="password"
                autoComplete="current-password"
                value={authPassword}
                onChange={(e) => {
                  setAuthPassword(e.target.value);
                }}
                required
                minLength={1}
                disabled={authBusy}
              />
            </label>
            <div className="form-actions">
              <button
                type="button"
                onClick={signIn}
                disabled={authBusy}
              >
                Sign in
              </button>
              <button
                type="button"
                onClick={signUp}
                disabled={authBusy}
              >
                Sign up
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {!configError && health ? (
        <div className="card">
          <strong>API</strong>
          <p>
            Status: {health.status}
            <br />
            Database configured: {String(health.database_configured)}
          </p>
        </div>
      ) : null}

      {!configError && items ? (
        <div className="card">
          <strong>Items</strong>
          {items.detail ? <p>{items.detail}</p> : null}
          {items.items.length === 0 ? (
            <p>No items yet.</p>
          ) : (
            <ul>
              {items.items.map((it) => (
                <li key={it.id}>
                  #{it.id} — {it.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </>
  );
}
